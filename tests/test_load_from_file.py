import pytest
import os
from parglare import Grammar, Parser


def test_load_from_file():

    def act_assignment(context, nodes):
        name = nodes[0]
        number = nodes[2]

        if not hasattr(context, 'variables'):
            context.variables = {}

        context.variables[name] = number

    actions = {
        "Calc": lambda _, nodes: nodes[1],
        "Assignment": act_assignment,
        "E:0": lambda _, nodes: nodes[0] + nodes[2],
        "E:1": lambda _, nodes: nodes[0] - nodes[2],
        "E:2": lambda _, nodes: nodes[0] * nodes[2],
        "E:3": lambda _, nodes: nodes[0] / nodes[2],
        "E:4": lambda _, nodes: nodes[1],
        "E:5": lambda _, nodes: nodes[0],
        "E:6": lambda _, nodes: nodes[0],
        "Number": lambda _, value: float(value),
        "VariableName": lambda _, value: value,
        "VariableRef": lambda context, nodes: context.variables[nodes[0]],
    }

    grammar = Grammar.from_file(os.path.join(
        os.path.dirname(__file__), 'calc.pg'))
    parser = Parser(grammar, actions=actions, debug=True)

    res = parser.parse("""
    a = 5
    b = 10

    56.4 + a / 3 * 5 - b + 8 * 3
    """)

    assert res == 56.4 + 5 / 3 * 5 - 10 + 8 * 3
