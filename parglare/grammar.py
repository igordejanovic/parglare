# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function
import sys
import re
from parglare.exceptions import GrammarError

if sys.version < '3':
    text = unicode  # NOQA
else:
    text = str

# Associativity
ASSOC_NONE = 0
ASSOC_LEFT = 1
ASSOC_RIGHT = 2

# Priority
DEFAULT_PRIORITY = 10


def escape(instr):
    return instr.replace('\n', r'\n').replace('\t', r'\t')


class GrammarSymbol(object):
    def __init__(self, name):
        self.name = escape(name)

    def __unicode__(self):
        return str(self)

    def __str__(self):
        return self.name

    def __repr__(self):
        return "{}({})".format(type(self).__name__, str(self))

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        return self.name == other.name


class NonTerminal(GrammarSymbol):
    pass


class Terminal(GrammarSymbol):
    def __init__(self, name):
        self.prior = DEFAULT_PRIORITY
        super(Terminal, self).__init__(name)


class TerminalStr(Terminal):
    def __init__(self, name, value=None):
        super(TerminalStr, self).__init__(name)
        self.value = value if value else name

    def parse(self, in_str, pos):
        if in_str[pos:pos+len(self.value)] == self.value:
            return self.value
        else:
            return ''


class TerminalRegEx(Terminal):
    def __init__(self, name, regex=None):
        super(TerminalRegEx, self).__init__(name)
        self._regex = regex if regex else name
        self.regex = re.compile(self._regex)

    def parse(self, in_str, pos):
        m = self.regex.match(in_str, pos)
        if m:
            matched = m.group()
            return matched
        else:
            return ''


class TerminalEmpty(Terminal):
    def parse(self, in_str, pos):
        return ''


class TerminalEOF(Terminal):
    def parse(self, in_str, pos):
        return ''


class TerminalStop(Terminal):
    def parse(self, in_str, pos):
        return ''


# These two terminals are special terminals used internally.
AUGSYMBOL = NonTerminal("S'")
STOP = TerminalStop("STOP")

# These two terminals are special terminals used in the grammars.
# EMPTY will match nothing and always succeeds.
# EOF will match only at the end of the input string.
EMPTY = TerminalEmpty("EMPTY")
EOF = TerminalEOF("EOF")


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
        if hasattr(self, 'prod_id'):
            return "%d: %s = %s" % (self.prod_id, self.symbol, self.rhs)
        else:
            return "%s = %s" % (self.symbol, self.rhs)

    def __repr__(self):
        return 'Production({})'.format(str(self.symbol))


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

    Attributes:
    productions (list of Production):
    root_symbol (GrammarSymbol): start/root symbol of the grammar.
    nonterminals (set of NonTerminal):
    terminals(set of Terminal):

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

        # Reserve 0 production. It is used for augmented prod. in LR
        # automata calculation.
        self.productions.insert(
            0,
            Production(AUGSYMBOL, ProductionRHS([self.productions[0].symbol,
                                                 STOP])))

        for s in self.productions:
            if isinstance(s.symbol, NonTerminal):
                self.nonterminals.add(s.symbol)
            else:
                raise GrammarError("Invalid production symbol '%s' "
                                   "for production '%s'" % (s.symbol,
                                                            text(s)))
            for idx, t in enumerate(s.rhs):
                if isinstance(t, Terminal):
                    self.terminals.add(t)
                elif isinstance(t, text):
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
                    raise GrammarError("Undefined grammar symbol '%s' "
                                       "referenced from production '%s'."
                                       % (ref, s))

    def get_terminal(self, name):
        "Returns terminal with the given name."
        for t in self.terminals:
            if t.name == name:
                return t

    def get_nonterminal(self, name):
        "Returns non-terminal with the given name."
        for n in self.nonterminals:
            if n.name == name:
                return n

    def get_symbol(self, name):
        "Returns grammar symbol with the given name."
        s = self.get_terminal(name)
        if not s:
            s = self.get_nonterminal(name)
        return s

    def get_production(self, name):
        "Returns first production number for the given symbol name"
        for idx, p in enumerate(self.productions):
            if p.symbol.name == name:
                return idx

    @staticmethod
    def from_string(grammar_str):
        from parglare import Parser
        global pg_productions, GRAMMAR, pg_actions
        p = Parser(create_grammar(pg_productions, GRAMMAR), actions=pg_actions)
        prods = p.parse(grammar_str)
        return Grammar(prods)

    @staticmethod
    def from_file(file_name):
        from parglare import Parser
        global pg_productions, GRAMMAR, pg_actions
        p = Parser(create_grammar(pg_productions, GRAMMAR), actions=pg_actions)
        prods = p.parse_file(file_name)
        return Grammar(prods)

    def print_debug(self):
        print("Terminals:")
        print(" ".join([text(t) for t in self.terminals]))
        print("NonTerminals:")
        print(" ".join([text(n) for n in self.nonterminals]))

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
 PRODUCTION_RHSS,
 PRODUCTION_RHS,
 GSYMBOL,
 NONTERM_REF,
 TERM,
 ASSOC,
 ASSOC_PRIOR,
 SEQUENCE) = [NonTerminal(name) for name in [
    'Grammar',
    'ProductionSet',
    'Production',
    'ProductionRHSs',
    'ProductionRHS',
    'GSymbol',
    'NonTermRef',
    'Term',
    'Assoc',
    'AssocPrior',
    'Sequence']]
NAME = TerminalRegEx('Name', r'[a-zA-Z0-9]+')
STR_TERM = TerminalRegEx("StrTerm",
                         r'''(?s)('[^'\\]*(?:\\.[^'\\]*)*')|'''
                         r'''("[^"\\]*(?:\\.[^"\\]*)*")''')
