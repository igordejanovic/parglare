# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function
from os import path
import sys
import re
import itertools
from parglare.six import add_metaclass
from parglare.exceptions import GrammarError
from parglare.actions import pass_single, pass_none, collect, collect_sep
from parglare.termui import prints, s_emph, s_header, a_print, h_print
from parglare import termui

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
MULT_OPTIONAL = '0..1'
MULT_ONE_OR_MORE = '1..*'
MULT_ZERO_OR_MORE = '0..*'

RESERVED_SYMBOL_NAMES = ['EOF', 'STOP', 'EMPTY']
SPECIAL_SYMBOL_NAMES = ['KEYWORD', 'LAYOUT']


def escape(instr):
    return instr.replace('\n', r'\n').replace('\t', r'\t')


class GrammarSymbol(object):
    """
    Represents an abstract grammar symbol.

    Attributes:
    name(str): The name of this grammar symbol.
    action_name(string): Name of common/user action given in the grammar.
    action(callable): Resolved action given by the user. Overrides grammar
        action if provided. If not provided by the user defaults to
        grammar_action.
    grammar_action(callable): Resolved action given in the grammar.
    imported_with (PGFileImport): PGFileImport where this symbol is first time
        imported from. Used for FQN calculation.
    """
    def __init__(self, name):
        self.name = escape(name)
        self.action_name = None
        self.action = None
        self.grammar_action = None
        self.imported_with = None
        self._hash = hash(name)

    @property
    def fqn(self):
        if self.imported_with:
            return "{}.{}".format(self.imported_with.fqn, self.name)
        else:
            return self.name

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
    """Represents a non-termial symbol of the grammar.

    Attributes:
    productions(list of Production): A list of alternative productions for
        this NonTerminal.
    """
    def __init__(self, name, productions=None):
        super(NonTerminal, self).__init__(name)
        self.productions = productions if productions else []


class Terminal(GrammarSymbol):
    """Represent a terminal symbol of the grammar.

    Attributes:
    prior(int): Priority used for lexical disambiguation.
    dynamic(bool): Should dynamic disambiguation be called to resolve conflict
        involving this terminal.
    finish(bool): Used for scanning optimization. If this terminal is `finish`
        no other recognizers will be checked if this succeeds. If not provided
        in the grammar implicit rules will be used during table construction.
    prefer(bool): Prefer this recognizer in case of multiple recognizers match
        at the same place and implicit disambiguation doesn't resolve.
    keyword(bool): `True` if this Terminal represents keyword. `False` by
        default.

    recognizer(callable): Called with input list of objects and position in the
        stream. Should return a sublist of recognized objects. The sublist
        should be rooted at the given position.
    """
    def __init__(self, name, recognizer=None):
        self.prior = DEFAULT_PRIORITY
        self.recognizer = recognizer if recognizer else StringRecognizer(name)
        self.finish = None
        self.prefer = False
        self.dynamic = False
        self.keyword = False
        super(Terminal, self).__init__(name)


class Reference(object):
    """
    A name reference to a GrammarSymbol used for cross-resolving during
    grammar construction.
    """
    def __init__(self, name, module_name=None):
        self.name = name
        self.module_name = module_name

    def __repr__(self):
        if self.module_name:
            return "{}.{}".format(self.module_name, self.name)
        else:
            return self.name


class Recognizer(object):
    """
    Recognizers are callables capable of recognizing low-level patterns
    (a.k.a tokens) in the input.
    """
    def __init__(self, name):
        self.name = name


class StringRecognizer(Recognizer):
    def __init__(self, value, ignore_case=False):
        super(StringRecognizer, self).__init__(value)
        self.value = value
        self.ignore_case = ignore_case
        self.value_cmp = value.lower() if ignore_case else value

    def __call__(self, in_str, pos):
        if self.ignore_case:
            if in_str[pos:pos+len(self.value)].lower() == self.value_cmp:
                return self.value
        else:
            if in_str[pos:pos+len(self.value)] == self.value_cmp:
                return self.value


def esc_control_characters(regex):
    """
    Escape control characters in regular expressions.
    """
    unescapes = [('\a', r'\a'), ('\b', r'\b'), ('\f', r'\f'), ('\n', r'\n'),
                 ('\r', r'\r'), ('\t', r'\t'), ('\v', r'\v')]
    for val, text in unescapes:
        regex = regex.replace(val, text)
    return regex


class RegExRecognizer(Recognizer):
    def __init__(self, regex, re_flags=re.MULTILINE, ignore_case=False):
        super(RegExRecognizer, self).__init__(regex)
        self._regex = regex
        self.ignore_case = ignore_case
        if ignore_case:
            re_flags |= re.IGNORECASE
        self.re_flags = re_flags
        try:
            self.regex = re.compile(self._regex, re_flags)
        except re.error as ex:
            regex = esc_control_characters(self._regex)
            message = 'Regex compile error in /{}/ (report: "{}")'
            raise GrammarError(message.format(regex, str(ex)))

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
EMPTY.grammar_action = pass_none
EOF = Terminal("EOF", EOF_recognizer)
EOF.grammar_action = pass_none


