# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import codecs
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
    def __init__(self, name, value=None):
        super(Terminal, self).__init__(name)
        self.value = value if value else name

    def __hash__(self):
        return hash(self.value)

    def parse(self, in_str, pos):
        if in_str[pos:].startswith(self.value):
            return self.value
        else:
            return ''


class TerminalRegEx(Terminal):
    def __init__(self, name, regex=None):
        super(Terminal, self).__init__(name)
        self._regex = regex if regex else name
        self.regex = re.compile(self._regex)

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

# Associativity
ASSOC_NONE = 0
ASSOC_LEFT = 1
ASSOC_RIGHT = 2

# Priority
DEFAULT_PRIORITY = 10

class Production(object):
    """Represent production from the grammar.

    Attributes:
    symbol (GrammarSymbol):
    rhs (ProductionRHS):
    assoc (int): Associativity. Used for ambiguity (shift/reduce) resolution.
    prior (int): Priority. Used for ambiguity (shift/reduce) resolution.
    prod_id (int): Ordinal number of the production.
    prod_symbol_id (str): Ident of production in the form "<Symbol>:ord" where
        ordinal is ordinal of the alternative choice starting from 0. Used to
        map actions.
    """

    def __init__(self, symbol, rhs, assoc=ASSOC_NONE, prior=DEFAULT_PRIORITY):
        """
        Args:
        symbol (GrammarSymbol): A grammar symbol on the LHS of the production.
        rhs (list of GrammarSymbols):
        """
        self.symbol = symbol
        self.rhs = rhs if rhs else ProductionRHS()
        self.assoc = assoc
        self.prior = prior

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

    def __init__(self, productions, root_symbol=None):
        self.productions = productions
        self.root_symbol = \
            root_symbol if root_symbol else productions[0].symbol
        self.init_grammar()

    def init_grammar(self):
        """
        Extracts all grammar symbol (nonterminal and terminal) from the
        grammar and check references in productions.
        """
        self.nonterminals = set()
        self.terminals = set()

        # Augmenting grammar. Used for LR item sets calculation.
        self.productions.insert(
            0, Production(AUGSYMBOL, ProductionRHS([self.root_symbol])))

        for s in self.productions:
            if isinstance(s.symbol, NonTerminal):
                self.nonterminals.add(s.symbol)
            else:
                raise Exception("Invalid production symbol type '%s' "
                                "for production '%s'" % (type(s.symbol),
                                                         str(s)))
            for idx, t in enumerate(s.rhs):
                if isinstance(t, Terminal):
                    self.terminals.add(t)
                elif isinstance(t, str):
                    term = TerminalStr(t)
                    self.terminals.add(term)
                    s.rhs[idx] = term

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

    def from_file(file_name):
        with codecs.open(file_name, encoding='utf-8') as f:
            grammar_str = f.read()

        # Parse grammar
        from parglare import Parser
        global productions, GRAMMAR
        p = Parser(create_grammar(productions, GRAMMAR))
        productions = p.parse(grammar_str)
        print(productions.tree_str())

        return create_grammar(productions, productions[0].symbol)

    def print_debug(self):
        print("Terminals:")
        print(" ".join([str(t) for t in self.terminals]))
        print("NonTerminals:")
        print(" ".join([str(n) for n in self.nonterminals]))

        print("Productions:")
        for p in self.productions:
            print(p)


def create_grammar(productions, start_symbol=None):
    """Creates grammar from a list of productions given in the form: (LHS, RHS).
    Where LHS is grammar symbol and RHS is a list or tuple of grammar symbols
    from the right-hand side of the production.
    """
    gp = []
    for p in productions:
        assoc = ASSOC_NONE
        prior = DEFAULT_PRIORITY
        if len(p) > 2:
            assoc = p[2]
        if len(p) > 3:
            prior = p[3]

        gp.append(Production(p[0], ProductionRHS(p[1]), assoc, prior))
    g = Grammar(gp, start_symbol)
    return g


# Grammar for grammars

(GRAMMAR,
 PRODUCTION_SET,
 PRODUCTION,
 PRODUCTION_RHS,
 GSYMBOL,
 NONTERM_REF,
 TERM,
 ASSOC,
 SEQUENCE) = [NonTerminal(name) for name in [
    'Grammar',
    'ProductionSet',
    'Production',
    'ProductionRHS',
    'GSymbol',
    'NonTermRef',
    'Term',
    'Assoc',
    'Sequence']]
NAME = TerminalRegEx('Name', r'[a-zA-Z0-9]+')
STR_TERM = TerminalRegEx("StrTerm", r'"[^"]*"')
REGEX_TERM = TerminalRegEx("RegExTerm", r'\/((\\/)|[^/])*\/')
PRIOR = TerminalRegEx("Prior", r'\d+')
productions = [
    [GRAMMAR, [PRODUCTION_SET]],
    [PRODUCTION_SET, [PRODUCTION]],
    [PRODUCTION_SET, [PRODUCTION_SET, PRODUCTION]],
    [PRODUCTION, [NAME, '=', PRODUCTION_RHS, ';']],
    [PRODUCTION_RHS, [SEQUENCE]],
    [PRODUCTION_RHS, [SEQUENCE, '{', ASSOC, ',', PRIOR, '}']],
    [PRODUCTION_RHS, [PRODUCTION_RHS, '|', PRODUCTION_RHS], ASSOC_LEFT, 5],
    [ASSOC, ['left']],
    [ASSOC, ['right']],
    [SEQUENCE, [GSYMBOL]],
    [SEQUENCE, [SEQUENCE, GSYMBOL]],
    [GSYMBOL, [NONTERM_REF]],
    [GSYMBOL, [TERM]],
    [NONTERM_REF, [NAME]],
    [TERM, [STR_TERM]],
    [TERM, [REGEX_TERM]],
]
