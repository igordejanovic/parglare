import pytest
from parglare.parser import first, follow
from parglare import Grammar, NonTerminal, TerminalStr, EMPTY
from parglare.grammar import STOP
from .expression_grammar import OPEN, ID, T, E, MULT, CLOSE, PLUS, get_grammar


def test_first():
    """
    Tests FIRST function.

    FIRST function returns a set of terminals that could start the sentence
    derived from the given non-terminal.
    """

    expression_grammar = get_grammar()
    first_set = first(expression_grammar)

    assert OPEN in first_set[T]
    assert ID in first_set[T]


def test_first_empty_in_rhs():
    """
    Test FIRST calculation when there are empty derivations in RHS of a
    production.
    """

    grammar = """
    S = A C;
    A = B | EMPTY;
    B = "b";
    C = "c";
    """

    g = Grammar.from_string(grammar)

    first_set = first(g)

    assert EMPTY in first_set[NonTerminal('A')]
    assert TerminalStr('B') in first_set[NonTerminal('A')]

    assert TerminalStr('B') in first_set[NonTerminal('S')]

    # 'A' can derive empty, thus 'C' must be in firsts of 'S'.
    assert TerminalStr('C') in first_set[NonTerminal('S')]


def test_follow():
    """Tests FOLLOW function.

    FOLLOW function calculates a set of terminals that can follow each grammar
    non-terminal in any of derived sentential forms.
    """

    expression_grammar = get_grammar()
    follow_set = follow(expression_grammar)

    assert follow_set[E] == set([CLOSE, PLUS, STOP])

    # Follow of T must contain all of follow of E
    assert follow_set[T] == set([MULT, CLOSE, PLUS, STOP])
