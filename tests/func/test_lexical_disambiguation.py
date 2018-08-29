# -*- coding: utf-8 -*-
"""Test lexical disambiguation strategy.

Longest-match strategy is first used. If more tokens has the same length
priority is given to the more specific match (i.e. str match over regex).
If ambiguity is still unresolved priority is checked as the last resort.
At the end disambiguation error is reported.

"""
from __future__ import unicode_literals
import pytest  # noqa
import difflib
import re
from parglare import Parser, Grammar, Token, ParseError, DisambiguationError


called = [False, False, False]


def act_called(which_called):
    def _called(_, __):
        called[which_called] = True
    return _called


actions = {
    "First": act_called(0),
    "Second": act_called(1),
    "Third": act_called(2),
}


@pytest.fixture()
def cf():
    global called
    called = [False, False, False]


def test_priority(cf):

    grammar = """
    S: M EOF;
    M: First | Second  | Third "5";

    terminals
    First: /\d+\.75/;
    Second: '14.75';
    Third: /\d+\.\d/ {15};
    """

    g = Grammar.from_string(grammar)
    parser = Parser(g, actions=actions, debug=False)

    # Priority is used first
    parser.parse('14.75')
    assert called == [False, False, True]


def test_priority_lower(cf):
    """
    Test that lower priority terminals have lower precendence.
    """

    grammar = """
    S: M EOF;
    M: First | Second  | Third;

    terminals
    First: /\d+\.75/ {7};
    Second: /\d+\.\d+/;
    Third: /foo/;
    """

    g = Grammar.from_string(grammar)
    parser = Parser(g, actions=actions, debug=False)

    # Second should match as it has higher priority over First
    parser.parse('14.75')
    assert called == [False, True, False]


def test_most_specific(cf):

    grammar = """
    S: First | Second | Third;

    terminals
    First: /\d+\.\d+/;
    Second: '14';
    Third: /\d+/;
    """

    g = Grammar.from_string(grammar)
    parser = Parser(g, actions=actions, debug=True)

    # String match in rule Second is more specific than Third regexp rule.
    parser.parse('14')
    assert called == [False, True, False]


def test_most_specific_longest_match(cf):

    grammar = """
    S: First | Second | Third;

    terminals
    First: '147';
    Second: '14';
    Third: /\d+/;
    """

    g = Grammar.from_string(grammar)
    parser = Parser(g, actions=actions, debug=True)

    # All three rules could match. First is tried first because it is
    # more specific (str match) and longest. It succeeds so other two
    # are not tried at all.
    parser.parse('147')
    assert called == [True, False, False]


def test_longest_match(cf):

    grammar = """
    S: First | Second | Third;

    terminals
    First: /\d+\.\d+/;
    Second: '13';
    Third: /\d+/;
    """

    g = Grammar.from_string(grammar)
    parser = Parser(g, actions=actions)

    # If all matches are regexes of the same priority use longest match
    # disambiguation.
    parser.parse('14.17')
    assert called == [True, False, False]


def test_failed_disambiguation(cf):

    grammar = """
    S: First | Second | Third;

    terminals
    First: /\d+\.\d+/ {15};
    Second: '14.7';
    Third: /\d+\.75/ {15};
    """

    g = Grammar.from_string(grammar)
    parser = Parser(g, actions=actions, debug=True)

    # All rules will match but First and Third have higher priority.
    # Both are regexes so longest match will be used.
    # Both have the same length.

    with pytest.raises(DisambiguationError) as e:
        parser.parse('14.75')

    assert 'disambiguate' in str(e)
    assert 'First' in str(e)
    assert 'Second' not in str(e)
    assert 'Third' in str(e)


def test_longest_match_prefer(cf):

    grammar = """
    S: First | Second | Third;

    terminals
    First: /\d+\.\d+/ {15};
    Second: '14.7';
    Third: /\d+\.75/ {15, prefer};
    """

    g = Grammar.from_string(grammar)
    parser = Parser(g, actions=actions)

    # All rules will match but First and Third have higher priority.
    # Both are regexes so longest match will be used.
    # Both have the same length but the third rule is preferred.

    parser.parse('14.75')
    assert called == [False, False, True]


