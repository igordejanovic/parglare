from __future__ import unicode_literals
import pytest  # noqa
from parglare import Parser, NodeNonTerm, Actions
from ..grammar.expression_grammar_numbers import get_grammar


def get_actions():

    class MyActions(Actions):

        def NUMBER(self, value):
            return float(value)

        def E(self, nodes):
            return [self.sum_act, self.act][self.prod_idx](nodes)

        def sum_act(self, nodes):
            return nodes[0] + nodes[2]

        def T(self, nodes):
            if len(nodes) == 3:
                return nodes[0] * nodes[2]
            else:
                return nodes[0]

        def F(self, nodes):
            return [self.parenthesses_act, self.act][self.prod_idx](nodes)

        def parenthesses_act(self, nodes):
            return nodes[1]

        def act(self, nodes):
            return nodes[0]

    return MyActions()


def test_actions():

    grammar = get_grammar()
    p = Parser(grammar, actions=get_actions())

    result = p.parse("""34.7+78*34 +89+
    12.223*4""")

    assert result == 34.7 + 78 * 34 + 89 + 12.223 * 4


def test_actions_manual():
    """
    Actions may be called as a separate step.
    """

    grammar = get_grammar()
    p = Parser(grammar, build_tree=True, actions=get_actions())

    result = p.parse("""34.7+78*34 +89+
    12.223*4""")

    assert type(result) is NodeNonTerm

    assert p.call_actions(result) == \
        34.7 + 78 * 34 + 89 + 12.223 * 4
