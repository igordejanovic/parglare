# -*- coding: utf-8 -*-
import pytest  # noqa
from parglare.parser import Parser
from ..grammar.expression_grammar import get_grammar


def test_to_str():

    grammar = get_grammar()
    p = Parser(grammar, build_tree=True)

    res = p.parse("""id+  id * (id
    +id  )
    """)

    ts = res.to_str()

    assert '+[18->19, "+"]' in ts
    assert ')[23->24, ")"]' in ts
    assert 'F[10->24]' in ts