def test_nofinish(cf):
    """
    Test that `nofinish` terminal filter will disable `finish` short-circuit
    optimization.
    """
    global called

    # In rare circumstances `finish` scanning optimization may lead to a
    # problem. This grammar demonstrates the problem.
    grammar = """
    S: First | Second | Third;

    terminals
    First: /\d+\.\d+/;
    Second: '*';
    Third: /[A-Za-z0-9\*\-]+/;
    """

    # In the previous grammar trying to parse input "*ThirdShouldMatchThis"
    # will parse only "*" at the beginning as Second will be short-circed by
    # implicit "prefer string match" rule and `finish` flag on Second terminal
    # will be set.
    g = Grammar.from_string(grammar)
    parser = Parser(g, actions=actions)
    parser.parse('*ThirdShouldMatchThis')
    assert called == [False, True, False]

    # In this case we would actually like for Third to match as it is a longer
    # match. To do this we should set `nofinish` flag on Second terminal which
    # will make parglare doesn't use short-circuit and try other possibilities
    # also.
    grammar = """
    S: First | Second | Third;

    terminals
    First: /\d+\.\d+/;
    Second: '*' {nofinish};
    Third: /[A-Za-z0-9\*\-]+/;
    """
    called = [False, False, False]
    g = Grammar.from_string(grammar)
    parser = Parser(g, actions=actions)
    parser.parse('*ThirdShouldMatchThis')
    assert called == [False, False, True]


def test_dynamic_lexical_disambiguation():
    """
    Dynamic disambiguation enables us to choose right token from the
    tokens posible to appear at given place in the input.
    """
    grammar = """
    S: Element+ EOF;
    Element: Bar | Baz | Number;

    terminals
    Bar: /Bar. \d+/;
    Baz: /Baz. \d+/;
    Number: /\d+/;
    """

    g = Grammar.from_string(grammar)
    grammar = [g]

    def custom_token_recognition(context, get_tokens):
        """
        Custom token recognition should return a single token that is
        recognized at the given place in the input string.
        """
        # Call default token recognition.
        tokens = get_tokens()

        if tokens:
            # If default recognition succeeds use the result.
            return tokens
        else:
            # If no tokens are found do the fuzzy match.
            matchers = [
                lambda x: difflib.SequenceMatcher(None, 'bar.', x.lower()),
                lambda x: difflib.SequenceMatcher(None, 'baz.', x.lower())
            ]
            symbols = [
                grammar[0].get_terminal('Bar'),
                grammar[0].get_terminal('Baz'),
            ]
            # Try to do fuzzy match at the position
            elem = context.input_str[context.position:context.position+4]
            elem_num = context.input_str[context.position:]
            number_matcher = re.compile(r'[^\d]*(\d+)')
            number_match = number_matcher.match(elem_num)
            ratios = []
            for matcher in matchers:
                ratios.append(matcher(elem).ratio())

            max_ratio_index = ratios.index(max(ratios))
            if ratios[max_ratio_index] > 0.7 and number_match.group(1):
                return [Token(symbols[max_ratio_index], number_match.group())]

    parser = Parser(
        g, custom_token_recognition=custom_token_recognition)

    # Bar and Baz will be recognized by a fuzzy match
    result = parser.parse('bar. 56 Baz 12')
    assert result == [['bar. 56', 'Baz 12'], None]

    result = parser.parse('Buz. 34 bar 56')
    assert result == [['Buz. 34', 'bar 56'], None]

    result = parser.parse('Ba. 34 baz 56')
    assert result == [['Ba. 34', 'baz 56'], None]

    # But if Bar/Baz are too different from the correct pattern
    # we get ParseError. In this case `bza` score is bellow 0.7
    # for both Bar and Baz symbols.
    with pytest.raises(ParseError):
        parser.parse('Bar. 34 bza 56')
