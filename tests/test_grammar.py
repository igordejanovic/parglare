import pytest
from parglare import Grammar


def test_terminal_nonterminal():

    # Production A is a terminal ("a") and non-terminal at the same time.
    # Thus, it must be recognized as non-terminal.
    g = """
    S = A B;
    A = "a" | B;
    B = "b";
    """
    Grammar.from_string(g)

    # Here A shoud be non-terminal while B will be terminal.
    g = """
    S = A B;
    A = B;
    B = "b";
    """

    Grammar.from_string(g)


def test_multiple_terminal_definition():

    # A is defined multiple times as terminal thus it must be recognized
    # as non-terminal with alternative expansions.
    g = """
    S = A A;
    A = "a";
    A = "b";
    """

    Grammar.from_string(g)