class Production(object):
    """Represent production from the grammar.

    Attributes:
    symbol (GrammarSymbol):
    rhs (ProductionRHS):
    assignments(dict): Assignment instances keyed by name.
    assoc (int): Associativity. Used for ambiguity (shift/reduce) resolution.
    prior (int): Priority. Used for ambiguity (shift/reduce) resolution.
    dynamic (bool): Is dynamic disambiguation used for this production.
    nops (bool): Disable prefer_shifts strategy for this production.
        Only makes sense for GLR parser.
    nopse (bool): Disable prefer_shifts_over_empty strategy for this
        production. Only makes sense for GLR parser.
    prod_id (int): Ordinal number of the production.
    prod_symbol_id (int): A zero-based ordinal of alternative choice for this
        production grammar symbol.
    """

    def __init__(self, symbol, rhs, assignments=None, assoc=ASSOC_NONE,
                 prior=DEFAULT_PRIORITY, dynamic=False, nops=False,
                 nopse=False):
        """
        Args:
        symbol (GrammarSymbol): A grammar symbol on the LHS of the production.
        rhs (list of GrammarSymbols):
        """
        self.symbol = symbol
        self.rhs = rhs if rhs else ProductionRHS()
        self.assignments = None
        if assignments:
            self.assignments = {}
            for assignment in assignments:
                if assignment.name:
                    self.assignments[assignment.name] = assignment
        self.assoc = assoc
        self.prior = prior
        self.dynamic = dynamic
        self.nops = nops
        self.nopse = nopse

    def __str__(self):
        if hasattr(self, 'prod_id'):
            return (s_header("%d:") + " %s " + s_emph("=") +
                    " %s") % (self.prod_id, self.symbol, self.rhs)
        else:
            return ("%s " + s_emph("=") + " %s") % (self.symbol, self.rhs)

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


class Assignment(object):
    """
    General assignment (`=` or `?=`, a.k.a. `named matches`) in productions.
    Used also for references as LHS and assignment operator are optional.
    """
    def __init__(self, name, op, symbol, orig_symbol, multiplicity=MULT_ONE,
                 index=None):
        """
        Attributes:
            name(str): The name on the LHS of assignment.
            op(str): Either a `=` or `?=`.
            symbol(GrammarSymbol): A grammar symbol on the RHS.
            orig_symbol(GrammarSymbol): A de-sugarred grammar symbol on the
                RHS, i.e. referenced symbol without regex operators.
            multiplicty(str): Multiplicity of the RHS reference (used for regex
                operators ?, *, +). See MULT_* constants above. By default
                multiplicity is MULT_ONE.
            index(int): Index in the production RHS
        """
        self.name = name
        self.op = op
        self.symbol = symbol
        self.orig_symbol = orig_symbol
        self.multiplicity = multiplicity
        self.index = index


class PGAttribute(object):
    """
    PGAttribute definition created by named matches.

    Attributes:
        name(str): The name of the attribute.
        multiplicity(str): Multiplicity of the attribute. See MULT_* constants.
        type_name(str): The type name of the attribute value(s). It is also the
            name of the referring grammar rule.
    """
    def __init__(self, name, multiplicity, type_name):
        self.name = name
        self.multiplicity = multiplicity
        self.type_name = type_name


