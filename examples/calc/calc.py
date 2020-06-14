from parglare import Grammar, Parser
from parglare.actions import pass_inner, pass_single

grammar = r"""
Calc: Assignments E;
Assignments: Assignment | Assignments Assignment | EMPTY;
Assignment: VariableName "=" Number;

E: E "+" E {left, 1}
 | E "-" E {left, 1}
 | E "*" E {left, 2}
 | E "/" E {left, 2}
 | "(" E ")"
 | VariableRef
 | Number
;

VariableRef: VariableName;

terminals
VariableName: /[a-zA-Z_][_a-zA-Z0-9]*/;
Number: /\d+(\.\d+)?/;
"""


# Semantic Actions
def act_assignment(context, nodes):
    """Semantic action for variable assignment."""

    name = nodes[0]
    number = nodes[2]

    if context.extra is None:
        context.extra = {}

    context.extra[name] = number


actions = {
    "Calc": lambda _, nodes: nodes[1],
    "Assignment": act_assignment,
    "E": [lambda _, nodes: nodes[0] + nodes[2],
          lambda _, nodes: nodes[0] - nodes[2],
          lambda _, nodes: nodes[0] * nodes[2],
          lambda _, nodes: nodes[0] / nodes[2],
          pass_inner,
          pass_single,
          pass_single],
    "Number": lambda _, value: float(value),
    "VariableRef": lambda context, nodes: context.extra[nodes[0]],
}


def main(debug=False):
    g = Grammar.from_string(grammar, debug=debug, debug_colors=True)
    parser = Parser(g, actions=actions, debug=debug, debug_colors=True)

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
