import pytest
from parglare.parser import Parser
from .expression_grammar import get_grammar, E


def test_tree_str():

    grammar = get_grammar()
    p = Parser(grammar)

    res = p.parse("""id+  id * (id
    +id  )
    """)

    ts = res.tree_str()

    assert '+[18, +]' in ts
    assert ')[23, )]' in ts
