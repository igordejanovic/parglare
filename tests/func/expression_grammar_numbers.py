from parglare import create_grammar
from parglare import NonTerminal, Terminal, RegExRecognizer


# Expression grammar with float numbers
E, T, F = [NonTerminal(name) for name in ['E', 'T', 'F']]
PLUS, MULT, OPEN, CLOSE = [
    Terminal(value) for value in ['+', '*', '(', ')']]
NUMBER = Terminal('number', RegExRecognizer(r'\d+(\.\d+)?'))
productions = [
    (E, (E, PLUS, T)),
    (E, (T, )),
    (T, (T, MULT, F)),
    (T, (F, )),
    (F, (OPEN, E, CLOSE)),
    (F, (NUMBER,))
]


def get_grammar():
    return create_grammar(productions, E)
