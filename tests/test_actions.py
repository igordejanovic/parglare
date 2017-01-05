import pytest
from parglare.parser import Parser
from .expression_grammar_numbers import get_grammar, E


def test_actions():

    def nodes_sum(position, symbol, nodes):
        if len(nodes) == 3:
            return nodes[0] + nodes[2]
        else:
            return nodes[0]

    def nodes_mul(positon, symbol, nodes):
        if len(nodes) == 3:
            return nodes[0] * nodes[2]
        else:
            return nodes[0]

    def nodes_factor(position, symbol, nodes):
        if len(nodes) == 3:
            return nodes[1]
        else:
            return nodes[0]

    grammar = get_grammar()
    actions = {"number": lambda position, symbol, value: float(value),
               "E": nodes_sum,
               "T": nodes_mul,
               "F": nodes_factor
    }

    p = Parser(grammar, E, actions=actions)

    result = p.parse("""34.7+78*34 +89+
    12.223*4""")

    assert result == 34.7 + 78 * 34 + 89 + 12.223 * 4
