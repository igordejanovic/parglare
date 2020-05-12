# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import pytest  # noqa
from parglare import Grammar, Parser, ParseError, ParserInitError, \
    GrammarError, DisambiguationError, Recognizers


def test_parse_list_of_integers():

    grammar = """
    Numbers: all_less_than_five;
    @collect
    all_less_than_five: all_less_than_five int_less_than_five
                      | int_less_than_five;

    terminals
    @pass_single
    int_less_than_five:;
    """

    class MyRecognizers(Recognizers):
        def int_less_than_five(self, input, pos):
            if input[pos] < 5:
                return [input[pos]]

    g = Grammar.from_string(grammar, recognizers=MyRecognizers())

    # Test that `ws` must be set to `None` for non-textual content
    parser = Parser(g)

    ints = [3, 4, 1, 4]
    with pytest.raises(
            ParserInitError,
            match=r'For parsing non-textual content please '
            'set `ws` to `None`'):
        parser.parse(ints)

    parser = Parser(g, ws=None)
    ints = [3, 4, 1, 4]
    p = parser.parse(ints)
    assert p == ints

    # Test that error is correctly reported.
    with pytest.raises(ParseError) as e:
        parser.parse([4, 2, 1, 6, 3])
    assert '1:3:"[4, 2, 1] **> [6, 3]"' in str(e.value)
    assert 'int_less_than_five' in str(e.value)


def test_parse_list_of_integers_lexical_disambiguation():

    class MyRecognizers(Recognizers):
        def int_less_than_five(self, input, pos):
            if input[pos] < 5:
                return [input[pos]]

        def ascending(self, input, pos):
            "Match sublist of ascending elements. Matches at least one."
            last = pos + 1
            while last < len(input) and input[last] > input[last-1]:
                last += 1
            if last > pos:
                return input[pos:last]

        def ascending_nosingle(self, input, pos):
            "Match sublist of ascending elements. Matches at least two."
            last = pos + 1
            while last < len(input) and input[last] > input[last-1]:
                last += 1
            if last - pos >= 2:
                return input[pos:last]

    grammar = """
    Numbers: all_less_than_five ascending all_less_than_five;
    @collect
    all_less_than_five: all_less_than_five int_less_than_five
                      | int_less_than_five;

    terminals
    @pass_single int_less_than_five:;
    ascending:;
    """

    g = Grammar.from_string(grammar, recognizers=MyRecognizers())

    parser = Parser(g, ws=None)

    ints = [3, 4, 1, 4, 7, 8, 9, 3]

    # This must fail as ascending and int_less_than_five recognizers both
    # might match just a single int and after parser has saw 3 it will try
    # to disambiguate and fail as the following 4 is recognized by both
    # recognizers.
    with pytest.raises(DisambiguationError):
        p = parser.parse(ints)

    # Now we change the recognizer for ascending to match at least two
    # consecutive ascending numbers.
    class MyRecognizers2(MyRecognizers):
        def ascending(self, input, pos):
            "Match sublist of ascending elements. Matches at least two."
            last = pos + 1
            while last < len(input) and input[last] > input[last-1]:
                last += 1
            if last - pos >= 2:
                return input[pos:last]

    g = Grammar.from_string(grammar, recognizers=MyRecognizers2())
    parser = Parser(g, ws=None)

    # Parsing now must pass
    p = parser.parse(ints)

    assert p == [[3, 4], [1, 4, 7, 8, 9], [3]]


def test_terminals_with_empty_bodies_require_recognizers():
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

    class MyRecognizers(Recognizers):
        def B(self, input, pos):
            return None

    with pytest.raises(GrammarError):
        g = Grammar.from_string(grammar, recognizers=MyRecognizers())

    class MyRecognizers2(MyRecognizers):
        def A(self, input, pos):
            return None

    g = Grammar.from_string(grammar, recognizers=MyRecognizers2())
    assert g

    # Test that setting _no_check_recognizers will prevent grammar
    # error. This is used in pglr command.
    Grammar.from_string(grammar, _no_check_recognizers=True)
