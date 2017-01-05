import pytest
from parglare import Parser
from .expression_grammar import get_grammar, E


def test_parsing():
    grammar = get_grammar()
    p = Parser(grammar, E)
    p.parse("id+id+id")
