from parglare import GLRParser, Grammar


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
