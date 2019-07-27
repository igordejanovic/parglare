"""
This module defines parglare textual grammar language using parglare internal
DSL specification.

"""
from parglare.actions import Actions
from parglare.grammar import Grammar, MODIFIERS
from parglare import GrammarError
from parglare.common import Location


def _(s):
    """
    Returns a terminal definition
    """
    return {'recognizer': s}


pg_grammar = {
    'start': 'PGFile',
    'rules': {
        'PGFile': {
            'productions': [
                {'production': ['ProductionRules', 'EOF']},
                {'production': ['Imports', 'ProductionRules', 'EOF']},
                {'production': ['ProductionRules',
                                'TERMINALS', 'TerminalRules', 'EOF']},
                {'production': ['Imports', 'ProductionRules',
                                'TERMINALS', 'TerminalRules', 'EOF']},
                {'production': ['TERMINALS', 'TerminalRules', 'EOF']},
            ]
        },
        'Imports': {
            'action': 'collect',
            'productions': [
                {'production': ['Imports', 'Import']},
                {'production': ['Import']},
            ]
        },
        'Import': {
            #'action': 'pgimport',
            'productions': [
                {'production': ['IMPORT', 'STR', 'SEMICOLON']},
                {'production': ['IMPORT', 'STR', 'AS', 'NAME', 'SEMICOLON']},
            ]
        },
        'ProductionRules': {
            'action': 'collect',
            'productions': [
                {'production': ['ProductionRules',
                                'ProductionRuleWithAction']},
                {'production': ['ProductionRuleWithAction']}
            ]
        },
        'ProductionRuleWithAction': {
            'action': 'rule_with_action',
            'productions': [
                {'production': ['ACTION', 'ProductionRule']},
                {'production': ['ProductionRule']},
            ]
        },
        'ProductionRule': {
            'productions': [
                {'production': ['NAME', 'COLON',
                                'ProductionRuleRHS', 'SEMICOLON']},
                {'production': ['NAME', 'OPENCURLY',
                                'ProdMetaDatas', 'CLOSEDCURLY', 'COLON',
                                'ProductionRuleRHS', 'SEMICOLON']},
            ]
        },
        'ProductionRuleRHS': {
            'modifiers': ['left', 5],
            'action': 'collect_sep',
            'productions': [
                {'production': ['ProductionRuleRHS', 'OR', 'Production']},
                {'production': ['Production']},
            ]
        },
        'Production': {
            'productions': [
                {'production': ['Assignments']},
                {'production': ['Assignments',
                                'OPENCURLY', 'ProdMetaDatas', 'CLOSEDCURLY']},
            ]
        },
        'TerminalRules': {
            'action': 'collect',
            'productions': [
                {'production': ['TerminalRules', 'TerminalRuleWithAction']},
                {'production': ['TerminalRuleWithAction']},
            ]
        },
        'TerminalRuleWithAction': {
            'action': 'rule_with_action',
            'productions': [
                {'production': ['ACTION', 'TerminalRule']},
                {'production': ['TerminalRule']},
            ]
        },
        'TerminalRule': {
            'modifiers': ['left', 15],
            'productions': [
                {'production': ['NAME', 'COLON', 'Recognizer', 'SEMICOLON']},
                {'production': ['NAME', 'COLON', 'SEMICOLON'],
                 'action': 'terminal_rule_empty'},
                {'production': ['NAME', 'COLON', 'Recognizer',
                                'OPENCURLY', 'TermMetaDatas', 'CLOSEDCURLY',
                                'SEMICOLON']},
                {'production': ['NAME', 'COLON',
                                'OPENCURLY', 'TermMetaDatas', 'CLOSEDCURLY',
                                'SEMICOLON'],
                 'action': 'terminal_rule_empty'},
            ]
        },
        'ProdMetaData': {
            'action': 'meta_data_bool',
            'productions': [
                {'production': ['LEFT']},
                {'production': ['REDUCE']},
                {'production': ['RIGHT']},
                {'production': ['SHIFT']},
                {'production': ['DYNAMIC']},
                {'production': ['NOPS']},
                {'production': ['PS']},
                {'production': ['GREEDY']},
                {'production': ['NOGREEDY']},
                {'production': ['NOPSE']},
                {'production': ['PSE']},
                {'production': ['INT'], 'action': 'meta_data_priority'},
                {'production': ['ACTION'], 'action': 'pass_single'},
                {'production': ['UserMetaData'], 'action': 'pass_single'},
            ]
        },
        'ProdMetaDatas': {
            'action': 'collect_sep',
            'productions': [
                {
                    'modifiers': ['left'],
                    'production': ['ProdMetaDatas', 'COMMA', 'ProdMetaData']
                },
                {'production': ['ProdMetaData']}
            ]
        },
        'TermMetaData': {
            'action': 'meta_data_bool',
            'productions': [
                {'production': ['PREFER']},
                {'production': ['_KEYWORD']},
                {'production': ['FINISH']},
                {'production': ['NOFINISH']},
                {'production': ['DYNAMIC']},
                {'production': ['INT'], 'action': 'meta_data_priority'},
                {'production': ['UserMetaData'], 'action': 'pass_single'},
            ]
        },
        'TermMetaDatas': {
            'action': 'collect_sep',
            'productions': [
                {'production': ['TermMetaDatas', 'COMMA', 'TermMetaData']},
                {'production': ['TermMetaData']},
            ]
        },
        'UserMetaData': {
            'productions': [
                {'production': ['NAME', 'COLON', 'Const']},
            ]
        },
        'Const': {
            'productions': [
                {'production': ['INT']},
                {'production': ['FLOAT']},
                {'production': ['BOOL']},
                {'production': ['STR']},
            ]
        },
        'Assignment': {
            'productions': [
                {'production': ['PlainAssignment']},
                {'production': ['BoolAssignment']},
                {'production': ['GSymbolReference']},
            ]
        },
        'Assignments': {
            'action': 'collect',
            'productions': [
                {'production': ['Assignments', 'Assignment']},
                {'production': ['Assignment']},
            ]
        },
        'PlainAssignment': {
            'action': 'pass_nochange',
            'productions': [
                {'production': ['NAME', 'EQUAL', 'GSymbolReference']},
            ]
        },
        'BoolAssignment': {
            'action': 'pass_nochange',
            'productions': [
                {'production': ['NAME', 'BOOLEQUAL', 'GSymbolReference']},
            ]
        },
        'GSymbolReference': {
            'productions': [
                {'production': ['GSymbol', 'OptRepOperator']},
            ]
        },
        'OptRepOperator': {
            'productions': [
                {'production': ['RepOperatorZero']},
                {'production': ['RepOperatorOne']},
                {'production': ['RepOperatorOptional']},
                {'production': ['EMPTY']},
            ]
        },
        'RepOperatorZero': {
            'productions': [
                {'production': ['ASTERISK', 'OptRepModifiersExp']},
            ]
        },
        'RepOperatorOne': {
            'productions': [
                {'production': ['PLUS', 'OptRepModifiersExp']},
            ]
        },
        'RepOperatorOptional': {
            'productions': [
                {'production': ['QUESTION', 'OptRepModifiersExp']},
            ]
        },
        'OptRepModifiersExp': {
            'productions': [
                {'production': ['OPENSQUARED', 'OptRepModifiers',
                                'CLOSEDSQUARED'],
                 'action': 'pass_inner'},
                {'production': ['EMPTY']},
            ]
        },
        'OptRepModifiers': {
            'action': 'collect_sep',
            'productions': [
                {'production': ['OptRepModifiers', 'COMMA', 'OptRepModifier']},
                {'production': ['OptRepModifier']},
            ]
        },
        'OptRepModifier': {
            'productions': [
                {'production': ['NAME']},
            ]
        },
        'GSymbol': {
            'productions': [
                {'production': ['NAME']},
                {'production': ['STR'], 'action': 'inline_terminal'},
            ]
        },
        'Recognizer': {
            'productions': [
                {'production': ['STR'], 'action': 'RecognizerStr'},
                {'production': ['REGEX'], 'action': 'pass_single'},
            ]
        },

        # Support for Layout
        'Layout': {
            'productions': [
                {'production': ['LayoutItem']},
                {'production': ['Layout', 'LayoutItem']},
            ]
        },
        'LayoutItem': {
            'productions': [
                {'production': ['WS']},
                {'production': ['Comment']},
                {'production': ['EMPTY']},
            ]
        },
        'Comment': {
            'productions': [
                {'production': ['COMMENTOPEN', 'Corncs', 'COMMENTCLOSE']},
                {'production': ['COMMENTLINE']},
            ]
        },
        'Corncs': {
            'productions': [
                {'production': ['Cornc']},
                {'production': ['Corncs', 'Cornc']},
                {'production': ['EMPTY']},
            ]
        },
        'Cornc': {
            'productions': [
                {'production': ['Comment']},
                {'production': ['NOTCOMMENT']},
                {'production': ['WS']},
            ]
        },
    },


    'terminals': {
        'TERMINALS': _('terminals'),
        'IMPORT': _('import'),
        'AS': _('as'),
        'COMMA': _(','),
        'COLON': _(':'),
        'SEMICOLON': _(';'),
        'OPENCURLY': _('{'),
        'CLOSEDCURLY': _('}'),
        'OPENSQUARED': _('['),
        'CLOSEDSQUARED': _(']'),
        'OR': _('|'),
        'EQUAL': _('='),
        'BOOLEQUAL': _('?='),
        'ASTERISK': _('*'),
        'PLUS': _('+'),
        'QUESTION': _('?'),
        'NAME': _(r'/[a-zA-Z_][a-zA-Z0-9_\.]*/'),
        'REGEX': _(r'/\/(\\.|[^\/\\])*\//'),
        'ACTION': _(r'/@[a-zA-Z0-9_]+/'),
        'INT': _(r'/\d+/'),
        'FLOAT': _(r'/[+-]?(\d+\.\d*|\.\d+)([eE][+-]?\d+)?(?<=[\w\.])(?![\w\.])/'),  # noqa
        'BOOL': _(r'/true|false/'),
        'STR': _(r'''/(?s)('[^'\\]*(?:\\.[^'\\]*)*')|("[^"\\]*(?:\\.[^"\\]*)*")/'''),  # noqa
        'COMMENTOPEN': _('/*'),
        'COMMENTCLOSE': _('*/'),
        'COMMENTLINE': _(r'/\/\/.*/'),
        'NOTCOMMENT': _(r'/((\*[^\/])|[^\s*\/]|\/[^\*])+/'),
        'WS': _(r'/\s+/'),
        'LEFT': _('left'),
        'REDUCE': _('reduce'),
        'RIGHT': _('right'),
        'SHIFT': _('shift'),
        'DYNAMIC': _('dynamic'),
        'NOPS': _('nops'),
        'PS': _('ps'),
        'GREEDY': _('greedy'),
        'NOGREEDY': _('nogreedy'),
        'NOPSE': _('nopse'),
        'PSE': _('pse'),
        'FINISH': _('finish'),
        'NOFINISH': _('nofinish'),
        'PREFER': _('prefer'),
        '_KEYWORD': _('keyword'),
    }
}


