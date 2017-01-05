import pytest
from parglare import Parser
from .expression_grammar_numbers import get_grammar, E


def test_parse():
    grammar = get_grammar()
    p = Parser(grammar, E)

    tree = p.parse("45 +23* 89.6")

    assert tree
