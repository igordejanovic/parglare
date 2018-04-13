"""Calculate the molecular weight given a molecular formula

Parse the formula using parglare.
This example is based on the example from
PLY compared with pyparsing and ANTLR by Andrew Dalke
http://www.dalkescientific.com/writings/diary/archive/2007/11/03/antlr_java.html
"""
from parglare import Grammar, Parser

grammar = r"""
mw: EMPTY | formula;
formula: species | formula species;
species: ATOM DIGITS | ATOM;

terminals
DIGITS: /\d+/;
"""

mw_table = {
    'H': 1.00794,
    'C': 12.001,
    'Cl': 35.453,
    'O': 15.999,
    'S': 32.06,
}

atom_names = sorted(
    mw_table.keys(),
    key=lambda symbol: (symbol[0], -len(symbol), symbol))

# Creates a pattern like:  Cl|C|H|O|S
atom_pattern = "|".join(atom_names)

# Extend grammar definition with the ATOM rule
grammar += '\nATOM: /{}/;'.format(atom_pattern)

actions = {
    'mw': [lambda _, __: 0.0,
           lambda _, nodes: nodes[0]],
    'formula': [lambda _, nodes: nodes[0],
                lambda _, nodes: nodes[0] + nodes[1]],
    'species': [lambda _, nodes: nodes[0] * nodes[1],
                lambda _, nodes: nodes[0]],
    'ATOM': lambda _, value: mw_table[value],
    'DIGITS': lambda _, value: int(value)
}

parser = Parser(Grammar.from_string(grammar), actions=actions)


def calculate_mw(formula):
    return parser.parse(formula)
