# -*- coding: utf-8 -*-
from parglare.builder import GrammarBuilder
from parglare.grammar import MULT_ONE_OR_MORE, MULT_ZERO_OR_MORE, MULT_OPTIONAL


def test_happy_path1():
    target = {
        'start': 'A',
        'rules': {
            'A': {
                'productions': [
                    {'production': ['B', {'symbol': 'C',
                                          'mult': MULT_ONE_OR_MORE,
                                          'modifiers': ['COMMA', 'nogreedy']}]}
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

    builder = GrammarBuilder()
    (builder.start('A')
            .rule('A').production('B', ('C', MULT_ONE_OR_MORE, ['COMMA', 'nogreedy']))
            .rule('B').production().append('C', MULT_ZERO_OR_MORE).append('D', MULT_OPTIONAL).production('D')
            .terminal('C', 'c')
            .terminal('D').recognizer(r'/\d+\/\d+/')
            .terminal('COMMA', ','))
    struct = builder.get_struct()
    assert struct == target


def test_happy_path2():
    target = {
        'start': "A",
        'rules': {
            "S'": {
                'productions': [
                    {'production': ['A', 'STOP']}
                ]
            },
            'A': {
                'productions': [
                    {'production': ['B', 'C_1_COMMA_nogreedy']}
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

    builder = GrammarBuilder()
    (builder.start('A')
            .rule("S'").production('A', 'STOP')
            .rule('A').production('B', 'C_1_COMMA_nogreedy')
            .rule('B').production('C_0', 'D_opt').production('D')
            .rule('C_1_COMMA_nogreedy')
            .action('collect_sep')
            .production('C_1_COMMA_nogreedy', 'COMMA', 'C', modifiers='nogreedy')
            .production('C')
            .rule('C_1').action('collect').production('C_1', 'C').production('C')
            .rule('C_0').production('C_1').production('EMPTY')
            .rule('D_opt').action('optional').production('D').production('EMPTY')
            .terminal('C', 'c')
            .terminal('D').recognizer(r'/\d+\/\d+/')
            .terminal('COMMA', ','))
    struct = builder.get_struct()
    assert struct == target
