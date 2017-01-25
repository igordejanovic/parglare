from __future__ import unicode_literals
import pytest
from parglare import Parser, Grammar, SLR, LALR
from .expression_grammar import get_grammar, E
from parglare.exceptions import ShiftReduceConflict


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
