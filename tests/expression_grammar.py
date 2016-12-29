from parglare.grammar import Grammar, NonTerminal, TerminalStr, Production, \
    ProductionRHS


# Expression grammar
E, T, F = [NonTerminal(name) for name in ['E', 'T', 'F']]
PLUS, MULT, ID, OPEN, CLOSE = [
    TerminalStr(value, value) for value in ['+', '*', 'id', '(', ')']]
productions = [
    (E, (E, PLUS, T)),
    (E, (T, )),
    (T, (T, MULT, F)),
    (T, (F, )),
    (F, (OPEN, E, CLOSE)),
    (F, (ID,))
]


def get_grammar():

    # Initialize grammar
    g = Grammar()

    for p in productions:
        g.productions.append(Production(p[0], ProductionRHS(p[1])))

    g.init_grammar(E)

    return g
