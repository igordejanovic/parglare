import pytest  # noqa
from parglare.parser import Parser
from .expression_grammar_numbers import get_grammar


def test_actions():

    def sum_act(_, nodes):
        return nodes[0] + nodes[2]

    def t_act(_, nodes):
        if len(nodes) == 3:
            return nodes[0] * nodes[2]
        else:
            return nodes[0]

    def parenthesses_act(_, nodes):
        return nodes[1]

    def pass_act(_, nodes):
        return nodes[0]

    grammar = get_grammar()
    actions = {
        "number": lambda _, value: float(value),
        # Check action for each alternative
        "E:1": sum_act,
        "E:2": pass_act,
        # Check symbol-level action
        "T": t_act,
        # Again action for each alternative
        "F:1": parenthesses_act,
        "F:2": pass_act
    }

    p = Parser(grammar, actions=actions)

    result = p.parse("""34.7+78*34 +89+
    12.223*4""")

    assert result == 34.7 + 78 * 34 + 89 + 12.223 * 4
