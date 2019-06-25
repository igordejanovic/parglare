"""
Testing grammar construction
"""

import pytest
from parglare import Parser
from parglare.grammar import (Grammar, MULT_ONE_OR_MORE, MULT_ZERO_OR_MORE,
                              MULT_OPTIONAL)

test_grammar = r'''
A: B C+[COMMA, nogreedy] EOF;
B: C* D? | D;
terminals
C: 'c';
D: /\d+\/\d+/;
COMMA: ',';
'''


@pytest.fixture
def test_grammar_struct():

    return {
        'start': 'A',
        'rules': {
            'A': {
                'productions': [
                    {'production': ['B', {'symbol': 'C',
                                          'mult': MULT_ONE_OR_MORE,
                                          'modifiers': ['COMMA', 'nogreedy']},
                                    'EOF']}
                ]
            },
            'B': {
                'productions': [
                    {'production': [{'symbol': 'C',
                                    'mult': MULT_ZERO_OR_MORE},
                                    {'symbol': 'D',
                                    'mult': MULT_OPTIONAL}]},
                    {'production': ['D']}
                ]
            }
        },
        'terminals': {
            'C': {'recognizer': 'c'},
            'D': {'recognizer': r'/\d+\/\d+/'},
            'COMMA': {'recognizer': ','},
        }
    }


test_grammar_struct_desugared = {
    'start': "S'",
    'rules': {
        "S'": {
            'productions': [
                {'production': ['A', 'STOP']}
            ]
        },
        'A': {
            'productions': [
                {'production': ['B', 'C_1_COMMA_nogreedy', 'EOF']}
            ]
        },
        'B': {
            'productions': [
                {'production': ['C_0', 'D_opt']},
                {'production': ['D']}
            ]
        },
        'C_1_COMMA_nogreedy': {
            'action': 'collect_sep',
            'productions': [
                {'production': ['C_1_COMMA_nogreedy', 'COMMA', 'C'],
                 'modifiers': ['nogreedy']},
                {'production': ['C']},

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
                {'production': ['C_1']},
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
        'COMMA': {'recognizer': ','},
    }
}


def test_grammar_construction_from_struct(test_grammar_struct):
    grammar = Grammar.from_struct(test_grammar_struct)
    assert grammar.grammar_struct == test_grammar_struct_desugared


def test_grammar_struct_construction_from_string(test_grammar_struct):
    grammar_struct = Grammar.struct_from_string(test_grammar)
    assert grammar_struct == test_grammar_struct


def test_grammar_from_string():
    grammar = Grammar.from_string(test_grammar)
    assert grammar
    parser = Parser(grammar)
    result = parser.parse('c c c c 34/44 c,c,c ')
    assert result == [[['c', 'c', 'c', 'c'], '34/44'], ['c', 'c', 'c'], None]
