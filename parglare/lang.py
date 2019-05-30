"""
This module defines the parglare grammar language using parglare internal
DSL specification.

"""

from parglare.recognizers import StringRecognizer, RegExRecognizer
from parglare.actions import ParglareActions


def _(s, regex=False):
    """
    Returns a terminal definition
    """
    if regex:
        {'recognizer': r'/{}/'.format(s)}
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
                                'ProductionRuleWithAction']},
                {'production': ['ProductionRuleWithAction'],
                 'action': 'pass_single'},
            ]
        },
        'ProductionRuleWithAction': {
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
            'action': 'collect',
            'productions': [
                {'production': ['TerminalRules', 'TerminalRuleWithAction']},
                {'production': ['TerminalRuleWithAction']},
            ]
        },
        'TerminalRuleWithAction': {
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
                 'action': 'TerminalRuleEmptyBody'},
                {'production': ['NAME', 'COLON', 'Recognizer',
                                'OPENCURLY', 'TermMetaDatas', 'CLOSEDCURLY',
                                'SEMICOLON']},
                {'production': ['NAME', 'COLON',
                                'OPENCURLY', 'TermMetaDatas', 'CLOSEDCURLY',
                                'SEMICOLON'],
                 'action': 'TerminalRuleEmptyBody'},
            ]
        },
        'ProdMetaData': {
            'productions': [
                {'production': ['LEFT']},
                {'production': ['REDUCE']},
                {'production': ['RIGHT']},
                {'production': ['SHIFT']},
                {'production': ['DYNAMIC']},
                {'production': ['NOPS']},
                {'production': ['NOPSE']},
                {'production': ['INT']},
                {'production': ['UserMetaData']},
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
            'productions': [
                {'production': ['PREFER']},
                {'production': ['FINISH']},
                {'production': ['NOFINISH']},
                {'production': ['DYNAMIC']},
                {'production': ['INT']},
                {'production': ['UserMetaData']},
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
                                'CLOSEDSQUARED']},
                {'production': ['EMPTY']},
            ]
        },
        'OptRepModifiers': {
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
                {'production': ['NAME'], 'action': 'GSymbolName'},
                {'production': ['STR'], 'action': 'GSymbolStr'},
            ]
        },
        'Recognizer': {
            'productions': [
                {'production': ['STR'], 'action': 'RecognizerStr'},
                {'production': ['REGEX'], 'action': 'RecognizerRegex'},
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
        'NAME': _(r'/[a-zA-Z_][a-zA-Z0-9_\.]*/', True),
        'REGEX': _(r'\/(\\.|[^\/\\])*\/', True),
        'ACTION': _(r'/@[a-zA-Z0-9_]+/', True),
        'INT': _(r'\d+', True),
        'FLOAT': _(r'[+-]?(\d+\.\d*|\.\d+)([eE][+-]?\d+)?(?<=[\w\.])(?![\w\.])', True),  # noqa
        'BOOL': _(r'true|false', True),
        'STR': _(r'''(?s)('[^'\\]*(?:\\.[^'\\]*)*')|'''
                 r'''("[^"\\]*(?:\\.[^"\\]*)*")''', True),
        'COMMENTOPEN': _('/*'),
        'COMMENTCLOSE': _('*/'),
        'COMMENTLINE': _(r'\/\/.*', True),
        'NOTCOMMENT': _(r'/((\*[^\/])|[^\s*\/]|\/[^\*])+/', True),
        'WS': _(r'/\s+/', True),
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

    def pgimport(self, nodes):
        pass

    def PGFile(self, nodes):
        pass

    def ProductionRules(self, nodes):
        pass

    def ProductionRuleWithAction(self, nodes):
        pass

    def ProductionRule(self, nodes):
        pass

    def Production(self, nodes):
        pass

    def TerminalRuleWithAction(self, nodes):
        pass

    def TerminalRule(self, nodes):
        pass

    def TerminalRuleEmptyBody(self, nodes):
        pass

    def Assignment(self, nodes):
        pass

    def GSymbolReference(self, nodes):
        pass

    def GSymbolName(self, nodes):
        pass

    def GSymbolStr(self, nodes):
        pass

    def RecognizerStr(self, nodes):
        value = nodes[0]
        value = value.replace(r'\"', '"')\
                     .replace(r"\'", "'")\
                     .replace(r"\\", "\\")\
                     .replace(r"\n", "\n")\
                     .replace(r"\t", "\t")
        return StringRecognizer(value, ignore_case=self.extra.ignore_case)

    def RecognizerRegex(self, nodes):
        value = nodes[0]
        return RegExRecognizer(value, re_flags=self.extra.re_flags,
                               ignore_case=self.extra.ignore_case)

    def STR(self, value):
        return value[1:-1].replace(r"\\", "\\").replace(r"\'", "'")

    def REGEX(self, value):
        return value[1:-1]

    def INT(self, value):
        return int(value)

    def FLOAT(self, value):
        return float(value)

    def BOOL(self, value):
        return value and value.lower() == 'true'
