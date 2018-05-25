# -*- coding: utf-8 -*-
"""
Test non-deterministic parsing.
"""
from __future__ import unicode_literals
import pytest  # noqa
from parglare import Parser, GLRParser, Grammar, SLR, LALR
from parglare.exceptions import ParseError, SRConflicts, RRConflicts


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
    From the paper: "GLR Parsing for e-Grammers" by Rahman Nozohoor-Farshi
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

    # x -> A -> S
    assert len(results) == 1


def todo_test_cyclic_grammar_2():
    """
    From the paper: "GLR Parsing for e-Grammers" by Rahman Nozohoor-Farshi

    """
    grammar = """
    S: S S;
    S: 'x';
    S: EMPTY;
    """
    g = Grammar.from_string(grammar)

    with pytest.raises(SRConflicts):
        Parser(g, prefer_shifts=False)

    p = GLRParser(g, debug=True)
    results = p.parse('xx')

    # This grammar has infinite ambiguity but by minimizing empty reductions
    # we shall get only one result xx -> xS -> SS -> S
    assert len(results) == 1


def test_cyclic_grammar_3():
    grammar = """
    S: S A | A;
    A: "a" | EMPTY;
    """

    g = Grammar.from_string(grammar)

    Parser(g)

    p = GLRParser(g, debug=True)
    results = p.parse('aa')

    assert len(results) == 1


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


def test_indirect_left_recursive():
    """Grammar with indirect/hidden left recursion.

    parglare LR parser will handle this using implicit disambiguation by
    prefering shifts over empty reductions. It will greadily match "b" tokens
    and than reduce EMPTY before "a" and start to reduce by 'B="b" B'
    production.

    """

    grammar = """
    S: B "a";
    B: "b" B | EMPTY;
    """

    g = Grammar.from_string(grammar)

    p = Parser(g)
    p.parse("bbbbbbbbbbbba")

    p = GLRParser(g, debug=True)
    results = p.parse("bbbbbbbbbbbba")
    assert len(results) == 1


def test_reduce_enough_empty():
    """In this unambiguous grammar parser must reduce as many empty A productions
    as there are "b" tokens ahead to be able to finish successfully, thus it
    needs unlimited lookahead

    Language is: xb^n, n>=0

    References:

    Nozohoor-Farshi, Rahman: "GLR Parsing for ε-Grammers", Generalized LR
    parsing, Springer, 1991.

    Rekers, Joan Gerard: "Parser generation for interactive environments",
    phD thesis, Universiteit van Amsterdam, 1992.

    """
    grammar = """
    S: A S "b";
    S: "x";
    A: EMPTY;
    """
    g = Grammar.from_string(grammar)

    p = GLRParser(g, debug=True)
    results = p.parse("xbbb")

    assert len(results) == 1
