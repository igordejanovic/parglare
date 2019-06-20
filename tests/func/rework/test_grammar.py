"""
Testing grammar construction
"""

import pytest
from parglare.grammar import (Grammar, MULT_ONE_OR_MORE, MULT_ZERO_OR_MORE,
                              MULT_OPTIONAL)

test_grammar = r'''
A: B C+ EOF;
B: C* D? | D;
terminals
C: 'c';
D: /\d+\/\d+/;
'''


@pytest.fixture
def test_grammar_struct():

    return {
        'rules': {
            'A': {
                'productions': [
                    {'production': ['B', {'symbol': 'C',
                                          'multiplicity': MULT_ONE_OR_MORE},
                                    'EOF']}
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


test_grammar_struct_expanded = {
    'rules': {
        'A': {
            'productions': [
                {'production': ['B', 'C_1', 'EOF']}
            ]
        },
        'B': {
            'productions': [
                {'production': ['C_0', 'D_opt']},
                {'production': ['D']}
            ]
        },
        'C_1': {
            'action': 'collect',
            'productions': [
                {'production': ['C_1', 'C']},
                {'production': ['C']},

            ]
        },
        'C_0': {
            'productions': [
                {'production': ['C_1'], 'nops': True},
                {'production': ['EMPTY']}

            ]
        },
        'D_opt': {
            'action': 'optional',
            'productions': [
                {'production': ['D']},
                {'production': ['EMPTY']}
            ]
        }
    },
    'terminals': {
        'C': {'recognizer': 'c'},
        'D': {'recognizer': r'/\d+\/\d+/'},
    }
}


def test_grammar_construction_from_struct(test_grammar_struct):
    grammar = Grammar.from_struct(test_grammar_struct)
    assert grammar.grammar_struct == test_grammar_struct_expanded


def test_grammar_struct_construction_from_string(test_grammar_struct):
    grammar_struct = Grammar.struct_from_string(test_grammar)
    assert grammar_struct == test_grammar_struct


def test_grammar_from_string():
     grammar = Grammar.from_string(test_grammar)
     assert grammar
