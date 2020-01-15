import re
from parglare import Grammar, Parser


def test_issue64():
    g = Grammar.from_string(
        'T: NL* L+ NL* | NL*; terminals L: /.+/; NL: "\n";',
        re_flags=re.MULTILINE)
    Parser(g, consume_input=False, ws=None).parse('\nL1\nL2\n\n')
