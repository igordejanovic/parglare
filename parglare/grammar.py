# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function
import sys
import re
from parglare.exceptions import GrammarError
from parglare.actions import pass_single, pass_nochange, collect, \
    collect_sep

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
    action(string): Common action given in the grammar.
    """
    def __init__(self, name):
        self.name = escape(name)
        self.action = None
        self._hash = hash(name)

    def __unicode__(self):
        return str(self)

    def __str__(self):
        return self.name

    def __repr__(self):
        return "{}({})".format(type(self).__name__, str(self))

    def __hash__(self):
        return self._hash

    def __eq__(self, other):
        return self.name == other.name

    def __ne__(self, other):
        return not self == other


class NonTerminal(GrammarSymbol):
    pass


class Terminal(GrammarSymbol):
    """Represent a terminal symbol of the grammar.

    Attributes:
    prior(int): Priority used for lexical disambiguation.
    dynamic(bool): Should dynamic disambiguation be called to resolve conflict
        involving this terminal.
    finish(bool): Used for optimization. If this terminal is `finish` no other
        recognizers will be checked if this succeeds.
    prefer(bool): Prefer this recognizer in case of multiple recognizers match
        at the same place and implicit disambiguation doesn't resolve.

    recognizer(callable): Called with input list of objects and position in the
        stream. Should return a sublist of recognized objects. The sublist
        should be rooted at the given position.
    """
    def __init__(self, name, recognizer=None):
        self.prior = DEFAULT_PRIORITY
        self.recognizer = recognizer if recognizer else StringRecognizer(name)
        self.finish = False
        self.prefer = False
        self.dynamic = False
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
    dynamic (bool): Is dynamic disambiguation used for this production.
    prod_id (int): Ordinal number of the production.
    prod_symbol_id (int): A zero-based ordinal of alternative choice for this
        production grammar symbol.
    """

    def __init__(self, symbol, rhs, assoc=ASSOC_NONE, prior=DEFAULT_PRIORITY,
                 dynamic=False):
        """
        Args:
        symbol (GrammarSymbol): A grammar symbol on the LHS of the production.
        rhs (list of GrammarSymbols):
        """
        self.symbol = symbol
        self.rhs = rhs if rhs else ProductionRHS()
        self.assoc = assoc
        self.prior = prior
        self.dynamic = dynamic

    def __str__(self):
        if hasattr(self, 'prod_id'):
            return "%d: %s = %s" % (self.prod_id, self.symbol, self.rhs)
        else:
            return "%s = %s" % (self.symbol, self.rhs)

    def __repr__(self):
        return 'Production({})'.format(str(self.symbol))


