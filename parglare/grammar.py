# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import re


class GrammarSymbol(object):
    def __init__(self, name):
        self.name = name

    def __unicode__(self):
        return str(self)

    def __str__(self):
        return self.name

    def __repr__(self):
        return str(self)


class NonTerminal(GrammarSymbol):
    pass


class Terminal(GrammarSymbol):
    pass


class TerminalStr(Terminal):
    def __init__(self, name, value):
        super(Terminal, self).__init__(name)
        self.value = value

    def __hash__(self):
        return hash(self.value)

    def parse(self, in_str, pos):
        if in_str[pos:].startswith(self.value):
            return self.value
        else:
            return ''


class TerminalRegEx(Terminal):
    def __init__(self, name, regex):
        super(Terminal, self).__init__(name)
        self._regex = regex
        self.regex = re.compile(regex)

    def __hash__(self):
        return hash(self._regex)

    def parse(self, in_str, pos):
        m = self.regex.match(in_str, pos)
        if m:
            matched = m.group()
            return matched
        else:
            return ''


AUGSYMBOL = NonTerminal("S'")
NULL = TerminalStr("Empty", "ɛ")
EOF = TerminalStr("EOF", "$")


class Production(object):
    """Represent production from the grammar.

    Attributes:
    symbol (GrammarSymbol):
    rhs (ProductionRHS):
    prod_id (int): Ordinal number of the production.
    prod_symbol_id (str): Ident of production in the form "<Symbol>:ord" where
        ordinal is ordinal of the alternative choice starting from 0. Used to
        map actions.
    """

    def __init__(self, symbol, rhs):
        """
        Args:
        symbol (GrammarSymbol): A grammar symbol on the LHS of the production.
        rhs (list of GrammarSymbols):
        """
        self.symbol = symbol
        self.rhs = rhs if rhs else ProductionRHS()

    def __str__(self):
        return "%d: %s -> %s" % (self.prod_id, self.symbol, self.rhs)


class ProductionRHS(list):
    def __getitem__(self, key):
        try:
            return super(ProductionRHS, self).__getitem__(key)
        except IndexError:
            return None

    def __str__(self):
        return " ".join([str(x) for x in self])


class Grammar(object):
    """
    Grammar is a collection of production rules.
    First production is reserved for the augmented production (S' -> S).
    """

    def __init__(self):
        self.productions = []

    def init_grammar(self, root_symbol):
        """
        Extracts all grammar symbol (nonterminal and terminal) from the
        grammar and check references in productions.
        """
        self.nonterminals = set()
        self.terminals = set()
        self.root_symbol = root_symbol

        # Augmenting grammar. Used for LR item sets calculation.
        if self.productions[0].symbol is not AUGSYMBOL:
            self.productions.insert(
                0, Production(AUGSYMBOL, ProductionRHS([root_symbol])))

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

        # Enumerate productions
        idx_per_symbol = {}
        for idx, s in enumerate(self.productions):
            s.prod_id = idx
            s.prod_symbol_id = "{}:{}".format(s.symbol,
                                              idx_per_symbol.get(s.symbol, 0))
            idx_per_symbol[s.symbol] = idx_per_symbol.get(s.symbol, 0) + 1
            for ref in s.rhs:
                if ref not in self.nonterminals and ref not in self.terminals:
                    raise Exception("Undefined grammar symbol '%s' referenced "
                                    "in production '%s'." % (ref, s))

    def print_debug(self):
        print("Terminals:")
        print(" ".join([str(t) for t in self.terminals]))
        print("NonTerminals:")
        print(" ".join([str(n) for n in self.nonterminals]))

        print("Productions:")
        for p in self.productions:
            print(p)


def create_grammar(productions, start_symbol):
    """Creates grammar from a list of productions given in the form: (LHS, RHS).
    Where LHS is grammar symbol and RHS is a list or tuple of grammar symbols
    from the right-hand side of the production.
    """
    g = Grammar()
    for p in productions:
        g.productions.append(Production(p[0], ProductionRHS(p[1])))
    g.init_grammar(start_symbol)
    return g
