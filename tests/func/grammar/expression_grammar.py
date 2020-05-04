from parglare import Grammar
from parglare.lang import _

# Expression grammar
expression_grammar = {
    'start': 'S',
    'rules': {
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
                {'production': ['ID']}
            ]
        }
    },
    'terminals': {
        'PLUS': _('+'),
        'MULT': _('*'),
        'OPEN': _('('),
        'CLOSE': _(')'),
        'ID': _('id'),
    }
}


def get_grammar():
    return Grammar.from_struct(expression_grammar)