class ProductionRHS(list):
    def __getitem__(self, idx):
        try:
            while True:
                symbol = super(ProductionRHS, self).__getitem__(idx)
                if symbol is not EMPTY:
                    break
                idx += 1
            return symbol
        except IndexError:
            return None

    def __len__(self):
        return super(ProductionRHS, self).__len__() - self.count(EMPTY)

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

        self._collect_grammar_symbols()

        # Add special terminals
        self._by_name['EMPTY'] = EMPTY
        self._by_name['EOF'] = EOF
        self._by_name['STOP'] = STOP
        self.terminals.update([EMPTY, EOF, STOP])

        # Connect recognizers
        for term in self.terminals:
            if term.recognizer is None:
                if not self.recognizers:
                    raise GrammarError(
                        'Terminal "{}" has no recognizer defined '
                        'and no recognizers are given during parser '
                        'construction.'.format(term.name))
                if term.name not in self.recognizers:
                    raise GrammarError(
                        'Terminal "{}" has no recognizer defined.'
                        .format(term.name))
                term.recognizer = self.recognizers[term.name]

        self._resolve_references()

        # At the end remove terminal productions as those are not the real
        # productions, but just a symbolic names for terminals.
        self.productions[:] = [p for p in self.productions
                               if isinstance(p.symbol, NonTerminal)]

        self._enumerate_productions()

    def _collect_grammar_symbols(self):
        """
        Collect all terminal and non-terminal symbols from LHS of productions.
        """
        self._by_name = {}
        self._term_to_lhs = {}
        for p in self.productions:
            new_symbol = p.symbol
            if isinstance(new_symbol, Terminal):
                prev_symbol = self._by_name.get(new_symbol.name)
                if prev_symbol:
                    if isinstance(prev_symbol, Terminal):
                        # Multiple definitions of Terminals. Consider it a
                        # non-terminal with alternative terminals.
                        new_symbol = NonTerminal(new_symbol.name)
                    else:
                        new_symbol = prev_symbol

                if isinstance(new_symbol, Terminal):
                    if p.rhs:
                        self._term_to_lhs[p.rhs[0].name] = new_symbol
                    else:
                        self._term_to_lhs[new_symbol.name] = new_symbol
                else:
                    for k, v in self._term_to_lhs.items():
                        if v.name == new_symbol.name:
                            del self._term_to_lhs[k]
                            break

            # Get/check grammar actions for rules/symbols.
            if new_symbol.action and new_symbol.action != p.symbol.action:
                raise GrammarError(
                    'Multiple different grammar actions for rule "{}".'
                    .format(new_symbol.name))
            elif p.symbol.action:
                new_symbol.action = p.symbol.action

            self._by_name[new_symbol.name] = new_symbol

        self.terminals = set([x for x in self._by_name.values()
                              if isinstance(x, Terminal)])
        self.nonterminals = set([x for x in self._by_name.values()
                                 if isinstance(x, NonTerminal)])

    def _resolve_references(self):
        """
        Resolve all references and unify objects so that we have single
        instances of each terminal and non-terminal in the grammar.
        Create Terminal for user supplied Recognizer.
        """

        for idx, p in enumerate(self.productions):
            if p.symbol.name in self._by_name:
                p.symbol = self._by_name[p.symbol.name]
            for idx_ref, ref in enumerate(p.rhs):
                ref_sym = None
                if ref.name in self._by_name:
                    ref_sym = self._by_name[ref.name]
                else:
                    if isinstance(ref, Terminal):
                        # Register terminal by name
                        ref_sym = ref
                        self._by_name[ref.name] = ref_sym

                        # If terminal is registered by str recognizer and is
                        # referenced in a RHS of some other production report
                        # error.
                        if not isinstance(p.symbol, Terminal):
                            term_by_rec = self._term_to_lhs.get(ref.name)
                            if term_by_rec:
                                raise GrammarError(
                                    "Terminal '{}' used in production '{}' "
                                    "already exists by the name '{}'.".format(
                                        text(ref.name), text(p.symbol),
                                        text(term_by_rec)))
                        self.terminals.add(ref_sym)

                    else:
                        # Element of RHS must be either a Terminal, a
                        # NonTerminal or a Reference.
                        assert isinstance(ref, NonTerminal) \
                            or isinstance(ref, Reference)

                if not ref_sym:
                    raise GrammarError(
                        "Unknown symbol '{}' referenced from production '{}'.".
                        format(ref.name, text(p)))

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
    def from_string(grammar_str, recognizers=None, debug=False,
                    parse_debug=False):
        g = Grammar(get_grammar_parser(parse_debug).parse(grammar_str),
                    recognizers=recognizers)
        if debug:
            g.print_debug()
        return g

    @staticmethod
    def from_file(file_name, recognizers=None, debug=False, parse_debug=False):
        g = Grammar(get_grammar_parser(parse_debug).parse_file(file_name),
                    recognizers=recognizers)
        if debug:
            g.print_debug()
        return g

    def print_debug(self):
        print("\n\n*** GRAMMAR ***")
        print("Terminals:")
        print(" ".join([text(t) for t in self.terminals]))
        print("NonTerminals:")
        print(" ".join([text(n) for n in self.nonterminals]))

        print("Productions:")
        for p in self.productions:
            print(p)


# Grammar for grammars

(GRAMMAR,
 RULES,
 RULE,
 PRODUCTION_RULE,
 PRODUCTION_RULE_RHS,
 PRODUCTION,
 TERMINAL_RULE,
 PROD_DIS_RULE,
 PROD_DIS_RULES,
 TERM_DIS_RULE,
 TERM_DIS_RULES,
 GSYMBOL,
 GSYMBOLS,
 RECOGNIZER,
 LAYOUT,
 LAYOUT_ITEM,
 COMMENT,
 CORNC,
 CORNCS) = [NonTerminal(name) for name in [
     'Grammar',
     'Rules',
     'Rule',
     'ProductionRule',
     'ProductionRuleRHS',
     'Production',
     'TerminalRule',
     'ProductionDisambiguationRule',
     'ProductionDisambiguationRules',
     'TerminalDisambiguationRule',
     'TerminalDisambiguationRules',
     'GrammarSymbol',
     'GrammarSymbols',
     'Recognizer',
     'LAYOUT',
     'LAYOUT_ITEM',
     'Comment',
     'CORNC',
     'CORNCS']]

