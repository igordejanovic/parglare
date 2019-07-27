from __future__ import unicode_literals
from parglare import Grammar, Parser, Actions
from operator import add, sub, mul, truediv

grammar = r"""
@pass_inner Calc: Assignments E;
Assignments: Assignment | Assignments Assignment | EMPTY;
Assignment: VariableName "=" Number;

@op E: E "+" E {left, 1}
     | E "-" E {left, 1}
     | E "*" E {left, 2}
     | E "/" E {left, 2}
     | "(" E ")" {@pass_inner}
     | VariableRef {@pass_single}
     | Number {@pass_single}
;

VariableRef: VariableName;

terminals
VariableName: /[a-zA-Z_][_a-zA-Z0-9]*/;
Number: /\d+(\.\d+)?/;
"""


class MyActions(Actions):

    # Semantic Actions
    def Assignment(self, n):
        """Semantic action for variable assignment."""

        name = n[0]
        number = n[2]

        if self.context.extra is None:
            self.context.extra = {}

        self.context.extra[name] = number

    def op(self, n):
        opfunc = {
            '+': add,
            '-': sub,
            '*': mul,
            '/': truediv,
        }[n[1]]
        return opfunc(n[0], n[2])

    def Number(self, n):
        return float(n)

    def VariableRef(self, n):
        return self.context.extra[n[0]]


def main(debug=False):
    g = Grammar.from_string(grammar, debug=debug, debug_colors=True)
    parser = Parser(g, actions=MyActions(), debug=debug, debug_colors=True)

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
