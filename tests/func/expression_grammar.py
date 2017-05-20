from parglare import NonTerminal, Terminal, create_grammar


# Expression grammar
E, T, F = [NonTerminal(name) for name in ['E', 'T', 'F']]
PLUS, MULT, ID, OPEN, CLOSE = [
    Terminal(value) for value in ['+', '*', 'id', '(', ')']]
productions = [
    (E, (E, PLUS, T)),
    (E, (T, )),
    (T, (T, MULT, F)),
    (T, (F, )),
    (F, (OPEN, E, CLOSE)),
    (F, (ID,))
]


def get_grammar():
    return create_grammar(productions, E)
