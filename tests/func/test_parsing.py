from __future__ import unicode_literals
import pytest
from parglare import Parser, Grammar, SLR, LALR
from .expression_grammar import get_grammar, E
from parglare.exceptions import ShiftReduceConflict, ParseError


def test_parsing():
    grammar = get_grammar()
    p = Parser(grammar, E)
    p.parse("id+id+id")


def test_lr_1_grammar():
    """From the Knuth's 1965 paper: On the Translation of Languages from Left to
    Right

    """
    grammar = """
    S = 'a' A 'd' | 'b' A B;
    A = 'c' A | 'c';
    B = 'd';
    """

    g = Grammar.from_string(grammar)
    parser = Parser(g)

    parser.parse("acccccccccd")
    parser.parse("bcccccccccd")


def test_slr_conflict():
    """
    Unambiguous grammar which is not SLR(1).
    From the Dragon Book.
    This grammar has a S/R conflict if SLR tables are used.
    """

    grammar = """
    S = L '=' R | R;
    L = '*' R | 'id';
    R = L;
    """

    grammar = Grammar.from_string(grammar)
    with pytest.raises(ShiftReduceConflict):
        Parser(grammar, tables=SLR)

    Parser(grammar, tables=LALR)


def test_lalr_reduce_reduce_conflict():
    """
    Naive merging of states can lead to R/R conflict as shown in this grammar
    from the Dragon Book.
    """

    grammar = """
    S = 'a' A 'd' | 'b' B 'd' | 'a' B 'e' | 'b' A 'e';
    A = C;
    B = C;
    C = 'c';
    """
    grammar = Grammar.from_string(grammar)
    Parser(grammar)


def test_partial_parse():
    """
    Not giving EOF at the end of the sequence enables parsing of the beggining
    of the input string.
    """
    grammar = """
    S = 'a' B;
    B = 'b';
    """
    g = Grammar.from_string(grammar)
    parser = Parser(g)

    # Parser should succesfuly parse 'ab' at the beggining.
    parser.parse('abc')

    # But if EOF is given it will match only at the end of the string,
    # thus, the whole string must be parsed in order for parsing to
    # succeed.
    grammar = """
    S = 'a' B EOF;
    B = 'b';
    """
    g = Grammar.from_string(grammar)
    parser = Parser(g)
    parser.parse('a b')
    with pytest.raises(ParseError):
        parser.parse('a b c')