class PGFile(object):
    """Objects of this class represent parglare grammar files.

    Grammar files can be imported using `import` keyword. Rules referenced from
    the imported grammar must be fully qualified by the grammar module name. By
    default the name of the target .pg file is the name of the module. `as`
    keyword can be used to override the default.

    Example:
    ```
    import `some/path/mygrammar.pg` as target
    ```

    Rules from file `mygrammar.pg` will be available under `target` namespace:

    ```
    MyRule: target.someRule+;
    ```

    Actions are by default loaded from the file named `<grammar>_actions.py`
    where `grammar` is basename of grammar file. Recognizers are loaded from
    `<grammar>_recognizers.py`. Actions and recognizers given this way are both
    optional. Furthermore, both actions and recognizers can be overriden by
    supplying actions and/or recognizers dict during grammar/parser
    instantiation.

    Attributes:

    productions (list of Production): Local productions defined in this file.
    imports (dict): Mapping imported module/file local name to PGFile object.
    file_path (str): A full canonic path to the .pg file.
    grammar (PGFile): A root/grammar file.
    recognizers (dict of callables): A dict of Python callables used as a
        terminal recognizers.
    """
    def __init__(self, productions, terminals=None, imports=None,
                 file_path=None, grammar=None, recognizers=None):
        self.productions = productions
        self.terminals = terminals if terminals is not None else set()
        if imports:
            self.imports = {i.module_name: i for i in imports}
        else:
            self.imports = {}
        self.file_path = path.realpath(file_path) if file_path else None
        self.grammar = self if grammar is None else grammar
        self.recognizers = recognizers

        self.collect_and_unify_symbols()
        self.resolve_references()
        self.init_recognizers()

    def collect_and_unify_symbols(self):
        """Collect non-terminals and terminals (both explicit and implicit/inline)
        defined in this file and make sure there is only one instance for each
        of them.

        """
        nonterminals_by_name = {}
        terminals_by_name = {}
        terminals_by_value = {}

        # Check terminal uniqueness in both name and string recognition
        # and collect all terminals from explicit definitions.
        for terminal in self.terminals:
            if terminal.name in terminals_by_name:
                self.raise_grammar_error(
                    'Multiple definitions of terminal rule "{}"'
                    .format(terminal.name))
            if isinstance(terminal.recognizer, StringRecognizer):
                rec = terminal.recognizer
                if rec.value in terminals_by_value:
                    self.raise_grammar_error(
                        'Terminals "{}" and "{}" match the same string.'
                        .format(terminal.name,
                                terminals_by_value[rec.value].name))
                terminals_by_value[rec.value] = terminal
            terminals_by_name[terminal.name] = terminal

        # Collect inline terminals
        for production in self.productions:
            for idx, rhs_elem in enumerate(production.rhs):

                if isinstance(rhs_elem, StringRecognizer):
                    recognizer = rhs_elem
                    # First check if the same recognizer already exists.
                    if recognizer.value in terminals_by_value:
                        terminal = terminals_by_value[recognizer.value]
                        if not getattr(terminal, '_inline', False):
                            self.raise_grammar_error(
                                'Terminal match "{}" defined as explicit'
                                ' terminal "{}" and inline at the same time'.
                                format(recognizer.name, terminal.name))
                        else:
                            terminal = terminals_by_value[recognizer.value]
                    else:
                        terminal = Terminal(recognizer.name,
                                            recognizer=recognizer)
                        terminal._inline = True
                        terminals_by_name[terminal.name] = terminal
                        terminals_by_value[recognizer.value] = terminal
                    production.rhs[idx] = terminal

                elif isinstance(rhs_elem, Terminal):
                    # RHS might contain terminals if from_struct is used or
                    # built-in special terminals (STOP, EOF). We just have to
                    # make sure the same object is used everywhere.
                    terminal = rhs_elem
                    if terminal.name not in terminals_by_name:
                        terminals_by_name[terminal.name] = terminal
                    else:
                        if terminal is not terminals_by_name[terminal.name]:
                            self.raise_grammar_error(
                                'Multiple different terminals "{}" used in '
                                'the grammar.'.format(terminal.name))

        # Collect non-terminals
        for production in self.productions:
            symbol = production.symbol
            # Check that there is no terminal defined by the same name.
            if symbol.name in terminals_by_name:
                raise self.raise_grammar_error(
                    'Rule "{}" already defined as terminal'
                    .format(symbol.name))
            # Unify all non-terminal objects
            if symbol.name in nonterminals_by_name:
                old_symbol = symbol
                new_symbol = nonterminals_by_name[symbol.name]
                production.symbol = new_symbol
            else:
                nonterminals_by_name[symbol.name] = symbol
                old_symbol = new_symbol = symbol
            new_symbol.productions.append(production)
            self._resolve_action(old_symbol, new_symbol)

        self.terminals = set(terminals_by_name.values())
        self.terminals.update([EMPTY, EOF, STOP])

        self.nonterminals = set(nonterminals_by_name.values())
        nonterminals_by_name.update(terminals_by_name)
        self.symbols_by_name = nonterminals_by_name
        # Add special terminals
        self.symbols_by_name['EMPTY'] = EMPTY
        self.symbols_by_name['EOF'] = EOF
        self.symbols_by_name['STOP'] = STOP

    def _resolve_action(self, old_symbol, new_symbol):
        """
        Checks and resolves common semantic actions given in the grammar.
        """
        # Get/check grammar actions for rules/symbols.
        if new_symbol.action_name:
            if new_symbol.action_name != old_symbol.action_name:
                raise GrammarError(
                    'Multiple different grammar actions for rule "{}".'
                    .format(new_symbol.name))

            # Try to find action in built-in actions module
            # If action is not given we suppose that it is a user defined
            # action that will be provided during parser instantiation
            # using `actions` param.
            import parglare.actions as actmodule
            if hasattr(actmodule, new_symbol.action_name):
                new_symbol.action = \
                    new_symbol.grammar_action = getattr(actmodule,
                                                        new_symbol.action_name)

    def resolve_references(self):
        for production in self.productions:
            for idx, ref in enumerate(production.rhs):
                if isinstance(ref, Reference):
                    production.rhs[idx] = self.resolve(ref.name)

    def init_recognizers(self):
        """Load recognizers from <grammar_name>_recognizers.py. Override
        with provided recognizers.

        """
        if self.file_path:
            recognizers_file = path.join(path.dirname(self.file_path),
                                         "{}_recognizers.py".format(
                                             path.basename(self.file_path)))

            if path.exists(recognizers_file):
                # noqa See https://stackoverflow.com/questions/67631/how-to-import-a-module-given-the-full-path
                mod_name = "{}.recognizers".format()
                if sys.version_info >= (3, 5):
                    import importlib.util
                    spec = importlib.util.spec_from_file_location(
                        mod_name, recognizers_file)
                    rec_module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(rec_module)
                elif sys.version_info >= (3, 3):
                    from importlib.machinery import SourceFileLoader
                    mod_recognizers = SourceFileLoader(
                        mod_name, recognizers_file).load_module()
                else:
                    import imp
                    rec_module = imp.load_source(mod_name, recognizers_file)
                mod_recognizers = rec_module.recognizer.all

                for symbol_name, symbol in self.symbols_by_name.items():
                    if symbol_name in mod_recognizers:
                        if not isinstance(symbol, Terminal):
                            raise GrammarError(
                                'Recognizer given for non-terminal'
                                ' "{}" in file "{}"'.format(symbol.name,
                                                            recognizers_file))

        # Override by recognizers given during instantiation.
        # TODO: Check that FQN are handled correctly.
        if self.recognizers:
            for symbol in self.symbols_by_name.values():
                if symbol.fqn in self.recognizers:
                    if not isinstance(symbol, Terminal):
                        raise GrammarError(
                            'Recognizer given for non-terminal'
                            ' "{}" in recognizers parameters.'.format(
                                symbol.fqn))

    def resolve(self, symbol_name):
        """Resolves given symbol by its name.

        For local name search this file, for FQN use imports and delegate to
        imported file.

        On each resolved symbol productions in the root file are updated.

        """
        if '.' in symbol_name:
            import_module_name, name = symbol_name.split('.')
            try:
                imported_pg_file = self.imports[import_module_name]
            except KeyError:
                self.raise_grammar_error(
                    'Unexisting module "{}" in reference "{}"'
                    .format(import_module_name, symbol_name),
                    'referenced from file')
            return imported_pg_file.resolve(name)
        else:
            symbol = self.symbols_by_name.get(symbol_name)
            if not symbol:
                self.raise_grammar_error('Unknown symbol "{}"'
                                         .format(symbol_name),
                                         'referenced from file')
            return symbol

    def raise_grammar_error(self, message, message2='in file'):
        raise GrammarError("{}{}.".format(
            message,
            ' {} "{}"'.format(message2, self.file_path)
            if self.file_path else ""))


