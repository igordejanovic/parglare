# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import pytest
from parglare import Parser, Grammar
from parglare.exceptions import GrammarError, ParseError, RRConflicts


def test_repeatable_zero_or_more():
    """
    Tests zero or more repeatable operator.
    """

    grammar = """
    S: "2" b* "3";

    terminals
    b: "1";
    """

    g = Grammar.from_string(grammar)
    assert g.get_nonterminal('b_0')
    assert g.get_nonterminal('b_1')

    p = Parser(g)

    input_str = '2 1 1 1 3'
    result = p.parse(input_str)
    assert result == ["2", ["1", "1", "1"], "3"]

    input_str = '2 3'
    result = p.parse(input_str)
    assert result == ["2", [], "3"]


def test_repeatable_zero_or_more_with_separator():
    """
    Tests zero or more repeatable operator with separator.
    """

    grammar = """
    S: "2" b*[comma] "3";

    terminals
    b: "1";
    comma: ",";
    """

    g = Grammar.from_string(grammar)
    assert g.get_nonterminal('b_0_comma')

    p = Parser(g)

    input_str = '2 1, 1 , 1 3'
    result = p.parse(input_str)
    assert result == ["2", ["1", "1", "1"], "3"]

    input_str = '2 3'
    result = p.parse(input_str)
    assert result == ["2", [], "3"]


def test_repeatable_one_or_more():
    """
    Tests one or more repeatable operator.
    """

    grammar = """
    S: "2" b+ "3";

    terminals
    b: "1";
    """

    g = Grammar.from_string(grammar)
    assert g.get_nonterminal('b_1')

    p = Parser(g)

    input_str = '2 1 1 1 3'
    result = p.parse(input_str)
    assert result == ["2", ["1", "1", "1"], "3"]

    input_str = '2 3'
    with pytest.raises(ParseError) as e:
        result = p.parse(input_str)
    assert 'Expected: b' in str(e)


def test_repeatable_one_or_more_with_separator():
    """
    Tests one or more repeatable operator with separator.
    """

    grammar = """
    S: "2" b+[comma] "3";

    terminals
    b: "1";
    comma: ",";
    """

    g = Grammar.from_string(grammar)
    assert g.get_nonterminal('b_1_comma')

    p = Parser(g)

    input_str = '2 1, 1 , 1 3'
    result = p.parse(input_str)
    assert result == ["2", ["1", "1", "1"], "3"]

    input_str = '2 3'
    with pytest.raises(ParseError) as e:
        p.parse(input_str)
    assert 'Expected: b' in str(e)


def test_optional():
    """
    Tests optional operator.
    """

    grammar = """
    S: "2" b? "3"? EOF;

    terminals
    b: "1";
    """

    g = Grammar.from_string(grammar)
    assert g.get_nonterminal('b_opt')

    p = Parser(g)

    input_str = '2 1 3'
    result = p.parse(input_str)
    assert result == ["2", "1", "3", None]

    input_str = '2 3'
    result = p.parse(input_str)
    assert result == ["2", None, "3", None]

    input_str = '2 1'
    result = p.parse(input_str)
    assert result == ["2", "1", None, None]

    input_str = ' 1 3'
    with pytest.raises(ParseError) as e:
        p.parse(input_str)
    assert 'Expected: 2' in str(e)


def test_optional_no_modifiers():
    """
    Tests that optional operator doesn't allow modifiers.
    """

    grammar = """
    S: "2" b?[comma] "3"? EOF;

    terminals
    b: "1";
    comma: ",";
    """

    with pytest.raises(GrammarError) as e:
        Grammar.from_string(grammar)

    assert "Repetition modifier not allowed" in str(e)


def test_multiple_repetition_operators():
    """
    Test using of multiple repetition operators.
    """
    grammar = """
    S: "2" b*[comma] c+ "3"? EOF;

    terminals
    b: "b";
    c: "c";
    comma: ",";
    """

    g = Grammar.from_string(grammar)
    assert g.get_nonterminal('b_0_comma')
    assert g.get_nonterminal('c_1')

    p = Parser(g)

    input_str = '2 b, b  c 3'
    result = p.parse(input_str)
    assert result == ["2", ["b", "b"], ["c"], "3", None]


def test_repetition_operator_many_times_same():
    """
    Test using the same repetition operator multiple times.
    """

    grammar = """
    S: "2" b*[comma] "3"? b*[comma] EOF;

    terminals
    b: "b";
    comma: ",";
    """

    g = Grammar.from_string(grammar)
    assert g.get_nonterminal('b_0_comma')

    p = Parser(g)

    input_str = '2 b  3 b, b'
    result = p.parse(input_str)
    assert result == ["2", ["b"], "3", ["b", "b"], None]


def test_repeatable_one_zero_rr_conflicts():
    """
    Check that translations of B+ and B* don't produce R/R conflict.
    """
    grammar = """
    S: A B+ C;
    S: A B* D;

    terminals
    A:; B:; C:; D:;
    """
    g = Grammar.from_string(grammar, _no_check_recognizers=True)

    # Check if parser construction raises exception
    try:
        Parser(g)
    except RRConflicts:
        pytest.fail("R/R conflicts not expected here.")
