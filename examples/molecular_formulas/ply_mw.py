"""Calculate the molecular weight given a molecular formula

Parse the formula using PLY.
"""
# ply_mw.py

from ply import lex
from ply.lex import TOKEN
import ply.yacc as yacc


class ParseError(Exception):
    def __init__(self, msg, offset):
        self.msg = msg
        self.offset = offset

    def __repr__(self):
        return "ParseError(%r, %r)" % (self.msg, self.offset)

    def __str__(self):
        return "%s at position %s" % (self.msg, self.offset + 1)


# Define the lexer

tokens = (
    "ATOM",
    "DIGITS",
)

mw_table = {
    'H': 1.00794,
    'C': 12.001,
    'Cl': 35.453,
    'O': 15.999,
    'S': 32.06,
}


# I don't want to duplicate the atom names so extract the
# keys to make the lexer pattern.

# Sort order is:
#   - alphabetically on first character, to make it easier
# for a human to look at and debug any problems
#
#   - then by the length of the symbol; two letters before 1
# Needed because Python's regular expression matcher
# uses "first match" not "longest match" rules.
# For example, "C|Cl" matches only the "C" in "Cl"
# The "-" in "-len(symbol)" is a trick to reverse the sort order.
#
#   - then by the full symbol, to make it easier for people

# (This is more complicated than needed; it's to show how
# this approach can scale to all 100+ known and named elements)

atom_names = sorted(
    mw_table.keys(),
    key=lambda symbol: (symbol[0], -len(symbol), symbol))

# Creates a pattern like:  Cl|C|H|O|S
atom_pattern = "|".join(atom_names)


# Use a relatively new PLY feature to set the __doc__
# string based on a Python variable.
@TOKEN(atom_pattern)
def t_ATOM(t):
    t.value = mw_table[t.value]
    return t


def t_DIGITS(t):
    r"\d+"
    t.value = int(t.value)
    return t


def t_error(t):
    raise ParseError("unknown character", t.lexpos)


lexer = lex.lex()

# Here's an example of using the lexer

# data = "H2SO4"
#
# lex.input(data)
#
# for tok in iter(lex.token, None):
#     print tok

# Define the grammar


# The molecular weight of "" is 0.0
def p_mw_empty(p):
    "mw : "
    p[0] = 0.0


def p_mw_formula(p):
    "mw : formula"
    p[0] = p[1]


def p_first_species_term(p):
    "formula : species"
    p[0] = p[1]


def p_species_list(p):
    "formula : formula species"
    p[0] = p[1] + p[2]


def p_species(p):
    "species : ATOM DIGITS"
    p[0] = p[1] * p[2]


def p_species_default(p):
    "species : ATOM"
    p[0] = p[1]


def p_error(p):
    raise ParseError("unexpected character", p.lexpos)


parser = yacc.yacc()

# Work around a problem in PLY 2.3 where the first parse does not
# allow a "".  I reported it to the ply mailing list on 2 November.
# This guarantees the first parse will never be "" :)
parser.parse("C")


# Calculate molecular weight
def calculate_mw(formula):
    return parser.parse(formula, lexer=lexer)
