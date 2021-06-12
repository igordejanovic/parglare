# -*- coding: utf-8 -*-
"""
Test non-deterministic parsing.
"""
import sys
import pytest  # noqa
from parglare import Parser, GLRParser, Grammar, SLR, LALR
from parglare.exceptions import ParseError, SRConflicts, RRConflicts, LoopError


def test_lr_1_grammar():
    """From the Knuth's 1965 paper: On the Translation of Languages from Left to
    Right

    """
    grammar = """
    S: 'a' A 'd' | 'b' A 'd';
    A: 'c' A | 'c';
    """

    g = Grammar.from_string(grammar)
    parser = Parser(g)

    parser.parse("acccccccccd")
    parser.parse("bcccccccccd")

    parser = GLRParser(g)
    assert len(parser.parse("accccccccd")) == 1
    assert len(parser.parse("bccccccccd")) == 1


def test_slr_conflict():
    """
    Unambiguous grammar which is not SLR(1).
    From the Dragon Book.
    This grammar has a S/R conflict if SLR tables are used.
    """

    grammar = """
    S: L '=' R | R;
    L: '*' R | 'id';
    R: L;
    """

    grammar = Grammar.from_string(grammar)
    with pytest.raises(SRConflicts):
        Parser(grammar, tables=SLR, prefer_shifts=False)

    Parser(grammar, tables=LALR, prefer_shifts=False)


def test_lalr_reduce_reduce_conflict():
    """
    Naive merging of states can lead to R/R conflict as shown in this grammar
    from the Dragon Book.
    But the extended LALR state compression algorithm used in parglare doesn't
    exibit this problem.
    """

    grammar = """
    S: 'a' A 'd' | 'b' B 'd' | 'a' B 'e' | 'b' A 'e';
    A: C;
    B: C;
    C: 'c';
    """
    grammar = Grammar.from_string(grammar)
    Parser(grammar)


def test_nondeterministic_LR_raise_error():
    """Language of even length palindromes.

    This is a non-deterministic grammar and the language is non-ambiguous.

    If the string is a even length palindrome parser should reduce EMPTY at he
    middle of the string and start to reduce by A and B.

    LR parsing is deterministic so this grammar can't parse the input as the
    EMPTY reduction will be tried only after consuming all the input by
    implicit disambiguation strategy of favouring shifts over empty reductions.

    OTOH, GLR parser can handle this by forking parser at each step and trying
    both empty reductions and shifts. Only the parser that has reduced empty at
    the middle of the input will succeed.

    """
    grammar = """
    S: A | B | EMPTY;
    A: '1' S '1';
    B: '0' S '0';
    """

    g = Grammar.from_string(grammar)
    with pytest.raises(ParseError):
        p = Parser(g)
        p.parse('0101000110001010')

    p = GLRParser(g)
    results = p.parse('0101000110001010')

    assert len(results) == 1


def test_cyclic_grammar_1():
    """
    Grammar G1 from the paper: "GLR Parsing for e-Grammers" by Rahman Nozohoor-Farshi
    """
    grammar = """
    S: A;
    A: S;
    A: 'x';
    """
    g = Grammar.from_string(grammar)
    with pytest.raises(SRConflicts):
        Parser(g, prefer_shifts=False)

    p = GLRParser(g)
    results = p.parse('x')

    # This grammar builds infinite/looping tree
    # x -> A -> S -> A -> S...
    with pytest.raises(LoopError):
        len(results)


@pytest.mark.skipif(sys.version_info < (3, 6),
                    reason="list comparison doesn't work "
                    "correctly in pytest 4.1")
def test_cyclic_grammar_2():
    """
    Grammar G2 from the paper: "GLR Parsing for e-Grammers" by Rahman Nozohoor-Farshi
    Classic Tomita's GLR algorithm doesn't terminate with this grammar.

    parglare will succeed parsing but will report LoopError during any tree traversal
    as the built SPPF is circular.
    """
    grammar = """
    S: S S;
    S: 'x';
    S: EMPTY;
    """
    g = Grammar.from_string(grammar)

    with pytest.raises(SRConflicts):
        Parser(g, prefer_shifts=False)

    p = GLRParser(g)
    results = p.parse('xx')

    with pytest.raises(LoopError):
        len(results)


@pytest.mark.skipif(sys.version_info < (3, 6),
                    reason="list comparison doesn't work "
                    "correctly in pytest 4.1")
def test_cyclic_grammar_3():
    """
    Grammar with indirect cycle.
    r:EMPTY->A ; r:A->S; r:EMPTY->A; r:SA->S; r:EMPTY->A; r:SA->S;...
    """
    grammar = """
    S: S A | A;
    A: "a" | EMPTY;
    """

    g = Grammar.from_string(grammar)

    # In this grammar we have 3 S/R conflicts where each reduction is EMPTY.
    # If we turn off prefer shifts over empty strategy in LR parser
    # we will get S/R conflict
    with pytest.raises(SRConflicts):
        Parser(g, prefer_shifts_over_empty=False)

    # By default there is no S/R conflict with prefer shifts over
    # empty strategy
    Parser(g)

    p = GLRParser(g)
    results = p.parse('aa')

    with pytest.raises(LoopError):
        len(results)


