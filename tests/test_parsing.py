import pytest
from parglare.parser import Parser
from .expression_grammar import get_grammar, E


def test_parsing():
    grammar = get_grammar()

    p = Parser(grammar, E, debug=True)

    p.parse("id+id+id")

    assert False