(NAME,
 STR_TERM,
 REGEX_TERM,
 PRIOR,
 ACTION,
 WS,
 COMMENTLINE,
 NOTCOMMENT) = [Terminal(name, RegExRecognizer(regex)) for name, regex in
                [
                    ('Name', r'[a-zA-Z0-9_]+'),
                    ('StrTerm', r'''(?s)('[^'\\]*(?:\\.[^'\\]*)*')|'''
                     r'''("[^"\\]*(?:\\.[^"\\]*)*")'''),
                    ('RegExTerm', r'''\/((\\/)|[^/])*\/'''),
                    ('Prior', r'\d+'),
                    ('Action', r'@[a-zA-Z0-9_]+'),
                    ('WS', r'\s+'),
                    ('CommentLine', r'\/\/.*'),
                    ('NotComment', r'((\*[^\/])|[^\s*\/]|\/[^\*])+'),
                ]]

pg_productions = [
    [GRAMMAR, [RULES, EOF]],
    [RULES, [RULES, RULE]],
    [RULES, [RULE]],
    [RULE, [PRODUCTION_RULE]],
    [RULE, [ACTION, PRODUCTION_RULE]],
    [RULE, [TERMINAL_RULE]],
    [RULE, [ACTION, TERMINAL_RULE]],

    [PRODUCTION_RULE, [NAME, ':', PRODUCTION_RULE_RHS, ';']],
    [PRODUCTION_RULE_RHS, [PRODUCTION_RULE_RHS, '|', PRODUCTION],
     ASSOC_LEFT, 5],
    [PRODUCTION_RULE_RHS, [PRODUCTION], ASSOC_LEFT, 5],
    [PRODUCTION, [GSYMBOLS]],
    [PRODUCTION, [GSYMBOLS, '{', PROD_DIS_RULES, '}']],

    [TERMINAL_RULE, [NAME, ':', RECOGNIZER, ';'], ASSOC_LEFT, 15],
    [TERMINAL_RULE, [NAME, ':', ';'], ASSOC_LEFT, 15],
    [TERMINAL_RULE, [NAME, ':', RECOGNIZER, '{', TERM_DIS_RULES, '}', ';'],
     ASSOC_LEFT, 15],
    [TERMINAL_RULE, [NAME, ':', '{', TERM_DIS_RULES, '}', ';'],
     ASSOC_LEFT, 15],

    [PROD_DIS_RULE, ['left']],
    [PROD_DIS_RULE, ['right']],
    [PROD_DIS_RULE, ['dynamic']],
    [PROD_DIS_RULE, [PRIOR]],
    [PROD_DIS_RULES, [PROD_DIS_RULES, ',', PROD_DIS_RULE], ASSOC_LEFT],
    [PROD_DIS_RULES, [PROD_DIS_RULE]],

    [TERM_DIS_RULE, ['prefer']],
    [TERM_DIS_RULE, ['finish']],
    [TERM_DIS_RULE, ['dynamic']],
    [TERM_DIS_RULE, [PRIOR]],
    [TERM_DIS_RULES, [TERM_DIS_RULES, ',', TERM_DIS_RULE]],
    [TERM_DIS_RULES, [TERM_DIS_RULE]],

    [GSYMBOL, [NAME]],
    [GSYMBOL, [RECOGNIZER]],
    [GSYMBOLS, [GSYMBOLS, GSYMBOL]],
    [GSYMBOLS, [GSYMBOL]],
    [RECOGNIZER, [STR_TERM]],
    [RECOGNIZER, [REGEX_TERM]],

    # Support for comments,
    [LAYOUT, [LAYOUT_ITEM]],
    [LAYOUT, [LAYOUT, LAYOUT_ITEM]],
    [LAYOUT_ITEM, [WS]],
    [LAYOUT_ITEM, [COMMENT]],
    [LAYOUT_ITEM, [EMPTY]],
    [COMMENT, ['/*', CORNCS, '*/']],
    [COMMENT, [COMMENTLINE]],
    [CORNCS, [CORNC]],
    [CORNCS, [CORNCS, CORNC]],
    [CORNCS, [EMPTY]],
    [CORNC, [COMMENT]],
    [CORNC, [NOTCOMMENT]],
    [CORNC, [WS]]
]


