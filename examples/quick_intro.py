from parglare import Parser, Grammar, Actions
from operator import add, sub, mul, truediv, pow

grammar = r"""
@op E: E '+' E  {left, 1}
     | E '-' E  {left, 1}
     | E '*' E  {left, 2}
     | E '/' E  {left, 2}
     | E '^' E  {right, 3}
     | '(' E ')' {@pass_inner}
     | number {@pass_single};

terminals
number: /\d+(\.\d+)?/;
"""


class MyActions(Actions):
    def op(self, n):
        opfunc = {
            '+': add,
            '-': sub,
            '*': mul,
            '/': truediv,
            '^': pow
        }[n[1]]
        return opfunc(n[0], n[2])

    def number(self, n):
        return float(n)


g = Grammar.from_string(grammar)
parser = Parser(g, debug=True, actions=MyActions())

result = parser.parse("34 + 4.6 / 2 * 4^2^2 + 78")

print("Result = ", result)

# Output
# -- Debugging/tracing output with detailed info about grammar, productions,
# -- terminals and nonterminals, DFA states, parsing progress,
# -- and at the end of the output:
# Result = 700.8
