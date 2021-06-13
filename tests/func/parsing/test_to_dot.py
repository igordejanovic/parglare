# -*- coding: utf-8 -*-
import pytest  # noqa
from parglare import Parser, GLRParser, Grammar
from ..grammar.expression_grammar import get_grammar


def test_to_dot():

    grammar = get_grammar()
    p = Parser(grammar, build_tree=True)

    res = p.parse("""id+  id * (id
    +id  )
    """)

    ts = res.to_dot()

    assert '[label="T[11-13]"];' in ts
    assert '[label="+[2-3]"];' in ts


def test_forest_to_dot():

    grammar = Grammar.from_string(r'''
    E: E "+" E | E "-" E | "(" E ")" | "id";
    ''')
    p = GLRParser(grammar)

    forest = p.parse("""id+  id - (id
    +id  )
    """)

    ts = forest.to_dot()

    assert '[label="+[18-19]"];' in ts
    assert '[label="E[5-7]"];' in ts
    assert '[label="Amb(E[0-24],2)" shape=box];' in ts
