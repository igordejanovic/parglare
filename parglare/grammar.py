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


class TerminalRegEx(Terminal):
    def __init__(self, name, regex):
        super(Terminal, self).__init__(name)
        self.regex = re.compile(regex)

    def __hash__(self):
        return hash(self.value)


AUGSYMBOL = NonTerminal("S'")
NULL = TerminalStr("Empty", "ɛ")
EOF = TerminalStr("EOF", "$")


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
    """
    Grammar is a collection of production rules.
    First production is the augmented production (S' -> S).
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