class Grammar(PGFile):
    """
    Grammar is a collection of production rules, nonterminals and terminals.
    First production is reserved for the augmented production (S' -> S).

    Attributes:
    start_symbol (GrammarSymbol or str): start/root symbol of the grammar or
        its name.
    files (dict): A global registry of PGFile instances keyed by abs path.
    nonterminals (set of NonTerminal):
    terminals(set of Terminal):

    """

    def __init__(self, productions=None, terminals=None, imports=None,
                 file_path=None, recognizers=None, start_symbol=None,
                 _no_check_recognizers=False, re_flags=re.MULTILINE,
                 ignore_case=False, debug=False, debug_parse=False,
                 debug_colors=False):
        """
        Grammar constructor is not meant to be called directly by the user.
        See `from_str` and `from_file` static methods instead.

        Arguments:
        see Grammar attributes.
        _no_check_recognizers (bool, internal): Used by pglr tool to circumvent
             errors for empty recognizers that will be provided in user code.
        """
        super(Grammar, self).__init__(productions=productions,
                                      terminals=terminals,
                                      imports=imports,
                                      file_path=file_path, grammar=self,
                                      recognizers=recognizers)

        self._no_check_recognizers = _no_check_recognizers

        if file_path is not None:
            self.files = {file_path: self}

        # Determine start symbol. If name is provided search for it. If name is
        # not given use the first production LHS symbol as the start symbol.
        if start_symbol:
            if isinstance(start_symbol, str):
                for p in self.productions:
                    if p.symbol.name == start_symbol:
                        self.start_symbol = p.symbol
            else:
                self.start_symbol = start_symbol
        else:
            # By default, first production symbol is the start symbol.
            self.start_symbol = self.productions[0].symbol

        self._init_grammar()

    def _init_grammar(self):
        """
        Extracts all grammar symbol (nonterminal and terminal) from the
        grammar, resolves and check references in productions, unify all
        grammar symbol objects and enumerate productions.
        """
        # Reserve 0 production. It is used for augmented prod. in LR
        # automata calculation.
        self.productions.insert(
            0,
            Production(AUGSYMBOL, ProductionRHS([self.start_symbol, STOP])))
        self.nonterminals.add(AUGSYMBOL)
        self.symbols_by_name[AUGSYMBOL.name] = AUGSYMBOL

        # Connect recognizers, override grammar provided
        if not self._no_check_recognizers:
            self._connect_override_recognizers()

        self._enumerate_productions()
        self._fix_keyword_terminals()

    def _connect_override_recognizers(self):
        for term in self.terminals:
            if self.recognizers and term.name in self.recognizers:
                term.recognizer = self.recognizers[term.name]
            else:
                if term.recognizer is None:
                    if not self.recognizers:
                        raise GrammarError(
                            'Terminal "{}" has no recognizer defined '
                            'and no recognizers are given during grammar '
                            'construction.'.format(term.name))
                    else:
                        if term.name not in self.recognizers:
                            raise GrammarError(
                                'Terminal "{}" has no recognizer defined.'
                                .format(term.name))

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
                'KEYWORD rule must have a regex recognizer defined.')

        # Change each string recognizer corresponding to the KEYWORD
        # regex by the regex recognizer that match on word boundaries.
        for term in self.terminals:
            if isinstance(term.recognizer, StringRecognizer):
                match = keyword_rec(term.recognizer.value, 0)
                if match == term.recognizer.value:
                    term.recognizer = RegExRecognizer(
                        r'\b{}\b'.format(match),
                        ignore_case=term.recognizer.ignore_case)
                    term.keyword = True

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

    def __iter__(self):
        return (s for s in itertools.chain(self.nonterminals, self.terminals)
                if s not in [AUGSYMBOL, STOP])

    def get_production_id(self, name):
        "Returns first production id for the given symbol name"
        for p in self.productions:
            if p.symbol.name == name:
                return p.prod_id

    @staticmethod
    def from_struct(productions, terminals=None, start_symbol=None,
                    recognizers=None):
        """Used internally to bootstrap grammar file parser."""
        return Grammar(productions=create_productions(productions),
                       terminals=terminals,
                       start_symbol=start_symbol, recognizers=recognizers)

    @staticmethod
    def _parse(parse_fun_name, what_to_parse, recognizers=None,
               ignore_case=False, re_flags=re.MULTILINE, debug=False,
               debug_parse=False, debug_colors=False,
               _no_check_recognizers=False):
        from .parser import Context
        context = Context()
        context.re_flags = re_flags
        context.ignore_case = ignore_case
        context.debug = debug
        context.debug_colors = debug_colors
        context.classes = {}
        context.imported_files = {}
        grammar_parser = get_grammar_parser(debug_parse, debug_colors)
        imports, productions, terminals = \
            getattr(grammar_parser, parse_fun_name)(what_to_parse,
                                                    context=context)
        g = Grammar(productions=productions,
                    terminals=terminals,
                    imports=imports,
                    recognizers=recognizers,
                    file_path=what_to_parse
                    if parse_fun_name == 'parse_file' else None,
                    _no_check_recognizers=_no_check_recognizers)
        g.classes = context.classes
        termui.colors = debug_colors
        if debug:
            g.print_debug()

        return g

    @staticmethod
    def from_string(grammar_str, **kwargs):
        return Grammar._parse('parse', grammar_str, **kwargs)

    @staticmethod
    def from_file(file_name, **kwargs):
        file_name = path.realpath(file_name)
        return Grammar._parse('parse_file', file_name, **kwargs)

    def print_debug(self):
        a_print("*** GRAMMAR ***", new_line=True)
        h_print("Terminals:")
        prints(" ".join([text(t) for t in self.terminals]))
        h_print("NonTerminals:")
        prints(" ".join([text(n) for n in self.nonterminals]))

        h_print("Productions:")
        for p in self.productions:
            prints(text(p))


