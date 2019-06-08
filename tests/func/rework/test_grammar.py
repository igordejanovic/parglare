"""
Testing grammar construction
"""

from parglare.grammar import Grammar
from parglare.lang import pg_grammar


def test_grammar_construction():
    grammar = Grammar(pg_grammar)

    assert grammar
