from parglare import NonTerminal, Terminal, Grammar, EOF


# Expression grammar
S, E, T, F = [NonTerminal(name) for name in ['S', 'E', 'T', 'F']]
PLUS, MULT, ID, OPEN, CLOSE = [
    Terminal(value) for value in ['+', '*', 'id', '(', ')']]
productions = [
    (S, (E, EOF)),
    (E, (E, PLUS, T)),
    (E, (T, )),
    (T, (T, MULT, F)),
    (T, (F, )),
    (F, (OPEN, E, CLOSE)),
    (F, (ID,))
]


def get_grammar():
    return Grammar.from_struct(productions=productions, start_symbol=S)
