from __future__ import unicode_literals


class Parser(object):
    """
    Parser works like a state machine driven by a LR table.
    LR table will be created and cached or loaded from cache if cache is found.
    """
    def __init__(self, grammar):
        self.grammar = grammar
        grammar.init_grammar()
        self.states = []
        self.actions = {}
        self.goto = []

        self._init_parser()

    def _init_parser(self):
        """Create parser states and tables."""
        self._create_state_item_collections()
        self._create_tables()

    def _create_state_item_collections(self):

        # Create I0 for the first production
        s = LRState(self, 0, [LRItem(self.grammar.productions[0], 0)])

        state_stack = [s]
        state_id = 1

        while state_stack:
            s = state_stack.pop()
            s.closure()
            goto = {}
            self.states.append(s)
            self.goto.append(goto)

            per_next_symbol = {}
            for i in s.items:
                symbol = i.production.rhs[i.position]
                if symbol:
                    per_next_symbol.setdefault(symbol, []).append(i)

            for symbol, items in per_next_symbol.items():
                inc_items = [i.get_pos_inc() for i in items]
                maybe_new_state = LRState(self, state_id, inc_items)
                if maybe_new_state not in self.states and \
                   maybe_new_state not in state_stack:
                    state_stack.append(maybe_new_state)
                    state_id += 1

        for s in self.states:
            s.print_debug()

    def _create_tables(self):
        pass

    def parse(self, input_str):
        pass


class GrammarSymbol(object):
    def __init__(self, name):
        self.name = name

    def __unicode__(self):
        return str(self)

    def __str__(self):
        return self.name


class NonTerminal(GrammarSymbol):
    pass


class Terminal(GrammarSymbol):
    def __init__(self, name, value):
        super(Terminal, self).__init__(name)
        self.value = value

    def __hash__(self):
        return hash(self.value)


AUGSYMBOL = NonTerminal("S'")


class Production(object):
    """Represent production from the grammar."""

    def __init__(self, symbol, rhs):
        """
        Args:
        symbol (GrammarSymbol): A grammar symbol on the LHS of the production.
        rhs (list of GrammarSymbols):
        """
        self.symbol = symbol
        self.rhs = rhs if rhs else ProductionRHS()

    def __str__(self):
        return "%s -> %s" % (self.symbol, self.rhs)


class ProductionRHS(list):
    def __getitem__(self, key):
        try:
            return super(ProductionRHS, self).__getitem__(key)
        except IndexError:
            return None

    def __str__(self):
        return " ".join([str(x) for x in self])


class Grammar(object):
    """Grammar is a collection of production rules.
    First production is the augmented production (S' -> S)."""

    def __init__(self):
        self.productions = [None]
        self.nonterminals = set()
        self.terminals = set()

    def set_root_symbol(self, root_symbol):
        self.productions[0] = Production(AUGSYMBOL,
                                         ProductionRHS([root_symbol]))

    def init_grammar(self):
        """Extracts all grammar symbol (nonterminal and terminal) from the
        grammar and check references in productions."""

        self.set_root_symbol(self.productions[1].symbol)

        for s in self.productions:
            if isinstance(s.symbol, NonTerminal):
                self.nonterminals.add(s.symbol)
            else:
                raise Exception("Invalid production symbol type '%s' "
                                "for production '%s'" % (type(s.symbol),
                                                         str(s)))
            for t in s.rhs:
                if isinstance(t, Terminal):
                    self.terminals.add(t)

        for s in self.productions:
            for ref in s.rhs:
                if ref not in self.nonterminals and ref not in self.terminals:
                    raise Exception("Undefined grammar symbol '%s' referenced "
                                    "in production '%s'." % (ref, s))

    def print_debug(self):
        print("Terminals:")
        print(" ".join([str(t) for t in self.terminals]))
        print("NonTerminals:")
        print(" ".join([str(n) for n in self.nonterminals]))


class LRItem(object):
    __slots__ = ('production', 'position')

    def __init__(self, production, position):
        self.production = production
        self.position = position

    def __eq__(self, other):
        return other and self.production == other.production and \
            self.position == other.position

    def __str__(self):
        s = ""
        for idx, r in enumerate(self.production.rhs):
            if idx == self.position:
                s += " ."
            s += " " + str(r)
        if len(self.production.rhs) == self.position:
            s += " ."

        return "%s -> %s" % (self.production.symbol, s)

    @property
    def is_kernel(self):
        """
        Kernel items are items whose position is not at the beginning.
        The only exception to this rule is start symbol of the augmented
        grammar.
        """
        return self.position > 0 or self.production.symbol is AUGSYMBOL

    def get_pos_inc(self):
        """Returns new LRItem with incremented position or None if position
        cannot be incremented (e.g. it is already at the end of the production)
        """

        if self.position < len(self.production.rhs):
            return LRItem(self.production, self.position+1)


class LRState(object):
    """LR State is a set of LR items."""

    def __init__(self, parser, state_id, items):
        self.parser = parser
        self.state_id = state_id
        self.items = items if items else []

    def __eq__(self, other):
        """Two states are equal if their kernel items are equal."""
        for item in self.items:
            if item.is_kernel:
                if item not in other.items:
                    return False
        return True

    def closure(self):
        """Forms a closure of the state. Adds all missing items."""

        while True:
            has_additions = False
            for item in self.items:
                gs = item.production.rhs[item.position]
                to_add = []
                if isinstance(gs, NonTerminal):
                    for p in self.parser.grammar.productions:
                        if p.symbol is gs:
                            new_item = LRItem(p, 0)
                            if new_item not in self.items:
                                to_add.append(new_item)
                                has_additions = True

            if has_additions:
                self.items.extend(to_add)
            else:
                break

    def print_debug(self):
        print("\nState %d" % self.state_id)
        for i in self.items:
            print("\t", i)


if __name__ == "__main__":

    # Initialize grammar

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

    g.set_root_symbol(E)

    # create parser
    parser = Parser(g)

    parser.parse("id+id*id")
