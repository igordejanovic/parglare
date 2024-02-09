import pytest

from parglare import GLRParser, Grammar, ParseError


def test_greedy_zero_or_more():
    """
    Test greedy variant of zero or more.
    """
    grammar = r"""
    S: A* A*;
    terminals
    A: "a";
    """

    g = Grammar.from_string(grammar)
    p = GLRParser(g)
    forest = p.parse("a a a a a a")
    assert len(forest) == 7

    # But greedy variant has only one solution where first A*! collects all tokens.
    grammar = r"""
    S: A*! A*;
    terminals
    A: "a";
    """

    g = Grammar.from_string(grammar)
    p = GLRParser(g)
    forest = p.parse("a a a a a a")
    assert len(forest) == 1


def test_greedy_zero_or_more_complex():
    """
    Test greedy variant of zero or more for complex subexpression.
    """
    grammar = r"""
    S: ("a" | "b" "c")* "a"*;
    """

    g = Grammar.from_string(grammar)
    p = GLRParser(g)
    forest = p.parse("a a a b c a b c a a a")
    assert len(forest) == 4

    grammar = r"""
    S: ("a" | "b" "c")*! "a"*;
    """

    g = Grammar.from_string(grammar)
    p = GLRParser(g)
    forest = p.parse("a a a b c a b c a a a")
    assert len(forest) == 1


def test_greedy_one_or_more():
    """
    Test greedy variant of one or more.
    """
    grammar = r"""
    S: A+ A*;
    terminals
    A: "a";
    """

    g = Grammar.from_string(grammar)
    p = GLRParser(g)
    forest = p.parse("a a a a a a")
    assert len(forest) == 6

    # But greedy variant has only one solution where first A+! collects all tokens.
    grammar = r"""
    S: A+! A*;
    terminals
    A: "a";
    """

    g = Grammar.from_string(grammar)
    p = GLRParser(g)
    forest = p.parse("a a a a a a")
    assert len(forest) == 1


def test_greedy_optional():
    """
    Test greedy variant of one or more.
    """
    grammar = r"""
    S: A? A+;
    terminals
    A: "a";
    """

    g = Grammar.from_string(grammar)
    p = GLRParser(g)
    forest = p.parse("a a a a a a")
    assert len(forest) == 2

    # But greedy variant has only one solution where first A?! is non-empty if possible
    grammar = r"""
    S: A?! A*;
    terminals
    A: "a";
    """

    g = Grammar.from_string(grammar)
    p = GLRParser(g)
    forest = p.parse("a a a a a a")
    assert len(forest) == 1


def test_greedy_interleaved_zero():
    """
    Multiple zero or more with optional in between.
    """
    grammar = r"""
    S: A* B? A*;
    terminals
    A: "a";
    B: "b";
    """

    g = Grammar.from_string(grammar)
    p = GLRParser(g)
    assert len(p.table.sr_conflicts) == 2
    assert len(p.table.rr_conflicts) == 0
    forest = p.parse("a a a a")
    assert len(forest) == 5
    forest = p.parse("a a b a a")
    assert len(forest) == 1
    forest = p.parse("a a a b")
    assert len(forest) == 1

    grammar = r"""
    S: A*! B? A*;
    terminals
    A: "a";
    B: "b";
    """

    g = Grammar.from_string(grammar)
    p = GLRParser(g)
    assert len(p.table.sr_conflicts) == 0
    assert len(p.table.rr_conflicts) == 0
    forest = p.parse("a a a a")
    assert len(forest) == 1
    forest = p.parse("a a b a a")
    assert len(forest) == 1


def test_greedy_interleaved_one():
    """
    Multiple one or more with optional in between.
    """
    grammar = r"""
    S: A+ B? A+;
    terminals
    A: "a";
    B: "b";
    """

    g = Grammar.from_string(grammar)
    p = GLRParser(g)
    assert len(p.table.sr_conflicts) == 1
    assert len(p.table.rr_conflicts) == 0
    forest = p.parse("a a a a")
    assert len(forest) == 3
    forest = p.parse("a a b a a")
    assert len(forest) == 1
    forest = p.parse("a a a b a")
    assert len(forest) == 1

    grammar = r"""
    S: A+! B? A+;
    terminals
    A: "a";
    B: "b";
    """

    g = Grammar.from_string(grammar)
    p = GLRParser(g)
    assert len(p.table.sr_conflicts) == 0
    assert len(p.table.rr_conflicts) == 0

    # This can't be parsed as A+! will collect all `a` and there will be none
    # left for the A+ at the end.
    with pytest.raises(ParseError):
        forest = p.parse("a a a a")

    forest = p.parse("a a b a a")
    assert len(forest) == 1
