import pytest
from parglare.grammar import Grammar, Terminal, NonTerminal


def test_terminal_nonterminal():

    # Production A is a terminal ("a") and non-terminal at the same time.
    # Thus, it must be recognized as non-terminal.
    grammar = """
    S = A B;
    A = "a" | B;
    B = "b";
    """
    g = Grammar.from_string(grammar)
    assert NonTerminal("A") in g.nonterminals
    assert Terminal("A") not in g.terminals
    assert Terminal("B") in g.terminals
    assert NonTerminal("B") not in g.nonterminals

    # Here A shoud be non-terminal while B will be terminal.
    grammar = """
    S = A B;
    A = B;
    B = "b";
    """

    g = Grammar.from_string(grammar)
    assert NonTerminal("A") in g.nonterminals
    assert Terminal("A") not in g.terminals
    assert Terminal("B") in g.terminals
    assert NonTerminal("B") not in g.nonterminals


def test_multiple_terminal_definition():

    # A is defined multiple times as terminal thus it must be recognized
    # as non-terminal with alternative expansions.
    grammar = """
    S = A A;
    A = "a";
    A = "b";
    """

    g = Grammar.from_string(grammar)

    assert NonTerminal("A") in g.nonterminals
    assert Terminal("A") not in g.terminals
