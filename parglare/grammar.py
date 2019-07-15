# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function
from os import path
import sys
import re
import itertools
from parglare.six import add_metaclass
from parglare.exceptions import GrammarError
from parglare.recognizers import (StringRecognizer, RegExRecognizer,
                                  STOP_recognizer, EOF_recognizer,
                                  EMPTY_recognizer)
from parglare.common import Location
from parglare.termui import prints, s_emph, s_header, a_print, h_print

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

# Multiplicity
MULT_ONE = '1'
MULT_OPTIONAL = '?'
MULT_ONE_OR_MORE = '+'
MULT_ZERO_OR_MORE = '*'

RESERVED_SYMBOL_NAMES = ['EOF', 'STOP', 'EMPTY']
SPECIAL_SYMBOL_NAMES = ['KEYWORD', 'LAYOUT']

MODIFIERS = ['left', 'right', 'shift', 'reduce', 'dynamic', 'ps', 'nops',
             'pse', 'nopse', 'greedy', 'nogreedy', 'finish', 'nofinish',
             'prefer']

THIS_LOCATION = Location(file_name=__file__)


def escape(instr):
    return instr.replace('\n', r'\n').replace('\t', r'\t')


class Locatable(object):
    """
    Represents a base class for all classes whose instances could have a
    location of definition.

    :param location: The location where the object is defined.
    :type location: :class:`Location`
    """
    def __init__(self, location=None, **kwargs):
        self.location = location
        super(Locatable, self).__init__(**kwargs)


class GrammarSymbol(Locatable):
    """
    Represents an abstract grammar symbol.

    :param name: The name of this grammar symbol.

    :param int prior: Priority used for disambiguation.
    :param bool dynamic: Should dynamic disambiguation be called to resolve
        conflict involving this symbol.
    :param dict meta: User meta-data.
    """
    def __init__(self, name, prior=DEFAULT_PRIORITY, dynamic=False, meta=None,
                 **kwargs):
        super(GrammarSymbol, self).__init__(**kwargs)
        self.name = escape(name)
        self.prior = prior
        self.dynamic = dynamic
        self.meta = meta
        self._hash = hash(self.name)

    def add_meta_data(self, name, value):
        if self.meta is None:
            self.meta = {}
        self.meta[name] = value

    def __getattr__(self, name):
        if self.meta is not None:
            attr = self.meta.get(name)
            if attr:
                return attr
        raise AttributeError

    def __unicode__(self):
        return str(self)

    def __str__(self):
        return self.name

    def __repr__(self):
        return "{}({})".format(type(self).__name__, str(self))

    def __hash__(self):
        return self._hash


class NonTerminal(GrammarSymbol):
    """
    Represents a non-termial symbol of the grammar.

    :param list productions: A list of alternative productions for this
        NonTerminal.
    :param assoc: Associativity for disambiguation
    :param bool ps: "prefer shift" strategy for this non-terminal.
    :param bool pse: "prefer shift over empty" strategy for this non-terminal.
    """
    def __init__(self, name, productions=None, assoc=ASSOC_NONE, ps=False,
                 pse=False, **kwargs):
        super(NonTerminal, self).__init__(name, **kwargs)
        self.productions = productions if productions is not None else []
        self.assoc = assoc
        self.ps = ps
        self.pse = pse


class Terminal(GrammarSymbol):
    """
    Represent a terminal symbol of the grammar.

    :param action: A name of common/user action given in the grammar.
    :param bool finish: Used for scanning optimization.  If this terminal is
        `finish` no other recognizers will be checked if this succeeds.  If not
        provided in the grammar implicit rules will be used during table
        construction.
    :param bool prefer: Prefer this recognizer in case of multiple recognizers
        match at the same place and implicit disambiguation doesn't resolve.
    :param bool keyword: `True` if this Terminal represents keyword.  `False`
        by default.
    :param callable recognizer: Called with input list of objects and position
        in the stream.  Should return a sublist of recognized objects.  The
        sublist should be rooted at the given position.
    """
    def __init__(self, name, recognizer=None, action=None, finish=None,
                 prefer=False, keyword=False, **kwargs):
        super(Terminal, self).__init__(name, **kwargs)
        self._recognizer = None
        self.recognizer = recognizer
        self.action = action
        self.finish = finish
        self.prefer = prefer
        self.keyword = keyword

    @property
    def recognizer(self):
        return self._recognizer

    @recognizer.setter
    def recognizer(self, value):
        self._recognizer = value


