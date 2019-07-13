from parglare import Grammar
from parglare.lang import _


# Expression grammar with float numbers
expression_grammar = {
    'start': 'S',
    'rules': {
        'S': {
            'productions': [
                {'action': 'pass_single',
                 'production': ['E', 'EOF']},
            ]
        },
        'E': {
            'productions': [
                {'production': ['E', 'PLUS', 'T']},
                {'production': ['T']}
            ]
        },
        'T': {
            'productions': [
                {'production': ['T', 'MULT', 'F']},
                {'production': ['F']},
            ]
        },
        'F': {
            'productions': [
                {'production': ['OPEN', 'E', 'CLOSE']},
                {'production': ['NUMBER']}
            ]
        }
    },
    'terminals': {
        'PLUS': _('+'),
        'MULT': _('*'),
        'OPEN': _('('),
        'CLOSE': _(')'),
        'NUMBER': _(r'/\d+(\.\d+)?/'),
    }
}


def get_grammar():
    return Grammar.from_struct(expression_grammar)