grammar_parser = None


def get_grammar_parser(debug):
    global grammar_parser
    if not grammar_parser:
        from parglare import Parser
        grammar_parser = Parser(Grammar.from_struct(pg_productions, GRAMMAR),
                                actions=pg_actions, debug=debug)
    return grammar_parser


def act_rules(_, nodes):
    e1, e2 = nodes
    e1.extend(e2)
    return e1


def act_rule_with_action(_, nodes):
    action, productions = nodes

    # Strip @ char
    action = action[1:]

    productions[0].symbol.action = action
    return productions


def act_production_rule(_, nodes):
    name, _, rhs_prods, __ = nodes

    symbol = NonTerminal(name)

    # Collect all productions for this rule
    prods = []
    for prod in rhs_prods:
        gsymbols, disrules = prod
        assoc = disrules.get('assoc', ASSOC_NONE)
        prior = disrules.get('priority', DEFAULT_PRIORITY)
        dynamic = disrules.get('dynamic', False)
        prods.append(Production(symbol,
                                ProductionRHS(gsymbols),
                                assoc=assoc,
                                prior=prior,
                                dynamic=dynamic))

    return prods


def act_production(_, nodes):
    gsymbols = nodes[0]
    disrules = {}
    if len(nodes) > 1:
        rules = nodes[2]
        for rule in rules:
            if rule == 'left':
                disrules['assoc'] = ASSOC_LEFT
            elif rule == 'right':
                disrules['assoc'] = ASSOC_RIGHT
            elif rule == 'dynamic':
                disrules['dynamic'] = True
            elif type(rule) is int:
                disrules['priority'] = rule

    return (gsymbols, disrules)


def act_term_rule(_, nodes):

    name = nodes[0]
    rhs_term = nodes[2]

    term = Terminal(name, rhs_term.recognizer)
    if len(nodes) > 4:
        for t in nodes[4]:
            if type(t) is int:
                term.prior = t
            elif t == 'finish':
                term.finish = True
            elif t == 'prefer':
                term.prefer = True
            elif t == 'dynamic':
                term.dynamic = True
            else:
                print(t)
                assert False
    return [Production(term, ProductionRHS([rhs_term]))]


def act_term_rule_empty_body(_, nodes):
    name = nodes[0]

    term = Terminal(name)
    term.recognizer = None
    if len(nodes) > 3:
        for t in nodes[3]:
            if type(t) is int:
                term.prior = t
            elif t == 'finish':
                term.finish = True
            elif t == 'prefer':
                term.prefer = True
            elif t == 'dynamic':
                term.dynamic = True
            else:
                print(t)
                assert False
    return [Production(term, ProductionRHS([]))]


def act_recognizer_str(_, nodes):
    value = nodes[0].value[1:-1]
    value = value.replace(r'\"', '"')\
                 .replace(r"\'", "'")\
                 .replace(r"\\", "\\")\
                 .replace(r"\n", "\n")\
                 .replace(r"\t", "\t")
    return Terminal(value, StringRecognizer(value))


def act_recognizer_regex(_, nodes):
    value = nodes[0].value[1:-1]
    return Terminal(value, RegExRecognizer(value))


pg_actions = {
    "Grammar": pass_single,
    "Rules": [act_rules, pass_single],
    "Action": pass_nochange,
    "Rule": [pass_single,
             act_rule_with_action,
             pass_single,
             act_rule_with_action],

    "ProductionRule": act_production_rule,
    "ProductionRuleRHS": collect_sep,
    "Production": act_production,

    "TerminalRule": [act_term_rule,
                     act_term_rule_empty_body,
                     act_term_rule,
                     act_term_rule_empty_body],

    "ProductionDisambiguationRule": pass_single,
    "ProductionDisambiguationRules": collect_sep,

    "TerminalDisambiguationRule": pass_single,
    "TerminalDisambiguationRules": collect_sep,

    "GrammarSymbols": collect,
    "GrammarSymbol": [lambda _, nodes: Reference(nodes[0]),
                      pass_single],

    "Recognizer": [act_recognizer_str, act_recognizer_regex],

    # Terminals
    "Name": pass_nochange,
    "Prior": lambda _, value: int(value),
    "left": pass_nochange,
    "right": pass_nochange,
    "dynamic": pass_nochange,
    "prefer": pass_nochange,
    "finish": pass_nochange

}