AUGSYMBOL_NAME = "S'"

# This terminal is a special terminal used internally.
STOP = Terminal("STOP", STOP_recognizer)

# These two terminals are special terminals used in the grammars.
# EMPTY will match nothing and always succeed.
# EOF will match only at the end of the input string.
EMPTY = Terminal("EMPTY", EMPTY_recognizer, action='pass_none')
EOF = Terminal("EOF", EOF_recognizer, action='pass_none')


class Production(Locatable):
    """
    Represent production from the grammar.

    :param GrammarSymbol symbol: A grammar symbol on the LHS of the production.
    :param ProductionRHS rhs:
    :param action: A name of common/user action given in the grammar.
    :param list assignments: A list of Assignment instances.
    :param int assoc: Associativity.  Used for ambiguity (shift/reduce)
        resolution.
    :param int prior: Priority.  Used for ambiguity (shift/reduce) resolution.
    :param bool dynamic: Is dynamic disambiguation used for this production.
    :param bool ps: `prefer_shifts` strategy for this production.  Only makes
        sense for GLR parser.  Default is `None` -- means use parser settings.
    :param bool pse: `prefer_shifts_over_empty` strategy for this production.
        Only makes sense for GLR parser.  Default is `None` -- means use parser
        settings.
    :param dict meta: User meta-data.
    :param int prod_id: Ordinal number of the production.
    :param int prod_symbol_id: A zero-based ordinal of alternative choice for
        this production grammar symbol.
    """

    def __init__(self, symbol, rhs, action=None, assignments=None,
                 assoc=ASSOC_NONE, prior=DEFAULT_PRIORITY, dynamic=False,
                 ps=None, pse=None, meta=None, **kwargs):
        super(Production, self).__init__(**kwargs)
        self.symbol = symbol
        self.rhs = rhs if rhs else ProductionRHS()
        self.action = action
        self.assignments = assignments
        self.assoc = assoc
        self.prior = prior
        self.dynamic = dynamic
        self.ps = ps
        self.pse = pse
        self.meta = meta

    def __str__(self):
        if hasattr(self, 'prod_id'):
            return (s_header("%d:") + " %s " + s_emph("=") +
                    " %s") % (self.prod_id, self.symbol, self.rhs)
        else:
            return ("%s " + s_emph("=") + " %s") % (self.symbol, self.rhs)

    def __repr__(self):
        return 'Production({})'.format(str(self.symbol))

    def __getattr__(self, name):
        if self.meta is not None:
            attr = self.meta.get(name)
            if attr:
                return attr
        raise AttributeError


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


class Assignment(object):
    """
    General assignment (`=` or `?=`, a.k.a. `named matches`) in productions.
    Used also for references as LHS and assignment operator are optional.
    """
    def __init__(self, name, op, symbol, mult=MULT_ONE, rhs_idx=None):
        """
        :param str name: The name on the LHS of assignment.
        :param str op: Either a `=` or `?=`.
        :param symbol: A grammar symbol on the RHS or the symbol name
        :type symbol: `GrammarSymbol` or `str`
        :param str mult: Multiplicity of the RHS reference (used for regex
            operators ?, *, +).  See MULT_* constants above.  By default
            multiplicity is MULT_ONE.
        :param int rhs_idx: Index in the production RHS
        """
        self.name = name
        self.op = op
        self.symbol = symbol
        self.mult = mult
        self.rhs_idx = rhs_idx


