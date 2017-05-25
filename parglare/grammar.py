# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function
import sys
import re
from parglare.exceptions import GrammarError
from parglare.actions import pass_single, pass_value, pass_nochange, \
    collect, collect_sep

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
    """
    Represents an abstract grammar symbol.

    Attributes:
    name(str): The name of this grammar symbol.
    """
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
    """Represent a terminal symbol of the grammar.

    Attributes:
    prior(int): Priority used for lexical disambiguation.

    recognizer(callable): Called with input list of objects and position in the
        stream. Should return a sublist of recognized objects. The sublist
        should be rooted at the given position.
    """
    def __init__(self, name, recognizer=None):
        self.prior = DEFAULT_PRIORITY
        self.recognizer = recognizer if recognizer else StringRecognizer(name)
        super(Terminal, self).__init__(name)


class Reference(object):
    """
    A name reference to a GrammarSymbol used for cross-resolving during
    grammar construction.
    """
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return self.name


class Recognizer(object):
    """
    Recognizers are callables capable of recognizing low-level patterns
    (a.k.a tokens) in the input.
    """
    def __init__(self, name):
        self.name = name


class StringRecognizer(Recognizer):
    def __init__(self, value):
        super(StringRecognizer, self).__init__(value)
        self.value = value

    def __call__(self, in_str, pos):
        if in_str[pos:pos+len(self.value)] == self.value:
            return self.value


class RegExRecognizer(Recognizer):
    def __init__(self, regex):
        super(RegExRecognizer, self).__init__(regex)
        self._regex = regex
        self.regex = re.compile(self._regex)

    def __call__(self, in_str, pos):
        m = self.regex.match(in_str, pos)
        if m:
            matched = m.group()
            return matched


def EMPTY_recognizer(input, pos):
    pass


def EOF_recognizer(input, pos):
    pass


def STOP_recognizer(input, pos):
    pass


# These two terminals are special terminals used internally.
AUGSYMBOL = NonTerminal("S'")
STOP = Terminal("STOP", STOP_recognizer)

# These two terminals are special terminals used in the grammars.
# EMPTY will match nothing and always succeed.
# EOF will match only at the end of the input string.
EMPTY = Terminal("EMPTY", EMPTY_recognizer)
EOF = Terminal("EOF", EOF_recognizer)


