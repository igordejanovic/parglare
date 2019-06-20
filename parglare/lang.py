"""
This module defines the parglare grammar language using parglare internal
DSL specification.

"""
from parglare.actions import ParglareActions
from parglare.grammar import (Grammar, MULT_ZERO_OR_MORE, MULT_ONE_OR_MORE,
                              MULT_OPTIONAL)


def _(s):
    """
    Returns a terminal definition
    """
    return {'recognizer': s}


pg_grammar = {
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
            'action': 'pgimport',
            'productions': [
                {'production': ['IMPORT', 'STR', 'SEMICOLON']},
                {'production': ['IMPORT', 'STR', 'AS', 'NAME', 'SEMICOLON']},
            ]
        },
        'ProductionRules': {
            'productions': [
                {'production': ['ProductionRules',
                                'ProductionRuleWithAction'],
                 'action': 'rules'},
                {'production': ['ProductionRuleWithAction'],
                 'action': 'pass_single'},
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
            'left': True,
            'priority': 5,
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
            'productions': [
                {'production': ['TerminalRules', 'TerminalRuleWithAction'],
                 'action': 'rules'},
                {'production': ['TerminalRuleWithAction'],
                 'action': 'pass_single'},
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
            'left': True,
            'priority': 15,
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
                {'production': ['NOPSE']},
                {'production': ['INT'], 'action': 'meta_data_priority'},
                {'production': ['UserMetaData'], 'action': 'pass_single'},
            ]
        },
        'ProdMetaDatas': {
            'action': 'collect_sep',
            'productions': [
                {
                    'left': True,
                    'production': ['ProdMetaDatas', 'COMMA', 'ProdMetaData']
                },
                {'production': ['ProdMetaData']}
            ]
        },
        'TermMetaData': {
            'action': 'meta_data_bool',
            'productions': [
                {'production': ['PREFER']},
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
            'productions': [
                {'production': ['NAME', 'EQUAL', 'GSymbolReference']},
            ]
        },
        'BoolAssignment': {
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
            'action': 'pass_single',
            'productions': [
                {'production': ['ASTERISK', 'OptRepModifiersExp']},
            ]
        },
        'RepOperatorOne': {
            'action': 'pass_single',
            'productions': [
                {'production': ['PLUS', 'OptRepModifiersExp']},
            ]
        },
        'RepOperatorOptional': {
            'action': 'pass_single',
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
                {'production': ['STR']},
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
        'NOPSE': _('nopse'),
        'PREFER': _('prefer'),
        'FINISH': _('finish'),
        'NOFINISH': _('nofinish'),
    }
}


class PGGrammarActions(ParglareActions):
    """
    Actions for parglare files
    """

    def PGFile(self, nodes):
        return [
            {'rules': nodes[0]},
            {'imports': nodes[0],
             'rules': nodes[1]},
            {'rules': nodes[0],
             'terminals': nodes[2]},
            {'imports': nodes[0],
             'rules': nodes[1],
             'terminals': nodes[3]},
            {'terminals': nodes[1]}][self.prod_idx]

    def Import(self, nodes):
        return

    def rule_with_action(self, nodes):
        prod_rule = nodes[-1]
        if len(nodes) > 1:
            prod_rule['action'] = nodes[0][1:]
        return prod_rule

    def ProductionRule(self, nodes):
        prods = {'productions': nodes[-2]}
        if len(nodes) > 4:
            # We have meta-data
            prods['meta'] = nodes[2]
        return {nodes[0]: prods}

    def rules(self, nodes):
        """
        Collect and merge rules. If two rules with the same name
        define same meta-data or both defined action report error.
        """
        rules, rule = nodes
        if rules is None:
            rules = {}
        rule_name, rule = list(rule.items())[0]
        if rule_name in rules:
            # TODO: Merge and report error
            pass
        rules[rule_name] = rule
        return rules

    def Production(self, nodes):
        prod = {'production': nodes[0]}
        if len(nodes) > 1:
            prod['meta'] = nodes[2]
        return prod

    def TerminalRule(self, nodes):
        term_rule = {'recognizer': nodes[2]}
        if len(nodes) > 4:
            term_rule['meta'] = nodes[4]
        return {nodes[0]: term_rule}

    def terminal_rule_empty(self, nodes):
        term_rule = {'recognizer': None}
        if len(nodes) > 3:
            term_rule['meta'] = nodes[3]
        return {nodes[0]: term_rule}

    def meta_data_bool(self, nodes):
        return {nodes[0]: True}

    def meta_data_priority(self, nodes):
        return {'priority': nodes[0]}

    def UserMetaData(self, nodes):
        return {nodes[0]: nodes[2]}

    def Assignment(self, nodes):
        return nodes[0]

    def PlainAssignment(self, nodes):
        return nodes[0]

    def BoolAssignment(self, nodes):
        return nodes[0]

    def GSymbolReference(self, nodes):
        symbol_ref, rep_op = nodes

        if rep_op:
            symbol_ref = {'symbol': symbol_ref}
            rep_op = rep_op[0]
            sep = rep_op[1] if len(rep_op) > 1 else None

            if rep_op == '*':
                multiplicity = MULT_ZERO_OR_MORE
            elif rep_op == '+':
                multiplicity = MULT_ONE_OR_MORE
            else:
                multiplicity = MULT_OPTIONAL

            symbol_ref['multiplicity'] = multiplicity
            if sep:
                symbol_ref['separator'] = sep

        return symbol_ref

    def RecognizerStr(self, nodes):
        return nodes[0].replace(r'\"', '"')\
                       .replace(r"\'", "'")\
                       .replace(r"\\", "\\")\
                       .replace(r"\n", "\n")\
                       .replace(r"\t", "\t")

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


def get_grammar_parser():
    """
    Constructs and returns a new instance of the Parglare grammar parser.
    Cache grammar and LALR table to speed up future calls.
    """
    global pg_parser_grammar, pg_parser_table
    if pg_parser_grammar is None:
        from parglare.lang import pg_grammar
        pg_parser_grammar = Grammar.from_struct(pg_grammar)
    if pg_parser_table is None:
        from parglare.tables import create_table
        pg_parser_table = create_table(pg_parser_grammar)

    from parglare import Parser
    from parglare.lang import PGGrammarActions
    return Parser(pg_parser_grammar, actions=PGGrammarActions(),
                  table=pg_parser_table)