class PGFileImport(object):
    """
    Represents import of a grammar file.

    Attributes:
    module_name (str): Name of this import. By default is the name of grammar
        file without .pg extension.
    file_path (str): A canonical full path of the imported .pg file.
    imported_with (PGFileImport): First import this import is imported from.
        Used for FQN calculation.
    fqn (str): Fully qualified name by first path of imports.
    context: Parsing context, used to lazy load the pg file.
    pgfile (PGFile instance or None):

    """
    def __init__(self, module_name, file_path, context):
        self.module_name = module_name
        self.file_path = file_path
        self.context = context
        self.imported_with = None
        self.pgfile = None

    @property
    def fqn(self):
        "A fully qualified name of the import following the first import path."
        if self.imported_with:
            return "{}.{}".format(self.imported_with.fqn, self.module_name)
        else:
            return self.module_name

    def resolve(self, symbol_name):
        "Resolves symbol from the imported file."

        if self.pgfile is None:
            # First search the global registry of imported files.
            if self.file_path in self.context.imported_files:
                self.pgfile = self.context.imported_files[self.file_path]
            else:
                # If not found construct new PGFile
                self.context.new_productions = {}
                imports, productions, terminals = \
                    get_grammar_parser(
                        self.context.debug,
                        self.context.debug_colors).parse_file(
                            self.file_path, context=self.context)
                self.pgfile = PGFile(productions=productions,
                                     terminals=terminals,
                                     imports=imports,
                                     file_path=self.file_path)
                self.context.imported_files[self.file_path] = self.pgfile

        return self.pgfile.resolve(symbol_name)


def create_productions(productions):
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

        # Convert strings to string recognizers
        for idx, t in enumerate(rhs):
            if isinstance(t, text):
                rhs[idx] = StringRecognizer(t)

        gp.append(Production(symbol, rhs, assoc=assoc, prior=prior))

    return gp


def check_name(context, name):
    """
    Used in actions to check for reserved names usage.
    """

    if name in RESERVED_SYMBOL_NAMES:
            from parglare.parser import pos_to_line_col
            raise GrammarError('Rule name "{}" at {} is reserved.'.format(
                name, pos_to_line_col(context.input_str,
                                      context.start_position)))


# Grammar for grammars

(PGFILE,
 IMPORTS,
 IMPORT,
 PRODUCTION_RULES,
 PRODUCTION_RULE,
 PRODUCTION_RULE_WITH_ACTION,
 PRODUCTION_RULE_RHS,
 PRODUCTION,
 TERMINAL_RULES,
 TERMINAL_RULE,
 TERMINAL_RULE_WITH_ACTION,
 PROD_DIS_RULE,
 PROD_DIS_RULES,
 TERM_DIS_RULE,
 TERM_DIS_RULES,

 ASSIGNMENT,
 ASSIGNMENTS,
 PLAIN_ASSIGNMENT,
 BOOL_ASSIGNMENT,

 REPEATABLE_GSYMBOL,
 REPEATABLE_GSYMBOLS,
 OPT_REP_OPERATOR,
 REP_OPERATOR_ZERO,
 REP_OPERATOR_ONE,
 REP_OPERATOR_OPTIONAL,
 OPT_REP_MODIFIERS_EXP,
 OPT_REP_MODIFIERS,
 OPT_REP_MODIFIER,

 GSYMBOL,
 RECOGNIZER,
 LAYOUT,
 LAYOUT_ITEM,
 COMMENT,
 CORNC,
 CORNCS) = [NonTerminal(name) for name in [
     'PGFile',
     'Imports',
     'Import',
     'ProductionRules',
     'ProductionRule',
     'ProductionRuleWithAction',
     'ProductionRuleRHS',
     'Production',
     'TerminalRules',
     'TerminalRule',
     'TerminalRuleWithAction',
     'ProductionDisambiguationRule',
     'ProductionDisambiguationRules',
     'TerminalDisambiguationRule',
     'TerminalDisambiguationRules',

     'Assignment',
     'Assignments',
     'PlainAssignment',
     'BoolAssignment',

     'RepeatableGrammarSymbol',
     'RepeatableGrammarSymbols',
     'OptRepeatOperator',
     'RepeatOperatorZero',
     'RepeatOperatorOne',
     'RepeatOperatorOptional',
     'OptionalRepeatModifiersExpression',
     'OptionalRepeatModifiers',
     'OptionalRepeatModifier',

     'GrammarSymbol',
     'Recognizer',
     'LAYOUT',
     'LAYOUT_ITEM',
     'Comment',
     'CORNC',
     'CORNCS']]

