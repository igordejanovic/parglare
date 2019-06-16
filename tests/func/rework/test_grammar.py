"""
Testing grammar construction
"""

from parglare.grammar import (Grammar, MULT_ONE_OR_MORE, MULT_ZERO_OR_MORE,
                              MULT_OPTIONAL)
from parglare.lang import pg_grammar

test_grammar = r'''
A: B C+;
B: C* D? | D;
terminals
C: 'c';
D: /\d+\/\d+/;
'''

test_grammar_struct = {
    'rules': {
        'A': {
            'productions': [
                {'production': ['B', {'symbol': 'C',
                                      'multiplicity': MULT_ONE_OR_MORE}]}
            ]
        },
        'B': {
            'productions': [
                {'production': [{'symbol': 'C',
                                 'multiplicity': MULT_ZERO_OR_MORE},
                                {'symbol': 'D',
                                 'multiplicity': MULT_OPTIONAL}]},
                {'production': ['D']}
            ]
        }
    },
    'terminals': {
        'C': {'recognizer': 'c'},
        'D': {'recognizer': r'/\d+\/\d+/'},
    }
}


def test_grammar_construction_from_struct():
    grammar = Grammar.from_struct(pg_grammar)
    assert grammar


def test_grammar_struct_construction_from_string():
    grammar_struct = Grammar.struct_from_string(test_grammar)
    assert grammar_struct == test_grammar_struct


# def test_grammar_from_string():
#     grammar = Grammar.from_string(test_grammar)

#     assert grammar
