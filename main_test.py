if __name__ == "__main__":

    # Initialize grammar
    from parglare.grammar import Grammar, NonTerminal, Terminal, Production, \
        ProductionRHS
    from parglare.parser import Parser

    g = Grammar()

    E, T, F = [NonTerminal(name) for name in ['E', 'T', 'F']]
    PLUS, MULT, ID, OPEN, CLOSE = [
        Terminal(value, value) for value in ['+', '*', 'id', '(', ')']]
    production = [
        (E, (E, PLUS, T)),
        (E, (T, )),
        (T, (T, MULT, F)),
        (T, (F, )),
        (F, (OPEN, E, CLOSE)),
        (F, (ID,))
    ]
    for p in production:
        g.productions.append(Production(p[0], ProductionRHS(p[1])))

    g.init_grammar()
    g.print_debug()

    # create parser
    parser = Parser(g, root_symbol=E)

    parser.parse("id+id*id")
