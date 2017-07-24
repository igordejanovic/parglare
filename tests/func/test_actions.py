import pytest  # noqa
from parglare.parser import Parser, NodeNonTerm
from .expression_grammar_numbers import get_grammar


def get_actions():

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

    actions = {
        "number": lambda _, value: float(value),
        # Check action for each alternative
        "E": [sum_act, pass_act],
        # Check symbol-level action
        "T": t_act,
        # Again action for each alternative
        "F": [parenthesses_act, pass_act]
    }

    return actions


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
    p = Parser(grammar)

    result = p.parse("""34.7+78*34 +89+
    12.223*4""")

    assert type(result) is NodeNonTerm

    assert p.call_actions(result, get_actions()) == \
        34.7 + 78 * 34 + 89 + 12.223 * 4