class PGAttribute(object):
    """
    PGAttribute definition created by named matches.

    :param str name: The name of the attribute.
    :param str mult: Multiplicity of the attribute.  See MULT_* constants.
    :param str type_name: The type name of the attribute value(s).  It is also
        the name of the referring grammar rule.
    """
    def __init__(self, name, mult, type_name):
        self.name = name
        self.mult = mult
        self.type_name = type_name


class Grammar(object):
    """
    Grammar is a collection of production rules, nonterminals and terminals.
    First production is reserved for the augmented production (S' -> S).

    :param grammar_struct: Python structure that represents the grammar to be
        built
    :param classes: A dict of user specific classes
    :param file_path: A file path where grammar was loaded from
    :param start_symbol: start/root symbol of the grammar or its name.
    :type start_symbol: :class:`GrammarSymbol` or str

    :param nonterminals: A dict of :class:`NonTerminal` keyed by name
    :param terminals: A dict of :class:`Terminal` keyed by name
    """

    # Cache for PG grammar and parser table
    pg_parser_grammar = None
    pg_parser_table = None

    def __init__(self, grammar_struct, classes=None, file_path=None,
                 start_symbol=None, ignore_case=False, re_flags=re.MULTILINE,
                 debug=False, debug_parse=False, debug_colors=False):
        self.classes = classes if classes else {}
        self.file_path = file_path
        self.ignore_case = ignore_case
        self.re_flags = re_flags
        self.terminals = {}
        self.nonterminals = {}
        self.productions = []

        if start_symbol is None:
            if 'start' not in grammar_struct:
                raise GrammarError(
                    location=THIS_LOCATION,
                    message='No start symbol provided for the grammar.')
            else:
                start_symbol = grammar_struct['start']

        # Augmented prod. in LR automata calculation.
        if AUGSYMBOL_NAME not in grammar_struct['rules']:
            grammar_struct['rules'][AUGSYMBOL_NAME] = {
                'productions': [
                    {'production': [start_symbol, 'STOP']}
                ]
            }
            grammar_struct['start'] = AUGSYMBOL_NAME

        self.grammar_struct = grammar_struct
        self._init_from_struct()
        self.AUGSYMBOL = self.get_nonterminal(AUGSYMBOL_NAME)

    def _init_from_struct(self):
        """
        Initialize this grammar from a grammar given in a form of a Python
        structure.
        """
        self._extend_assignment_definitions()
        self._desugar_struct_multiplicities()
        self._create_terminals()
        self._fix_keyword_terminals()
        self._create_productions()
        self._enumerate_productions()
        self._resolve()

        # At the end remove location objects to release unused memory
        self.remove_locations(self.grammar_struct)

    def _extend_assignment_definitions(self):
        """
        Extend assignment definition struct to include information about
        multiplicities and symbol names before multiplicities desugaring.
        """
        rules = self.grammar_struct['rules']
        for rule_name, rule_struct in list(rules.items()):
            for (prod_idx,
                 production_struct) in enumerate(rule_struct['productions']):
                rhs = production_struct['production']
                assignments_struct = production_struct.get('assignments', {})
                for assignment_struct in assignments_struct.values():
                    rhs_idx = assignment_struct['rhs_idx']
                    mult_struct = rhs[rhs_idx]
                    if 'mult' not in assignment_struct:
                        if type(mult_struct) is dict:
                            assignment_struct['mult'] = mult_struct['mult']
                        else:
                            assignment_struct['mult'] = MULT_ONE
                    if 'symbol' not in assignment_struct:
                        if type(mult_struct) is dict:
                            assignment_struct['symbol'] = \
                                mult_struct['symbol']
                        else:
                            assignment_struct['symbol'] = mult_struct

    def _desugar_struct_multiplicities(self):
        """
        Desugar grammar struct by creating additional multiplicities grammar
        symbols and reducing grammar struct to its canonical form.
        """
        rules = self.grammar_struct['rules']
        for rule_name, rule_struct in list(rules.items()):
            for (prod_idx,
                 production_struct) in enumerate(rule_struct['productions']):
                rhs = production_struct['production']
                for ref_idx, ref in enumerate(rhs):
                    if type(ref) is dict:
                        if 'symbol' not in ref:
                            raise GrammarError(
                                location=self._get_location(production_struct),
                                message='"symbol" key must be given in '
                                'reference in rule "{}".'.format(rule_name))
                        self._degugar_multiplicity_ref(ref, production_struct)
                        if len(ref) == 1:
                            # If we are reduced a reference only on symbol name
                            # replace with just a simple string
                            rhs[ref_idx] = ref['symbol']  # noqa

    def _degugar_multiplicity_ref(self, ref, production_struct):
        """
        Desugar complex suggared reference containing multiplicity and
        separator definition to a canonical form of a reference.  Create
        necessary rules for repetitions (one or more, zero or more, optional).
        """
        symbol = ref['symbol']
        multiplicity = ref.get('mult', None)

        if not multiplicity:
            return

        separator = None
        modifiers = ref.get('modifiers', [])
        if modifiers:
            del ref['modifiers']
        for idx, modifier in enumerate(modifiers):
            if modifier not in MODIFIERS:
                if separator:
                    raise GrammarError(
                        location=self._get_location(production_struct),
                        message='Multiple separators in reference "{}".'
                        .format(ref))
                separator = modifier
                del modifiers[idx]

        symbol_mult = self._make_multiplicity_name(symbol, multiplicity,
                                                   separator, modifiers)
        ref['symbol'] = symbol_mult
        del ref['mult']

        rules = self.grammar_struct['rules']
        if symbol_mult in rules:
            return

        if multiplicity in [MULT_ONE_OR_MORE, MULT_ZERO_OR_MORE]:
            # noqa See: http://www.igordejanovic.net/parglare/grammar_language/#one-or-more_1
            symbol_one = self._make_multiplicity_name(symbol, MULT_ONE_OR_MORE,
                                                      separator, modifiers)
            if symbol_one not in rules:
                productions = []
                if separator:
                    p = {'production': [symbol_one, separator, symbol]}
                else:
                    p = {'production': [symbol_one, symbol]}

                if modifiers:
                    p['modifiers'] = modifiers
                productions.append(p)
                productions.append(
                        {'production': [symbol]}
                )

                rules[symbol_one] = {
                    'action': 'collect_sep' if separator else 'collect',
                    'productions': productions
                }

            if multiplicity is MULT_ZERO_OR_MORE:
                rules[symbol_mult] = {
                    'productions': [
                        {'production': [symbol_one]},
                        {'production': ['EMPTY']}
                    ]
                }

        elif multiplicity in MULT_OPTIONAL:
            if separator:
                raise GrammarError(
                    location=self._get_location(production_struct),
                    message='Repetition modifier not allowed for '
                    'optional (?) for symbol "{}".'.format(symbol))

            rules[symbol_mult] = {
                'action': 'optional',
                'productions': [
                    {'production': [symbol]},
                    {'production': ['EMPTY']}
                ]
            }

    def _create_terminals(self):
        """
        Create terminals of this grammar given the Python struct.
        """
        self.terminals.update([(s.name, s) for s in (EMPTY, EOF, STOP)])
        for terminal_name, terminal_struct \
                in self.grammar_struct.get('terminals', {}).items():
            location = self._get_location(terminal_struct)
            self._check_name(terminal_name, location)
            if terminal_name in self.terminals:
                raise GrammarError(
                    location=location,
                    message=f'"{terminal_name}" terminal multiple definition')
            recognizer = None
            recognizer_str = terminal_struct.get('recognizer')
            if recognizer_str:
                if recognizer_str.startswith('/') \
                   and recognizer_str.endswith('/') \
                   and len(recognizer_str) > 2:
                    recognizer = RegExRecognizer(recognizer_str[1:-1],
                                                 re_flags=self.re_flags,
                                                 ignore_case=self.ignore_case)
                else:
                    recognizer = StringRecognizer(recognizer_str,
                                                  ignore_case=self.ignore_case)
            term_modifiers = self._desugar_modifiers(
                terminal_struct.get('modifiers', []))
            terminal = Terminal(terminal_name,
                                location=location,
                                recognizer=recognizer,
                                prior=term_modifiers.get('prior',
                                                         DEFAULT_PRIORITY),
                                finish=term_modifiers.get('finish', None),
                                prefer=term_modifiers.get('prefer', False),
                                dynamic=term_modifiers.get('dynamic', False),
                                keyword=term_modifiers.get('keyword', False),
                                action=terminal_struct.get('action',
                                                           terminal_name),
                                meta=terminal_struct.get('meta'))
            self.terminals[terminal_name] = terminal

    def _create_productions(self):
        """
        Create productions of this grammar given the Python struct.
        """
        for rule_name, rule_struct in self.grammar_struct['rules'].items():
            location = self._get_location(rule_struct)
            self._check_name(rule_name, location)
            if rule_name in self.nonterminals or rule_name in self.terminals:
                raise GrammarError(
                    location=location,
                    message=f'"{rule_name}" rule multiple definitions')
            rule_modifiers = self._desugar_modifiers(
                rule_struct.get('modifiers', []))
            nt = NonTerminal(
                rule_name,
                location=location,
                assoc=rule_modifiers.get('assoc', ASSOC_NONE),
                prior=rule_modifiers.get('prior', DEFAULT_PRIORITY),
                dynamic=rule_modifiers.get('dynamic', False),
                ps=rule_modifiers.get('ps', None),
                pse=rule_modifiers.get('pse', None),
                meta=rule_struct.get('meta')
            )
            self.nonterminals[rule_name] = nt
            productions = []
            rule_assignments = {}
            for production_struct in rule_struct['productions']:
                location = self._get_location(production_struct)
                rhs = ProductionRHS(production_struct['production'])
                prod_modifiers = self._desugar_modifiers(
                    production_struct.get('modifiers', []))
                prod_assignments = {}
                assignments = production_struct.get('assignments', {})
                for assign_name, assignment_struct in assignments.items():
                    prod_assignments[assign_name] = \
                        Assignment(assign_name,
                                   op=assignment_struct['op'],
                                   symbol=assignment_struct['symbol'],
                                   mult=assignment_struct['mult'],
                                   rhs_idx=assignment_struct['rhs_idx'])
                productions.append(Production(
                    nt, rhs,
                    location=location,
                    action=production_struct.get(
                        'action', rule_struct.get('action', rule_name)),
                    assignments=prod_assignments.values(),
                    assoc=prod_modifiers.get('assoc', nt.assoc),
                    prior=prod_modifiers.get('prior', nt.prior),
                    dynamic=prod_modifiers.get('dynamic', nt.dynamic),
                    ps=prod_modifiers.get('ps', nt.ps),
                    pse=prod_modifiers.get('pse', nt.pse),
                    meta=production_struct.get('meta')
                ))
                rule_assignments.update(prod_assignments)
            nt.productions = productions
            if rule_assignments and rule_name not in self.classes:
                self._create_class(rule_name, rule_assignments)
                nt.action = 'obj'
            # AUGMENTED symbol production must be first
            if rule_name == AUGSYMBOL_NAME:
                self.productions.insert(0, productions[0])
            else:
                self.productions.extend(productions)

    def _enumerate_productions(self):
        """
        Enumerates all productions (prod_id) and production per symbol
        (prod_symbol_id).
        """
        idx_per_symbol = {}
        for idx, prod in enumerate(self.productions):
            prod.prod_id = idx
            prod.prod_symbol_id = idx_per_symbol.get(prod.symbol, 0)
            idx_per_symbol[prod.symbol] = \
                idx_per_symbol.get(prod.symbol, 0) + 1

    def _create_class(self, rule_name, rule_assignments):
        """
        Create class for each rule using assignments.
        """
        attrs = {}
        for a in rule_assignments.values():
            attrs[a.name] = PGAttribute(a.name, a.mult, a.symbol)

        class ParglareMetaClass(type):

            def __repr__(cls):
                return '<parglare:{} class at {}>'.format(rule_name, id(cls))

        @add_metaclass(ParglareMetaClass)
        class ParglareClass(object):
            """
            Dynamically created class for each parglare rule that uses named
            matches.

            :param _pg_attrs: A dict of meta-attributes keyed by name.  Used by
                common rules.
            :param int _pg_position: A position in the input string where this
                class is defined.
            :param int _pg_position_end: A position in the input string where
                this class ends.
            """

            _pg_attrs = attrs

            def __init__(self, **attrs):
                for attr_name, attr_value in attrs.items():
                    setattr(self, attr_name, attr_value)

            def __repr__(self):
                if hasattr(self, 'name'):
                    return "<{}:{}>".format(rule_name, self.name)
                else:
                    return "<parglare:{} instance at {}>"\
                        .format(rule_name, hex(id(self)))

        ParglareClass.__name__ = rule_name

        self.classes[rule_name] = ParglareClass

    def _desugar_modifiers(self, modifiers):
        """
        Returns a dict of desugared modifiers values.
        """
        mod_dict = {}
        for m in modifiers:
            if type(m) is int:
                mod_dict['prior'] = m
            elif m in ['left', 'reduce']:
                mod_dict['assoc'] = ASSOC_LEFT
            elif m in ['right', 'shift']:
                mod_dict['assoc'] = ASSOC_RIGHT
            elif m in ['ps', 'nops', 'greedy', 'nogreedy']:
                mod_dict['ps'] = not m.startswith('no')
            elif m in ['pse', 'nopse']:
                mod_dict['pse'] = not m.startswith('no')
            elif m == 'dynamic':
                mod_dict['dynamic'] = True
            elif m in ['finish', 'nofinish']:
                mod_dict['finish'] = not m.startswith('no')
            elif m == 'prefer':
                mod_dict['prefer'] = True
            elif m == 'keyword':
                mod_dict['keyword'] = True
        return mod_dict

    def _fix_keyword_terminals(self):
        """
        If KEYWORD terminal with regex match is given fix all matching string
        recognizers to match on a word boundary.
        """
        keyword_term = self.get_terminal('KEYWORD')
        if keyword_term is None:
            return

        # KEYWORD rule must have a regex recognizer
        keyword_rec = keyword_term.recognizer
        if not isinstance(keyword_rec, RegExRecognizer):
            raise GrammarError(
                location=keyword_term.location,
                message='KEYWORD rule must have a regex recognizer defined.')

        # Change each string recognizer corresponding to the KEYWORD
        # regex by the regex recognizer that match on word boundaries.
        for term in self.terminals.values():
            if isinstance(term.recognizer, StringRecognizer):
                match = keyword_rec(term.recognizer.value, 0)
                if match == term.recognizer.value:
                    term.recognizer = RegExRecognizer(
                        r'\b{}\b'.format(match),
                        ignore_case=term.recognizer.ignore_case)
                    term.keyword = True

    def _resolve(self):
        """
        Resolve productions RHS references.
        """
        for production in self.productions:
            for refidx, ref in enumerate(production.rhs):
                if type(ref) is dict:
                    ref = ref['symbol']
                production.rhs[refidx] = self.get_check_symbol(ref, production)

    def get_terminal(self, name):
        "Returns terminal with the given fully qualified name or name."
        return self.terminals.get(name)

    def get_nonterminal(self, name):
        "Returns non-terminal with the given fully qualified name or name."
        return self.nonterminals.get(name)

    def get_symbol(self, name):
        "Returns grammar symbol with the given name."
        s = self.get_terminal(name)
        if not s:
            s = self.get_nonterminal(name)
        return s

    def get_check_symbol(self, name, production):
        "Returns symbol if exists or raise grammar error if not."
        symbol = self.get_symbol(name)
        if not symbol:
            raise GrammarError(
                location=production.location,
                message='Unknown symbol "{}" in rule "{}".'
                .format(name, production.symbol.name))
        return symbol

    def __iter__(self):
        return (s for s in itertools.chain(self.nonterminals.values(),
                                           self.terminals.values())
                if s not in [self.AUGSYMBOL, STOP])

    def get_production_id(self, name):
        "Returns first production id for the given symbol name"
        for p in self.productions:
            if p.symbol.name == name:
                return p.prod_id

    @staticmethod
    def from_struct(grammar_struct, **kwargs):
        """
        Create grammar object from grammar given in a form of a Python data
        structure.
        """
        return Grammar(grammar_struct, **kwargs)

    @staticmethod
    def from_string(grammar_str, **kwargs):
        return Grammar.from_struct(Grammar.struct_from_string(grammar_str),
                                   **kwargs)

    @staticmethod
    def from_file(file_name, **kwargs):
        file_name = path.realpath(file_name)

        with open(file_name, 'r', encoding="utf-8") as f:
            content = f.read()
        return Grammar.from_struct(Grammar.struct_from_string(content),
                                   **kwargs)

    @staticmethod
    def struct_from_string(grammar_str, **kwargs):
        """
        Parse grammar string and return the grammar represented as Python
        structure.
        """
        from parglare.lang import get_grammar_parser
        debug = kwargs.pop('debug', False)
        debug_colors = kwargs.pop('debug_colors', False)
        return get_grammar_parser(
            debug=debug, debug_colors=debug_colors).parse(grammar_str,
                                                          **kwargs)

    @staticmethod
    def remove_locations(grammar_struct):
        """
        Remove location objects used to report errors during grammar
        construction.
        """
        for rule_name, rule_struct in grammar_struct['rules'].items():
            for production_struct in rule_struct['productions']:
                if 'location' in production_struct:
                    del production_struct['location']

        for terminal_name, terminal_struct \
                in grammar_struct.get('terminals', {}).items():
            if 'location' in terminal_struct:
                del terminal_struct['location']

    def _get_location(self, loc_struct):
        """
        Construct location object used in error reporting.
        """
        return loc_struct.get('location', THIS_LOCATION)

    def _check_name(self, name, location=None):
        """
        Used in actions to check for reserved names usage.
        """

        if name in RESERVED_SYMBOL_NAMES:
            raise GrammarError(
                location=location,
                message='Rule name "{}" is reserved.'.format(name))
        if '.' in name:
            raise GrammarError(
                location=location,
                message='Using dot in names is not allowed.'.format(name))

    def _make_multiplicity_name(self, symbol_name, multiplicity=None,
                                separator_name=None, modifiers=None):
        if multiplicity is None or multiplicity == MULT_ONE:
            return symbol_name
        name_by_mult = {
            MULT_ZERO_OR_MORE: "0",
            MULT_ONE_OR_MORE: "1",
            MULT_OPTIONAL: "opt"
        }
        name = "{}_{}{}".format(
            symbol_name, name_by_mult[multiplicity],
            "_{}".format(separator_name) if separator_name else "")
        if modifiers:
            modifiers = list(sorted(map(lambda x: str(x), modifiers)))
            mod_name_sufix = "_".join(modifiers)
        name += "_{}".format(mod_name_sufix) if modifiers else ""
        return name

    def print_debug(self):
        a_print("*** GRAMMAR ***", new_line=True)
        h_print("Terminals:")
        prints(" ".join([text(t) for t in self.terminals]))
        h_print("NonTerminals:")
        prints(" ".join([text(n) for n in self.nonterminals]))

        h_print("Productions:")
        for p in self.productions:
            prints(text(p))