pg_terminals = \
    (NAME,
     STR_TERM,
     REGEX_TERM,
     PRIOR,
     ACTION,
     WS,
     COMMENTLINE,
     NOTCOMMENT) = [Terminal(name, RegExRecognizer(regex)) for name, regex in
                    [
                        ('Name', r'[a-zA-Z0-9_\.]+'),
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
    [PGFILE, [PRODUCTION_RULES, EOF]],
    [PGFILE, [IMPORTS, PRODUCTION_RULES, EOF]],
    [PGFILE, [PRODUCTION_RULES, 'terminals', TERMINAL_RULES, EOF]],
    [PGFILE, [IMPORTS, PRODUCTION_RULES, 'terminals', TERMINAL_RULES, EOF]],
    [IMPORTS, [IMPORTS, IMPORT]],
    [IMPORTS, [IMPORT]],
    [IMPORT, ['import', STR_TERM, ';']],
    [IMPORT, ['import', STR_TERM, 'as', NAME, ';']],
    [PRODUCTION_RULES, [PRODUCTION_RULES, PRODUCTION_RULE_WITH_ACTION]],
    [PRODUCTION_RULES, [PRODUCTION_RULE_WITH_ACTION]],

    [PRODUCTION_RULE_WITH_ACTION, [ACTION, PRODUCTION_RULE]],
    [PRODUCTION_RULE_WITH_ACTION, [PRODUCTION_RULE]],
    [PRODUCTION_RULE, [NAME, ':', PRODUCTION_RULE_RHS, ';']],
    [PRODUCTION_RULE, [NAME, '{', PROD_DIS_RULES, '}', ':',
                       PRODUCTION_RULE_RHS, ';']],
    [PRODUCTION_RULE_RHS, [PRODUCTION_RULE_RHS, '|', PRODUCTION],
     ASSOC_LEFT, 5],
    [PRODUCTION_RULE_RHS, [PRODUCTION], ASSOC_LEFT, 5],
    [PRODUCTION, [ASSIGNMENTS]],
    [PRODUCTION, [ASSIGNMENTS, '{', PROD_DIS_RULES, '}']],

    [TERMINAL_RULES, [TERMINAL_RULES, TERMINAL_RULE_WITH_ACTION]],
    [TERMINAL_RULES, [TERMINAL_RULE_WITH_ACTION]],
    [TERMINAL_RULE_WITH_ACTION, [ACTION, TERMINAL_RULE]],
    [TERMINAL_RULE_WITH_ACTION, [TERMINAL_RULE]],
    [TERMINAL_RULE, [NAME, ':', RECOGNIZER, ';'], ASSOC_LEFT, 15],
    [TERMINAL_RULE, [NAME, ':', ';'], ASSOC_LEFT, 15],
    [TERMINAL_RULE, [NAME, ':', RECOGNIZER, '{', TERM_DIS_RULES, '}', ';'],
     ASSOC_LEFT, 15],
    [TERMINAL_RULE, [NAME, ':', '{', TERM_DIS_RULES, '}', ';'],
     ASSOC_LEFT, 15],

    [PROD_DIS_RULE, ['left']],
    [PROD_DIS_RULE, ['reduce']],
    [PROD_DIS_RULE, ['right']],
    [PROD_DIS_RULE, ['shift']],
    [PROD_DIS_RULE, ['dynamic']],
    [PROD_DIS_RULE, ['nops']],   # no prefer shifts
    [PROD_DIS_RULE, ['nopse']],  # no prefer shifts over empty
    [PROD_DIS_RULE, [PRIOR]],
    [PROD_DIS_RULES, [PROD_DIS_RULES, ',', PROD_DIS_RULE], ASSOC_LEFT],
    [PROD_DIS_RULES, [PROD_DIS_RULE]],

    [TERM_DIS_RULE, ['prefer']],
    [TERM_DIS_RULE, ['finish']],
    [TERM_DIS_RULE, ['nofinish']],
    [TERM_DIS_RULE, ['dynamic']],
    [TERM_DIS_RULE, [PRIOR]],
    [TERM_DIS_RULES, [TERM_DIS_RULES, ',', TERM_DIS_RULE]],
    [TERM_DIS_RULES, [TERM_DIS_RULE]],

    # Assignments
    [ASSIGNMENT, [PLAIN_ASSIGNMENT]],
    [ASSIGNMENT, [BOOL_ASSIGNMENT]],
    [ASSIGNMENT, [REPEATABLE_GSYMBOL]],
    [ASSIGNMENTS, [ASSIGNMENTS, ASSIGNMENT]],
    [ASSIGNMENTS, [ASSIGNMENT]],
    [PLAIN_ASSIGNMENT, [NAME, '=', REPEATABLE_GSYMBOL]],
    [BOOL_ASSIGNMENT, [NAME, '?=', REPEATABLE_GSYMBOL]],

    # Regex-like repeat operators
    [REPEATABLE_GSYMBOL, [GSYMBOL, OPT_REP_OPERATOR]],
    [OPT_REP_OPERATOR, [REP_OPERATOR_ZERO]],
    [OPT_REP_OPERATOR, [REP_OPERATOR_ONE]],
    [OPT_REP_OPERATOR, [REP_OPERATOR_OPTIONAL]],
    [OPT_REP_OPERATOR, [EMPTY]],
    [REP_OPERATOR_ZERO, ['*', OPT_REP_MODIFIERS_EXP]],
    [REP_OPERATOR_ONE, ['+', OPT_REP_MODIFIERS_EXP]],
    [REP_OPERATOR_OPTIONAL, ['?', OPT_REP_MODIFIERS_EXP]],
    [OPT_REP_MODIFIERS_EXP, ['[', OPT_REP_MODIFIERS, ']']],
    [OPT_REP_MODIFIERS_EXP, [EMPTY]],
    [OPT_REP_MODIFIERS, [OPT_REP_MODIFIERS, ',', OPT_REP_MODIFIER]],
    [OPT_REP_MODIFIERS, [OPT_REP_MODIFIER]],
    [OPT_REP_MODIFIER, [NAME]],

    [GSYMBOL, [NAME]],
    [GSYMBOL, [STR_TERM]],
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


def get_grammar_parser(debug, debug_colors):
    global grammar_parser
    if not grammar_parser:
        from parglare import Parser
        grammar_parser = Parser(Grammar.from_struct(pg_productions,
                                                    pg_terminals, PGFILE),
                                actions=pg_actions,
                                debug=debug,
                                debug_colors=debug_colors)
    EMPTY.action = pass_none
    EOF.action = pass_none
    return grammar_parser


def act_pgfile(context, nodes):
    if len(nodes) in [3, 5]:
        imports = nodes.pop(0)
    else:
        imports = []
    productions = nodes.pop(0)
    terminals = nodes[1] if len(nodes) > 1 else []

    if hasattr(context, 'new_productions'):
        for _, (nt, prods) in context.new_productions.items():
            productions.extend(prods)
    return [imports, productions, terminals]


def act_import(context, nodes):
    if not context.file_name:
        raise GrammarError('Import can be used only for grammars '
                           'defined in files.')
    import_path = nodes[1]
    module_name = nodes[3] if len(nodes) > 3 else None
    if module_name is None:
        module_name = path.splitext(path.basename(import_path))[0]
    if not path.isabs(import_path):
        import_path = path.realpath(path.join(path.dirname(context.file_name),
                                              import_path))
    else:
        import_path = path.realpath(import_path)

    return PGFileImport(module_name, import_path, context)


def act_production_rules(_, nodes):
    e1, e2 = nodes
    e1.extend(e2)
    return e1


def act_production_rule_with_action(_, nodes):
    if len(nodes) > 1:
        action_name, productions = nodes
        # Strip @ char
        action_name = action_name[1:]
        for p in productions:
            p.symbol.action_name = action_name
    else:
        productions = nodes[0]

    return productions


def act_production_rule(context, nodes):
    name, _, rhs_prods, __ = nodes

    check_name(context, name)

    symbol = NonTerminal(name)

    # Collect all productions for this rule
    prods = []
    attrs = {}
    for prod in rhs_prods:
        assignments, disrules = prod
        # Here we know the indexes of assignments
        for idx, a in enumerate(assignments):
            if a.name:
                a.index = idx
        gsymbols = (a.symbol for a in assignments)
        assoc = disrules.get('assoc', ASSOC_NONE)
        prior = disrules.get('priority', DEFAULT_PRIORITY)
        dynamic = disrules.get('dynamic', False)
        nops = disrules.get('nops', False)
        nopse = disrules.get('nopse', False)
        prods.append(Production(symbol,
                                ProductionRHS(gsymbols),
                                assignments=assignments,
                                assoc=assoc,
                                prior=prior,
                                dynamic=dynamic,
                                nops=nops,
                                nopse=nopse))

        for a in assignments:
            if a.name:
                attrs[a.name] = PGAttribute(a.name, a.multiplicity,
                                            a.orig_symbol.name)
            # TODO: check/handle multiple assignments to the same attribute
            #       If a single production have multiple assignment of the
            #       same attribute, multiplicity must be set to many.

    # If named matches are used create Python class that will be used
    # for object instantiation.
    if attrs:
        class ParglareMetaClass(type):

            def __repr__(cls):
                return '<parglare:{} class at {}>'.format(name, id(cls))

        @add_metaclass(ParglareMetaClass)
        class ParglareClass(object):
            """Dynamicaly created class. Each parglare rule that uses named
            matches by default uses this action that will create Python object
            of this class.

            Attributes:
                _pg_attrs(dict): A dict of meta-attributes keyed by name.
                    Used by common rules.
                _pg_position(int): A position in the input string where
                    this class is defined.
                _pg_position_end(int): A position in the input string where
                    this class ends.

            """

            _pg_attrs = attrs

            def __init__(self, **attrs):
                for attr_name, attr_value in attrs.items():
                    setattr(self, attr_name, attr_value)

            def __repr__(self):
                if hasattr(self, 'name'):
                    return "<{}:{}>".format(name, self.name)
                else:
                    return "<parglare:{} instance at {}>"\
                        .format(name, hex(id(self)))

        ParglareClass.__name__ = str(name)
        if name in context.classes:
            # If rule has multiple definition merge attributes.
            context.classes[name]._pg_attrs.update(attrs)
        else:
            context.classes[name] = ParglareClass

        symbol.action_name = 'obj'

    return prods


def act_production(_, nodes):
    assignments = nodes[0]
    disrules = {}
    if len(nodes) > 1:
        rules = nodes[2]
        for rule in rules:
            if rule in ['left', 'reduce']:
                disrules['assoc'] = ASSOC_LEFT
            elif rule in ['right', 'shift']:
                disrules['assoc'] = ASSOC_RIGHT
            elif rule == 'dynamic':
                disrules['dynamic'] = True
            elif rule == 'nops':
                disrules['nops'] = True
            elif rule == 'nopse':
                disrules['nopse'] = True
            elif type(rule) is int:
                disrules['priority'] = rule

    return (assignments, disrules)


def _set_term_props(term, props):
    for t in props:
        if type(t) is int:
            term.prior = t
        elif t == 'finish':
            term.finish = True
        elif t == 'nofinish':
            term.finish = False
        elif t == 'prefer':
            term.prefer = True
        elif t == 'dynamic':
            term.dynamic = True
        else:
            print(t)
            assert False


def act_term_rule(context, nodes):

    name = nodes[0]
    recognizer = nodes[2]

    check_name(context, name)
    term = Terminal(name, recognizer)
    if len(nodes) > 4:
        _set_term_props(term, nodes[4])
    return term


def act_term_rule_empty_body(context, nodes):
    name = nodes[0]

    check_name(context, name)
    term = Terminal(name)
    term.recognizer = None
    if len(nodes) > 3:
        _set_term_props(term, nodes[3])
    return term


def act_term_rule_with_action(context, nodes):
    if len(nodes) > 1:
        action_name, term = nodes
        # Strip @ char
        action_name = action_name[1:]
        term.action_name = action_name
    else:
        term = nodes[0]

    return term


def make_repetition(context, gsymbol, sep_ref, suffix,
                    action, prod_callable):
    new_gsymbol_name = gsymbol.name + suffix
    if sep_ref:
        new_gsymbol_name += '_' + sep_ref.name

    if not hasattr(context, 'new_productions'):
        # symbol_name -> (NonTerminal, [productions])
        context.new_productions = {}

    if new_gsymbol_name in context.new_productions:
        return context.new_productions[new_gsymbol_name][0]

    new_nt = NonTerminal(new_gsymbol_name)
    if type(action) is text:
        new_nt.action_name = action
    else:
        new_nt.action = action
    new_productions = prod_callable(new_nt)
    context.new_productions[new_gsymbol_name] = (new_nt, new_productions)

    return new_nt


def make_one_or_more(context, gsymbol, sep_ref=None):
    def prod_callable(new_nt):
        new_productions = []
        if sep_ref:
            new_productions.append(
                Production(new_nt,
                           ProductionRHS([new_nt, sep_ref, gsymbol])))
        else:
            new_productions.append(
                Production(new_nt, ProductionRHS([new_nt, gsymbol])))

        new_productions.append(
            Production(new_nt, ProductionRHS([gsymbol])))

        return new_productions

    return make_repetition(context, gsymbol, sep_ref, '_1',
                           'collect' if sep_ref is None else 'collect_sep',
                           prod_callable)


def make_zero_or_more(context, gsymbol, sep_ref=None):
    def prod_callable(new_nt):
        new_productions = []
        one_or_more = make_one_or_more(context, gsymbol, sep_ref)
        new_productions.append(
            Production(new_nt, ProductionRHS([one_or_more]), nops=True))
        new_productions.append(
            Production(new_nt, ProductionRHS([EMPTY])))

        return new_productions

    def action(_, nodes):
        if nodes:
            return nodes[0]
        else:
            return []

    return make_repetition(
        context, gsymbol, sep_ref, '_0', action, prod_callable)


def make_optional(context, gsymbol, sep_ref=None):
    def prod_callable(new_nt):
        if sep_ref:
            from parglare import pos_to_line_col
            raise GrammarError(
                'Repetition modifier not allowed for '
                'optional (?) for symbol "{}" at {}.'
                .format(gsymbol.name,
                        pos_to_line_col(context.input_str,
                                        context.start_position)))
        # Optional
        new_productions = [Production(new_nt, ProductionRHS([gsymbol])),
                           Production(new_nt, ProductionRHS([EMPTY]))]

        return new_productions

    return make_repetition(
        context, gsymbol, sep_ref, '_opt', 'optional',
        prod_callable)


def act_repeatable_gsymbol(context, nodes):
    """Repetition operators (`*`, `+`, `?`) will create additional productions in
    the grammar with name generated from original symbol name and suffixes:
    - `_0` - for `*`
    - `_1` - for `+`
    - `_opt` - for `?`

    Zero or more produces `one or more` productions and additional productions
    of the form:

    ```
    somerule_0: somerule_1 | EMPTY;
    ```

    In addition if separator is used another suffix is added which is the name
    of the separator rule, for example:

    ```
    spam*[comma] --> spam_0_comma and spam_1_comma
    spam+[comma] --> spam_1_comma
    spam* --> spam_0 and spam_1
    spam? --> spam_opt
    ```

    """
    gsymbol, rep_op = nodes

    if not rep_op:
        return gsymbol, gsymbol, MULT_ONE

    if len(rep_op) > 1:
        rep_op, modifiers = rep_op
    else:
        rep_op = rep_op[0]
        modifiers = None

    sep_ref = None
    if modifiers:
        sep_ref = modifiers[1]
        sep_ref = Reference(sep_ref)

    if rep_op == '*':
        new_nt = make_zero_or_more(context, gsymbol, sep_ref)
        multiplicity = MULT_ZERO_OR_MORE
    elif rep_op == '+':
        new_nt = make_one_or_more(context, gsymbol, sep_ref)
        multiplicity = MULT_ONE_OR_MORE
    else:
        new_nt = make_optional(context, gsymbol, sep_ref)
        multiplicity = MULT_OPTIONAL

    return new_nt, gsymbol, multiplicity


def act_assignment(_, nodes):
    repeatable_gsymbol = nodes[0]
    if type(repeatable_gsymbol[0]) in (NonTerminal, Terminal,
                                       StringRecognizer, Reference):
        symbol, orig_symbol, multiplicity = repeatable_gsymbol
        name, op = None, None
    else:
        # Named match
        name, op, repeatable_gsymbol = repeatable_gsymbol
        symbol, orig_symbol, multiplicity = repeatable_gsymbol

    return Assignment(name, op, symbol, orig_symbol, multiplicity)


def act_recognizer_str(context, nodes):
    value = nodes[0]
    value = value.replace(r'\"', '"')\
                 .replace(r"\'", "'")\
                 .replace(r"\\", "\\")\
                 .replace(r"\n", "\n")\
                 .replace(r"\t", "\t")
    return StringRecognizer(value, ignore_case=context.ignore_case)


def act_recognizer_regex(context, nodes):
    value = nodes[0]
    return RegExRecognizer(value, re_flags=context.re_flags,
                           ignore_case=context.ignore_case)


def act_str_regex_term(context, value):
    return value[1:-1]


pg_actions = {
    "PGFile": act_pgfile,
    "Imports": collect,
    "Import": act_import,

    "ProductionRules": [act_production_rules, pass_single],
    'ProductionRule': act_production_rule,
    'ProductionRuleWithAction': act_production_rule_with_action,
    'ProductionRuleRHS': collect_sep,
    'Production': act_production,

    'TerminalRules': collect,
    'TerminalRule': [act_term_rule,
                     act_term_rule_empty_body,
                     act_term_rule,
                     act_term_rule_empty_body],
    'TerminalRuleWithAction': act_term_rule_with_action,

    "ProductionDisambiguationRules": collect_sep,
    "TerminalDisambiguationRules": collect_sep,

    "Assignment": act_assignment,
    "Assignments": collect,

    'RepeatableGrammarSymbol': act_repeatable_gsymbol,
    'RepeatableGrammarSymbols': collect,

    'GrammarSymbol': [lambda _, nodes: Reference(nodes[0]),
                      act_recognizer_str],

    'Recognizer': [act_recognizer_str, act_recognizer_regex],
    'StrTerm': act_str_regex_term,
    'RegExTerm': act_str_regex_term,

    # Terminals
    "Prior": lambda _, value: int(value),

}