REGEX_TERM = TerminalRegEx("RegExTerm",
                           r'''\/((\\/)|[^/])*\/''')
PRIOR = TerminalRegEx("Prior", r'\d+')
pg_productions = [
    [GRAMMAR, [PRODUCTION_SET]],
    [PRODUCTION_SET, [PRODUCTION]],
    [PRODUCTION_SET, [PRODUCTION_SET, PRODUCTION]],
    [PRODUCTION, [NAME, '=', PRODUCTION_RHSS, ';']],
    [PRODUCTION_RHS, [SEQUENCE]],
    [PRODUCTION_RHS, [SEQUENCE, '{', ASSOC_PRIOR, '}']],
    [PRODUCTION_RHSS, [PRODUCTION_RHS], ASSOC_LEFT, 5],
    [PRODUCTION_RHSS, [PRODUCTION_RHSS, '|', PRODUCTION_RHS], ASSOC_LEFT, 5],
    [ASSOC_PRIOR, [ASSOC]],
    [ASSOC_PRIOR, [PRIOR]],
    [ASSOC_PRIOR, [ASSOC_PRIOR, ',', ASSOC_PRIOR], ASSOC_LEFT],
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


def act_term_str(_, nodes):
    value = nodes[0].value[1:-1]
    name = value
    value = value.replace(r'\"', '"')\
                 .replace(r"\'", "'")\
                 .replace(r"\\", "\\")\
                 .replace(r"\n", "\n")\
                 .replace(r"\t", "\t")
    return TerminalStr(name, value)


def act_term_regex(_, nodes):
    value = nodes[0].value[1:-1]
    return TerminalRegEx(value, value)


def act_sequence(_, nodes):
    res = nodes[0]
    res.append(nodes[1])
    return res


def act_prod_rhss(_, nodes):
    res = nodes[0]
    res.append(nodes[2])
    return res


def act_production(_, nodes):
    symbol = NonTerminal(nodes[0])
    prods = []
    for p_rhs in nodes[2]:
        asoc = ASSOC_NONE
        prior = DEFAULT_PRIORITY
        if len(p_rhs) > 1:
            asoc = p_rhs[1]
        if len(p_rhs) > 2:
            prior = p_rhs[2]
        prods.append(Production(symbol, p_rhs[0], asoc, prior))

    return prods


def act_prodset(_, nodes):
    res = nodes[0]
    res.extend(nodes[1])
    return res


def act_assoc_prior(_, nodes):
    res = []
    res.extend(nodes[0])
    res.extend(nodes[2])
    return res


def act_production_rhs(_, nodes):
    assoc = ASSOC_NONE
    prior = DEFAULT_PRIORITY
    for ap in nodes[2]:
        if type(ap) is int:
            prior = ap
        else:
            if ap == 'left':
                assoc = ASSOC_LEFT
            elif ap == 'right':
                assoc = ASSOC_RIGHT
    return [ProductionRHS(nodes[0]), assoc, prior]


def act_grammar(_, nodes):
    prods = nodes[0]

    # Remove terminal production rules but first replace its
    # references.
    terms = {}
    to_del = []
    for idx, p in enumerate(prods):
        if len(p.rhs) == 1 and isinstance(p.rhs[0], Terminal):
            # Optimization: If a production has a single terminal RHS and there
            # is only one production for this grammar symbol then treat is as a
            # terminal.
            if len([x for x in prods if x.symbol == p.symbol]) == 1 and \
               p.symbol.name != 'LAYOUT':
                t = p.rhs[0]
                terms[p.symbol.name] = t
                t.name = p.symbol.name
                t.prior = p.prior
                if p.assoc != ASSOC_NONE:
                    raise GrammarError(
                        'Terminals should not define associativity '
                        '(terminal "{}").'.format(t.name))
                assert p.assoc == ASSOC_NONE
                to_del.append(idx)

    for idx in sorted(to_del, reverse=True):
        del prods[idx]

    # Change terminal references
    for p in prods:
        for idx, ref in enumerate(p.rhs):
            if ref.name in terms:
                p.rhs[idx] = terms[ref.name]
            elif ref.name == 'EMPTY':
                p.rhs[idx] = EMPTY
            elif ref.name == 'EOF':
                p.rhs[idx] = EOF

    return prods


pg_actions = {
    "Assoc:0": lambda _, nodes: nodes[0].value,
    "Assoc:1": lambda _, nodes: nodes[0].value,
    "AssocPrior:0": lambda _, nodes: [nodes[0]],
    "AssocPrior:1": lambda _, nodes: [nodes[0]],
    "AssocPrior:2": act_assoc_prior,
    "Prior": lambda _, value: int(value),
    "Term:0": act_term_str,
    "Term:1": act_term_regex,
    "Name": lambda _, value: value,
    "NonTermRef": lambda _, nodes: NonTerminal(nodes[0]),
    "GSymbol": lambda _, nodes: nodes[0],
    "Sequence:0": lambda _, nodes: [nodes[0]],
    "Sequence:1": act_sequence,
    "ProductionRHS:0": lambda _, nodes: [ProductionRHS(nodes[0])],
    "ProductionRHS:1": act_production_rhs,
    "ProductionRHSs:0": lambda _, nodes: [nodes[0]],
    "ProductionRHSs:1": act_prod_rhss,
    "Production": act_production,
    "ProductionSet:0": lambda _, nodes: nodes[0],
    "ProductionSet:1": act_prodset,
    "Grammar": act_grammar
}
