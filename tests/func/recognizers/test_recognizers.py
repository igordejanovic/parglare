# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import pytest  # noqa
from parglare import Grammar, Parser, ParseError, ParserInitError, \
    GrammarError, DisambiguationError
from parglare.actions import pass_single, pass_nochange, collect


def test_parse_list_of_integers():

    grammar = """
    Numbers: all_less_than_five EOF;
    all_less_than_five: all_less_than_five int_less_than_five
                      | int_less_than_five;

    terminals
    int_less_than_five:;
    """

    def int_less_than_five(input, pos):
        if input[pos] < 5:
            return [input[pos]]

    recognizers = {
        'int_less_than_five': int_less_than_five
    }
    g = Grammar.from_string(grammar, recognizers=recognizers, debug=True)

    actions = {
        'Numbers': pass_single,
        'all_less_than_five': collect,
        'int_less_than_five': pass_single
    }

    # Test that `ws` must be set to `None` for non-textual content
    parser = Parser(g, actions=actions)

    ints = [3, 4, 1, 4]
    with pytest.raises(
            ParserInitError,
            match=r'For parsing non-textual content please '
            'set `ws` to `None`'):
        parser.parse(ints)

    parser = Parser(g, actions=actions, ws=None)
    ints = [3, 4, 1, 4]
    p = parser.parse(ints)
    assert p == ints

    # Test that error is correctly reported.
    with pytest.raises(ParseError) as e:
        parser.parse([4, 2, 1, 6, 3])
    assert '1:3:"[4, 2, 1]*[6, 3]"' in str(e)
    assert 'int_less_than_five' in str(e)


def test_parse_list_of_integers_lexical_disambiguation():

    def int_less_than_five(input, pos):
        if input[pos] < 5:
            return [input[pos]]

    def ascending(input, pos):
        "Match sublist of ascending elements. Matches at least one."
        last = pos + 1
        while last < len(input) and input[last] > input[last-1]:
            last += 1
        if last > pos:
            return input[pos:last]

    def ascending_nosingle(input, pos):
        "Match sublist of ascending elements. Matches at least two."
        last = pos + 1
        while last < len(input) and input[last] > input[last-1]:
            last += 1
        if last - pos >= 2:
            return input[pos:last]

    grammar = """
    Numbers: all_less_than_five ascending all_less_than_five EOF;
    all_less_than_five: all_less_than_five int_less_than_five
                      | int_less_than_five;

    terminals
    int_less_than_five:;
    ascending:;
    """

    recognizers = {
        'int_less_than_five': int_less_than_five,
        'ascending': ascending
    }
    g = Grammar.from_string(grammar, recognizers=recognizers)

    actions = {
        'Numbers': lambda _, nodes: [nodes[0], nodes[1], nodes[2]],
        'all_less_than_five': collect,
        'int_less_than_five': pass_single,   # Unpack element for collect
        'ascending': pass_nochange
    }
    parser = Parser(g, actions=actions, ws=None, debug=True)

    ints = [3, 4, 1, 4, 7, 8, 9, 3]

    # This must fail as ascending and int_less_than_five recognizers both
    # might match just a single int and after parser has saw 3 it will try
    # to disambiguate and fail as the following 4 is recognized by both
    # recognizers.
    with pytest.raises(DisambiguationError):
        p = parser.parse(ints)

    # Now we change the recognizer for ascending to match at least two
    # consecutive ascending numbers.
    recognizers['ascending'] = ascending_nosingle
    g = Grammar.from_string(grammar, recognizers=recognizers)
    parser = Parser(g, actions=actions, ws=None, debug=True)

    # Parsing now must pass
    p = parser.parse(ints)

    assert p == [[3, 4], [1, 4, 7, 8, 9], [3]]


def test_terminals_with_emtpy_bodies_require_recognizers():
    """
    If there are terminals with empty bodies in the grammar then recognizers
    must be given and there must be a recognizer for each terminal missing
    in-grammar recognizer.
    """

    grammar = """
    S: A | B | C;

    terminals
    A: {15};
    B: ;
    C: "c";
    """

    with pytest.raises(GrammarError):
        g = Grammar.from_string(grammar)

    recognizers = {
        'B': lambda input, pos: None,
    }

    with pytest.raises(GrammarError):
        g = Grammar.from_string(grammar, recognizers=recognizers)

    recognizers['A'] = lambda input, pos: None

    g = Grammar.from_string(grammar, recognizers=recognizers)
    assert g

    # Test that setting _no_check_recognizers will prevent grammar
    # error. This is used in pglr command.
    Grammar.from_string(grammar, _no_check_recognizers=True)