def test_highly_ambiguous_grammar():
    """
    This grammar has both Shift/Reduce and Reduce/Reduce conflicts and
    thus can't be parsed by a deterministic LR parsing.
    Shift/Reduce can be resolved by prefer_shifts strategy.
    """
    grammar = """
    S: "b" | S S | S S S;
    """

    g = Grammar.from_string(grammar)

    with pytest.raises(SRConflicts):
        Parser(g, prefer_shifts=False)

    # S/R are resolved by selecting prefer_shifts strategy.
    # But R/R conflicts remain.
    with pytest.raises(RRConflicts):
        Parser(g, prefer_shifts=True)

    # GLR parser handles this fine.
    p = GLRParser(g)

    # For three tokens we have 3 valid derivations/trees.
    results = p.parse("bbb")
    assert len(results) == 3

    # For 4 tokens we have 10 valid derivations.
    results = p.parse("bbbb")
    assert len(results) == 10


def test_reduce_enough_empty():
    """
    In this unambiguous grammar parser must reduce as many empty A productions
    as there are "b" tokens ahead to be able to finish successfully, thus it
    needs unlimited lookahead

    Language is: xb^n, n>=0

    References:

    Grammar G3 from: Nozohoor-Farshi, Rahman: "GLR Parsing for ε-Grammers",
    Generalized LR parsing, Springer, 1991.

    Rekers, Joan Gerard: "Parser generation for interactive environments",
    phD thesis, Universiteit van Amsterdam, 1992.

    """
    grammar = """
    S: A S "b";
    S: "x";
    A: EMPTY;
    """
    g = Grammar.from_string(grammar)

    p = GLRParser(g)
    results = p.parse("xbbb")

    assert len(results) == 1


def test_reduce_enough_many_empty():
    """
    This is an extension of the previous grammar where parser must reduce
    enough A B pairs to succeed.

    The language is the same: xb^n, n>=0
    """
    grammar = """
    S: A B S "b";
    S: "x";
    A: EMPTY;
    B: EMPTY;
    """
    g = Grammar.from_string(grammar)

    p = GLRParser(g)
    results = p.parse("xbbb")

    assert len(results) == 1


def test_bounded_ambiguity():
    """
    This grammar has bounded ambiguity.

    The language is the same: xb^n, n>=0 but each valid sentence will
    always have two derivations.

    Grammar G4 from: Nozohoor-Farshi, Rahman: "GLR Parsing for ε-Grammers"
    """

    grammar = """
    S: M | N;
    M: A M "b" | "x";
    N: A N "b" | "x";
    A: EMPTY;
    """

    g = Grammar.from_string(grammar)

    p = GLRParser(g)
    results = p.parse("xbbb")

    assert len(results) == 2


def test_bounded_direct_ambiguity():
    """
    This grammar has bounded direct ambiguity of degree 2, in spite of being
    unboundedly ambiguous as for every k we can find a string that will give at
    least k solutions.

    The language is t^{m}xb^{n}, n>=m>=0

    Grammar G5 from: Nozohoor-Farshi, Rahman: "GLR Parsing for ε-Grammers"
    """
    grammar = """
    S: A S "b" | "x";
    A: "t" | EMPTY;
    """

    g = Grammar.from_string(grammar)

    p = GLRParser(g)
    results = p.parse("txbbbbb")

    assert len(results) == 5


def test_unbounded_ambiguity():
    """
    This grammar has unbounded ambiguity.

    Grammar G6 from: Nozohoor-Farshi, Rahman: "GLR Parsing for ε-Grammers"
    """
    grammar = """
    S: M N;
    M: A M "b" | "x";
    N: "b" N A | "x";
    A: EMPTY;
    """

    g = Grammar.from_string(grammar)

    p = GLRParser(g)
    results = p.parse("xbbbbx")

    assert len(results) == 5


def test_g7():
    """
    Grammar G7 from: Nozohoor-Farshi, Rahman: "GLR Parsing for ε-Grammers"
    """
    grammar = """
    S: "a" S "a" | B S "b" | C S "c" | "x";
    B: "a";
    C: "a";
    """

    g = Grammar.from_string(grammar)

    p = GLRParser(g)
    results = p.parse("aaaaaaaaxbbcaacaa")

    assert len(results) == 1


def test_g8():
    """
    This is another interesting ambiguous grammar.

    Grammar G8 from: Nozohoor-Farshi, Rahman: "GLR Parsing for ε-Grammers"
    """
    grammar = """
    S: "x" | B S "b" | A S "b";
    B: A A;
    A: EMPTY;
    """

    g = Grammar.from_string(grammar)

    p = GLRParser(g)
    results = p.parse("xbbb")

    assert len(results) == 15


def test_right_nullable():
    """
    Grammar Γ2 (pp.17) from:
    Scott, E. and Johnstone, A., 2006. Right nulled GLR parsers. ACM
    Transactions on Programming Languages and Systems (TOPLAS), 28(4),
    pp.577-618.

    """
    grammar = """
    S: "a" S A | EMPTY;
    A: EMPTY;
    """

    g = Grammar.from_string(grammar)

    p = GLRParser(g)
    results = p.parse("aa")

    assert len(results) == 1
