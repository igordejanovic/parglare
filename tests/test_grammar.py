import pytest
from parglare import Grammar
from parglare.exceptions import GrammarError


def test_terminal_nonterminal_conflict():

    # Production A is a terminal ("a") and non-terminal at the same time.
    g = """
    A = "a" | B;
    B = "b";
    """
    try:
        Grammar.from_string(g)
        assert False
    except GrammarError as e:
        assert 'Multiple definition' in str(e)


def test_multiple_terminal_definition():

    g = """
    S = A A;
    A = "a";
    A = "b";
    """
    try:
        Grammar.from_string(g)
        assert False
    except GrammarError as e:
        assert 'Multiple definition' in str(e)