class PGGrammarActions(Actions):
    """
    Actions for parglare files
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.inline_terminals = {}

    def PGFile(self, nodes):
        rules_idx = [0, 1, 0, 1, None][self.prod_idx]
        imports_idx = [None, 0, None, 0, None][self.prod_idx]
        terminals_idx = [None, None, 2, 3, 1][self.prod_idx]

        pgfile = {}
        if rules_idx is not None:
            pgfile['start'] = nodes[rules_idx][0][0]
        if imports_idx is not None:
            pgfile.update(nodes[imports_idx])
        if rules_idx is not None:
            rules = {}
            rule_tuples = nodes[rules_idx]
            for rule_name, rule in rule_tuples:
                if rule_name not in rules:
                    rules[rule_name] = {'productions': []}
                rules[rule_name]['productions'].extend(rule['productions'])
                del rule['productions']
                if 'action' in rule:
                    if 'action' in rules[rule_name]:
                        raise GrammarError(
                            location=Location(),
                            message='Multiple actions defined for rule "{}".'
                            .format(rule_name))
                rules[rule_name].update(rule)
            pgfile['rules'] = rules
        if terminals_idx is not None or self.inline_terminals:
            terminals = {}
            if terminals_idx:
                term_tuples = nodes[terminals_idx]
                for name, term in term_tuples:
                    if name in terminals:
                        raise GrammarError(
                            location=Location(),
                            message='Multiple definitions '
                            'of terminal rule "{}"'.format(name))
                    terminals[name] = term

            for inline_term in self.inline_terminals:
                if inline_term in terminals:
                    raise GrammarError(
                        location=Location(),
                        message='Inline terminal with the name '
                        '"{}" already exists.'.format(inline_term))
                terminals[inline_term] = self.inline_terminals[inline_term]
            pgfile.update({'terminals': terminals})

        return pgfile

    def Import(self, nodes):
        return

    def rule_with_action(self, nodes):
        prod_rule = nodes[-1]
        if len(nodes) > 1:
            action = nodes[0]
            prod_rule[1][action[0]] = action[1]
        return prod_rule

    def extract_modifiers(self, target):
        """
        Extract built-in modifiers (e.g. disambiguation rules) and action from
        meta-data of rules, productions, terminals.
        """
        modifiers = []
        meta = target['meta']
        for m in list(meta):
            if m == 'prior':
                modifiers.append(meta[m])
                del meta[m]
            elif m == 'action':
                target['action'] = meta[m]
                del meta[m]
            elif m in MODIFIERS:
                modifiers.append(m)
                del meta[m]
        if modifiers:
            target['modifiers'] = modifiers
        if not target['meta']:
            del target['meta']

    def ProductionRule(self, nodes):
        rule = {'productions': nodes[-2]}
        if len(nodes) > 4:
            # We have meta-data
            rule['meta'] = dict(nodes[2])
            self.extract_modifiers(rule)
        return nodes[0], rule

    def Production(self, nodes):
        p = nodes[0]
        assignments = {}
        for idx, assignment in enumerate(p):
            if type(assignment) is list:
                # We have an assignment
                assignments[assignment[0]] = {'op': assignment[1],
                                              'rhs_idx': idx}
                p[idx] = assignment[2]
        prod = {'production': p,
                'location': Location(self.context)}
        if len(nodes) > 1:
            prod['meta'] = dict(nodes[2])
            self.extract_modifiers(prod)
        if assignments:
            prod['assignments'] = assignments
        return prod

    def TerminalRule(self, nodes):
        term_rule = {'recognizer': nodes[2],
                     'location': Location(self.context)}
        if len(nodes) > 4:
            term_rule['meta'] = dict(nodes[4])
            self.extract_modifiers(term_rule)
        return nodes[0], term_rule

    def terminal_rule_empty(self, nodes):
        term_rule = {'recognizer': None}
        if len(nodes) > 3:
            term_rule['meta'] = dict(nodes[3])
            self.extract_modifiers(term_rule)
        return nodes[0], term_rule

    def meta_data_bool(self, nodes):
        return (nodes[0], True)

    def meta_data_priority(self, nodes):
        return ('prior', nodes[0])

    def UserMetaData(self, nodes):
        return (nodes[0], nodes[2])

    def GSymbolReference(self, nodes):
        symbol_ref, rep_op = nodes

        if rep_op:
            symbol_ref = {'symbol': symbol_ref}
            modifiers = rep_op[1]
            rep_op = rep_op[0]

            if modifiers:
                symbol_ref['modifiers'] = modifiers

            symbol_ref['mult'] = rep_op

        return symbol_ref

    def RecognizerStr(self, nodes):
        return nodes[0].replace(r'\"', '"')\
                       .replace(r"\'", "'")\
                       .replace(r"\\", "\\")\
                       .replace(r"\n", "\n")\
                       .replace(r"\t", "\t")

    def inline_terminal(self, nodes):
        symbol = nodes[0]
        if symbol not in self.inline_terminals:
            self.inline_terminals[symbol] = {'recognizer': symbol}
        return symbol

    def ACTION(self, value):
        return ('action', value[1:])

    def STR(self, value):
        return value[1:-1].replace(r"\\", "\\").replace(r"\'", "'")

    def INT(self, value):
        return int(value)

    def FLOAT(self, value):
        return float(value)

    def BOOL(self, value):
        return value and value.lower() == 'true'


pg_parser_grammar = None
pg_parser_table = None


def get_grammar_parser(debug=False, debug_colors=False):
    """
    Constructs and returns a new instance of the Parglare grammar parser.
    Cache grammar and LALR table to speed up future calls.
    """
    global pg_parser_grammar, pg_parser_table
    if pg_parser_grammar is None:
        from parglare.lang import pg_grammar
        pg_parser_grammar = Grammar.from_struct(pg_grammar, debug=debug,
                                                debug_colors=debug_colors)
    if pg_parser_table is None:
        from parglare.tables import create_table
        pg_parser_table = create_table(pg_parser_grammar)

    from parglare import Parser
    from parglare.lang import PGGrammarActions
    return Parser(pg_parser_grammar, actions=PGGrammarActions(),
                  table=pg_parser_table, debug=debug,
                  debug_colors=debug_colors)
