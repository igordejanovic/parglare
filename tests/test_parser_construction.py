import pytest
from parglare.parser import first, follow
from parglare.exceptions import NotInitialized
from parglare import Grammar, NonTerminal, TerminalStr, NULL, EOF, \
    create_grammar
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

    # S -> A C
    # A -> B | NULL
    # B -> b
    # C -> c
    S, A, B, C = [NonTerminal(name) for name in ['S', 'A', 'B', 'C']]
    b, c = [
        TerminalStr(value, value) for value in ['b', 'c']]
    productions = [
        (S, (A, C)),
        (A, (B,)),
        (A, (NULL,)),
        (B, (b,)),
        (C, (c,)),
    ]

    g = create_grammar(productions, S)

    first_set = first(g)

    assert NULL in first_set[A]
    assert b in first_set[A]

    assert b in first_set[S]
    assert c in first_set[S]


def test_first_uninitialized():

    g = Grammar()

    with pytest.raises(NotInitialized):
        first(g)


def test_follow():
    """Tests FOLLOW function.

    FOLLOW function calculates a set of terminals that can follow each grammar
    non-terminal in any of derived sentential forms.
    """

    expression_grammar = get_grammar()
    follow_set = follow(expression_grammar)

    assert follow_set[E] == set([CLOSE, PLUS, EOF])

    # Follow of T must contain all of follow of E
    assert follow_set[T] == set([MULT, CLOSE, PLUS, EOF])


def test_follow_uninitialized():

    g = Grammar()

    with pytest.raises(NotInitialized):
        follow(g)
