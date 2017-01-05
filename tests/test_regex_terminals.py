import pytest
from parglare import Parser, create_grammar
from parglare import NonTerminal, TerminalStr, TerminalRegEx


# Expression grammar with float numbers
E, T, F = [NonTerminal(name) for name in ['E', 'T', 'F']]
PLUS, MULT, OPEN, CLOSE = [
    TerminalStr(value, value) for value in ['+', '*', '(', ')']]
NUMBER = TerminalRegEx('number', r'\d+(\.\d+)?')
productions = [
    (E, (E, PLUS, T)),
    (E, (T, )),
    (T, (T, MULT, F)),
    (T, (F, )),
    (F, (OPEN, E, CLOSE)),
    (F, (NUMBER,))
]


def test_parse():
    grammar = create_grammar(productions, E)
    p = Parser(grammar, E, debug=True)

    p.parse("45 +23* 89.6")