class Production(object):
    """Represent production from the grammar.

    Attributes:
    symbol (GrammarSymbol):
    rhs (ProductionRHS):
    assoc (int): Associativity. Used for ambiguity (shift/reduce) resolution.
    prior (int): Priority. Used for ambiguity (shift/reduce) resolution.
    prod_id (int): Ordinal number of the production.
    prod_symbol_id (int): A zero-based ordinal of alternative choice for this
        production grammar symbol.
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

    def __repr__(self):
        return "<ProductionRHS([{}])>".format(
            ", ".join([str(x) for x in self]))


class Grammar(object):
    """
    Grammar is a collection of production rules.
    First production is reserved for the augmented production (S' -> S).

    Attributes:
    productions (list of Production):
    root_symbol (GrammarSymbol): start/root symbol of the grammar.
    recognizers (dict of callables): A set of Python callables used as a
        terminal recognizers not specified in the grammar.
    nonterminals (set of NonTerminal):
    terminals(set of Terminal):

    """

    def __init__(self, productions, root_symbol=None, recognizers=None):
        self.productions = productions
        self.root_symbol = \
            root_symbol if root_symbol else productions[0].symbol
        self.recognizers = recognizers if recognizers else {}

        self._init_grammar()

    def _init_grammar(self):
        """
        Extracts all grammar symbol (nonterminal and terminal) from the
        grammar, resolves and check references in productions, unify all
        grammar symbol objects and enumerate production.
        """
        self.nonterminals = set()
        self.terminals = set()

        # Reserve 0 production. It is used for augmented prod. in LR
        # automata calculation.
        self.productions.insert(
            0,
            Production(AUGSYMBOL, ProductionRHS([self.root_symbol, STOP])))

        by_name = self._collect_grammar_symbols()

        # Add special terminals
        by_name['EMPTY'] = EMPTY
        by_name['EOF'] = EOF
        by_name['STOP'] = STOP
        self.terminals.update([EMPTY, EOF, STOP])

        self._resolve_references(by_name)

        # At the end remove terminal productions as those are not the real
        # productions, but just a symbolic names for terminals.
        self.productions[:] = [p for p in self.productions
                               if isinstance(p.symbol, NonTerminal)]

        self._enumerate_productions()

    def _collect_grammar_symbols(self):
        """
        Collect all terminal and non-terminal symbols.
        """
        by_name = {}
        for p in self.productions:
            if isinstance(p.symbol, NonTerminal):
                self.nonterminals.add(p.symbol)
            else:
                # Multiple definitions of Terminals
                if p.symbol.name in by_name \
                   and isinstance(by_name[p.symbol.name], Terminal):
                    # If a terminal is defined multiple times assume it to
                    # be a nonterminal with alternative terminals.
                    self.terminals.remove(p.symbol)
                    nt = NonTerminal(p.symbol.name)
                    for i in self.productions:
                        if i.symbol.name == p.symbol.name:
                            i.symbol = nt
                    self.nonterminals.add(nt)
                else:
                    self.terminals.add(p.symbol)

            by_name[p.symbol.name] = p.symbol

        return by_name

    def _resolve_references(self, by_name):
        """
        Resolve all references and unify objects so that we have single
        instances of each terminal and non-terminal in the grammar.
        Create Terminal for Recognizer instance or a reference to user
        supplied Recognizer.
        """

        for idx, p in enumerate(self.productions):
            for idx_ref, ref in enumerate(p.rhs):
                if isinstance(ref, Recognizer):
                    # If terminal with the same "name" is registered use it.
                    # If not, create new.
                    if ref.name in by_name:
                        ref_sym = by_name[ref.name]
                    ref_sym = Terminal(ref.name, ref)
                    by_name[ref.name] = ref_sym
                    self.terminals.add(ref_sym)

                else:
                    # Element of RHS must be either a Terminal, a NonTerminal
                    # or a Reference. Replace it by the collected LHS elements
                    # just to be sure that we have a single instance of each in
                    # the grammar.
                    assert isinstance(ref, Terminal) \
                        or isinstance(ref, NonTerminal) \
                        or isinstance(ref, Reference)
                    if ref.name not in by_name:
                        # Terminals might only be on the RHS for grammars
                        # constructed from data structure. All non-terminals
                        # must already be registered in `by_name` as they must
                        # be found as LHS of some of the productions.
                        if isinstance(ref, Terminal):
                            by_name[ref.name] = ref
                            self.terminals.add(ref)
                        elif isinstance(ref, Reference):
                            # The last option is that the reference is a name
                            # of user supplied Recognizer. If so create a
                            # terminal for it.
                            if ref.name in self.recognizers:
                                ref_sym = Terminal(ref.name,
                                                   self.recognizers[ref.name])
                                by_name[ref.name] = ref_sym
                                self.terminals.add(ref_sym)

                    if ref.name not in by_name:
                        raise GrammarError(
                            "Unknown symbol '{}' "
                            "referenced from production '{}'.".
                            format(ref.name, text(p)))

                    ref_sym = by_name[ref.name]

                p.rhs[idx_ref] = ref_sym

    def _enumerate_productions(self):
        """
        Enumerates all productions (prod_id) and production per symbol
        (prod_symbol_id).
        """
        idx_per_symbol = {}
        for idx, s in enumerate(self.productions):
            s.prod_id = idx
            s.prod_symbol_id = idx_per_symbol.get(s.symbol, 0)
            idx_per_symbol[s.symbol] = idx_per_symbol.get(s.symbol, 0) + 1

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

    def get_production_id(self, name):
        "Returns first production id for the given symbol name"
        for p in self.productions:
            if p.symbol.name == name:
                return p.prod_id

    @staticmethod
    def _create_productions(productions, start_symbol=None):
        """Creates Production instances from the list of productions given in
        the form:
        [LHS, RHS, optional ASSOC, optional PRIOR].
        Where LHS is grammar symbol and RHS is a list or tuple of grammar
        symbols from the right-hand side of the production.
        """
        gp = []
        for p in productions:
            assoc = ASSOC_NONE
            prior = DEFAULT_PRIORITY
            symbol = p[0]
            if not isinstance(symbol, NonTerminal):
                raise GrammarError("Invalid production symbol '{}' "
                                   "for production '{}'".format(symbol,
                                                                text(p)))
            rhs = ProductionRHS(p[1])
            if len(p) > 2:
                assoc = p[2]
            if len(p) > 3:
                prior = p[3]

            # Convert strings to Terminals with string recognizers
            for idx, t in enumerate(rhs):
                if isinstance(t, text):
                    rhs[idx] = Terminal(t)

            gp.append(Production(symbol, rhs, assoc, prior))

        return gp

    @staticmethod
    def from_struct(productions, start_symbol, recognizers=None):
        return Grammar(Grammar._create_productions(productions, start_symbol),
                       start_symbol, recognizers=recognizers)

    @staticmethod
    def from_string(grammar_str, recognizers=None, debug=False):
        return Grammar(get_grammar_parser(debug).parse(grammar_str),
                       recognizers=recognizers)

    @staticmethod
    def from_file(file_name, recognizers=None, debug=False):
        return Grammar(get_grammar_parser(debug).parse_file(file_name),
                       recognizers=recognizers)

    def print_debug(self):
        print("Terminals:")
        print(" ".join([text(t) for t in self.terminals]))
        print("NonTerminals:")
        print(" ".join([text(n) for n in self.nonterminals]))

        print("Productions:")
        for p in self.productions:
            print(p)


# Grammar for grammars

(GRAMMAR,
 PRODUCTION_SET,
 PRODUCTION,
 TERM_PRODUCTION,
 PRODUCTION_RHSS,
 PRODUCTION_RHS,
 GSYMBOL,
 NONTERM_REF,
 RECOGNIZER,
 ASSOC,
 ASSOC_PRIOR,
 SEQUENCE,
 LAYOUT,
 LAYOUT_ITEM) = [NonTerminal(name) for name in [
     'Grammar',
     'ProductionSet',
     'Production',
     'TermProduction',
     'ProductionRHSs',
     'ProductionRHS',
     'GSymbol',
     'NonTermRef',
     'Recognizer',
     'Assoc',
     'AssocPrior',
     'Sequence',
     'LAYOUT',
     'LAYOUT_ITEM']]

(NAME,
 STR_TERM,
 REGEX_TERM,
 PRIOR,
 WS,
 COMMENT) = [Terminal(name, RegExRecognizer(regex)) for name, regex in
             [
               ('Name', r'[a-zA-Z0-9_]+'),
               ('StrTerm', r'''(?s)('[^'\\]*(?:\\.[^'\\]*)*')|'''
                           r'''("[^"\\]*(?:\\.[^"\\]*)*")'''),
               ('RegExTerm', r'''\/((\\/)|[^/])*\/'''),
               ('Prior', r'\d+'),
               ('WS', r'\s+'),
               ('Comment', r'\/\/.*'),
             ]]

pg_productions = [
    [GRAMMAR, [PRODUCTION_SET, EOF]],
    [PRODUCTION_SET, [PRODUCTION_SET, PRODUCTION]],
    [PRODUCTION_SET, [PRODUCTION_SET, TERM_PRODUCTION]],
    [PRODUCTION_SET, [PRODUCTION]],
    [PRODUCTION_SET, [TERM_PRODUCTION]],
    [PRODUCTION, [NAME, '=', PRODUCTION_RHSS, ';']],
    [TERM_PRODUCTION, [NAME, '=', RECOGNIZER, ';'], ASSOC_LEFT, 15],
    [TERM_PRODUCTION, [NAME, '=', RECOGNIZER, '{', PRIOR, '}', ';'],
     ASSOC_LEFT, 15],
    [PRODUCTION_RHS, [SEQUENCE]],
    [PRODUCTION_RHS, [SEQUENCE, '{', ASSOC_PRIOR, '}']],
    [PRODUCTION_RHSS, [PRODUCTION_RHSS, '|', PRODUCTION_RHS], ASSOC_LEFT, 5],
    [PRODUCTION_RHSS, [PRODUCTION_RHS], ASSOC_LEFT, 5],
    [ASSOC_PRIOR, [ASSOC]],
    [ASSOC_PRIOR, [PRIOR]],
    [ASSOC_PRIOR, [ASSOC_PRIOR, ',', ASSOC_PRIOR], ASSOC_LEFT],
    [ASSOC, ['left']],
    [ASSOC, ['right']],
    [SEQUENCE, [SEQUENCE, GSYMBOL]],
    [SEQUENCE, [GSYMBOL]],
    [GSYMBOL, [NAME]],
    [GSYMBOL, [RECOGNIZER]],
    [RECOGNIZER, [STR_TERM]],
    [RECOGNIZER, [REGEX_TERM]],

    # Support for comments,
    [LAYOUT, [LAYOUT_ITEM]],
    [LAYOUT, [LAYOUT, LAYOUT_ITEM]],
    [LAYOUT_ITEM, [WS]],
    [LAYOUT_ITEM, [COMMENT]],
    [LAYOUT_ITEM, [EMPTY]],
]


grammar_parser = None


def get_grammar_parser(debug):
    global grammar_parser
    if not grammar_parser:
        from parglare import Parser
        grammar_parser = Parser(Grammar.from_struct(pg_productions, GRAMMAR),
                                actions=pg_actions, debug=debug)
    return grammar_parser


def act_recognizer_str(_, nodes):
    value = nodes[0].value[1:-1]
    value = value.replace(r'\"', '"')\
                 .replace(r"\'", "'")\
                 .replace(r"\\", "\\")\
                 .replace(r"\n", "\n")\
                 .replace(r"\t", "\t")
    return StringRecognizer(value)


def act_recognizer_regex(_, nodes):
    value = nodes[0].value[1:-1]
    return RegExRecognizer(value)


def act_production(_, nodes):

    symbol = NonTerminal(nodes[0])

    # Collect all productions for this non-terminal
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


def act_term_production(_, nodes):

    term = Terminal(nodes[0], nodes[2])
    if len(nodes) > 4:
        term.prior = nodes[4]
    return [Production(term, ProductionRHS([term]), prior=term.prior)]


def act_assoc_prior(_, nodes):
    res = []
    res.extend(nodes[0])
    res.extend(nodes[2])
    return res


def act_production_rhs_simple(_, nodes):
    return (ProductionRHS(nodes[0]),)


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
    return (ProductionRHS(nodes[0]), assoc, prior)


def act_production_set(_, nodes):
    e1, e2 = nodes
    e1.extend(e2)
    return e1


pg_actions = {
    "Assoc": pass_value,
    "AssocPrior": [pass_nochange, pass_nochange, act_assoc_prior],
    "Prior": lambda _, value: int(value),
    "Recognizer": [act_recognizer_str, act_recognizer_regex],
    "Name": pass_nochange,
    "GSymbol": [lambda _, nodes: Reference(nodes[0]),
                pass_single],
    "Sequence": collect,
    "ProductionRHS": [act_production_rhs_simple,
                      act_production_rhs,
                      act_production_rhs_simple,
                      act_production_rhs],
    "ProductionRHSs": collect_sep,
    "Production": act_production,
    "TermProduction": act_term_production,
    "ProductionSet": [act_production_set, act_production_set,
                      pass_single, pass_single],
    "Grammar": pass_single
}
