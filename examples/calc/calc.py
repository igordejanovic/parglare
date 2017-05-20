from __future__ import unicode_literals
from parglare import Grammar, Parser

grammar = """
Calc = Assignments E;
Assignments = Assignment | Assignments Assignment | EMPTY;
Assignment = VariableName "=" Number;

E = E "+" E {left, 1}
  | E "-" E {left, 1}
  | E "*" E {left, 2}
  | E "/" E {left, 2}
  | "(" E ")"
  | VariableRef
  | Number
;

VariableRef = VariableName;

VariableName = /[a-zA-Z_][_a-zA-Z0-9]*/;
Number = /\d+(\.\d+)?/;
"""


# Semantic Actions
def act_assignment(context, nodes):
    """Semantic action for variable assignment."""

    name = nodes[0]
    number = nodes[2]

    if not hasattr(context, 'variables'):
        context.variables = {}

    context.variables[name] = number


actions = {
    "Calc": lambda _, nodes: nodes[1],
    "Assignment": act_assignment,
    "E:1": lambda _, nodes: nodes[0] + nodes[2],
    "E:2": lambda _, nodes: nodes[0] - nodes[2],
    "E:3": lambda _, nodes: nodes[0] * nodes[2],
    "E:4": lambda _, nodes: nodes[0] / nodes[2],
    "E:5": lambda _, nodes: nodes[1],
    "E:6": lambda _, nodes: nodes[0],
    "E:7": lambda _, nodes: nodes[0],
    "Number": lambda _, value: float(value),
    "VariableName": lambda _, value: value,
    "VariableRef": lambda context, nodes: context.variables[nodes[0]],
}


def main(debug=False):
    g = Grammar.from_string(grammar)
    parser = Parser(g, actions=actions)

    input_str = """
    a = 5
    b = 10

    a + 56.4 / 3 * 5 - b + 8 * 3
    """

    res = parser.parse(input_str)

    assert res == 5. + 56.4 / 3 * 5 - 10 + 8 * 3
    print("Input:\n", input_str)
    print("Result = ", res)


if __name__ == "__main__":
    main(debug=True)
