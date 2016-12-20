import pytest
from parglare.parser import firsts
from parglare.grammar import Grammar, NonTerminal, Terminal, Production, \
    ProductionRHS, NULL


# Expression grammar
E, T, F = [NonTerminal(name) for name in ['E', 'T', 'F']]
PLUS, MULT, ID, OPEN, CLOSE = [
    Terminal(value, value) for value in ['+', '*', 'id', '(', ')']]
productions = [
    (E, (E, PLUS, T)),
    (E, (T, )),
    (T, (T, MULT, F)),
    (T, (F, )),
    (F, (OPEN, E, CLOSE)),
    (F, (ID,))
]

@pytest.fixture
def expression_grammar():
    # Initialize grammar
    g = Grammar()

    for p in productions:
        g.productions.append(Production(p[0], ProductionRHS(p[1])))

    g.init_grammar()

    return g


def test_first(expression_grammar):
    """
    Tests FIRST function.

    FIRST function returns a set of terminals that could start the sentence
    derived from the given non-terminal.
    """

    first_set = firsts(expression_grammar)

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

    g = Grammar()
    S, A, B, C = [NonTerminal(name) for name in ['S', 'A', 'B', 'C']]
    b, c = [
        Terminal(value, value) for value in ['b', 'c']]
    productions = [
        (S, (A, C)),
        (A, (B,)),
        (A, (NULL,)),
        (B, (b,)),
        (C, (c,)),
    ]

    for p in productions:
        g.productions.append(Production(p[0], ProductionRHS(p[1])))

    g.init_grammar()

    first_set = firsts(g)

    assert NULL in first_set[A]
    assert b in first_set[A]

    assert b in first_set[S]
    assert c in first_set[S]


def test_follow():
    """
    Tests FOLLOW function.

    FOLLOW function calculates a set of terminals that can follow given
    non-terminal in any of derived sentential forms.
    """





