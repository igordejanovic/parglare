import pytest  # noqa
from parglare import Grammar, Parser
from parglare.actions import pass_single


grammar = r"""
Result = E EOF;
E = E '+' E  {left}
  | number;
number = /\d+(\.\d+)?/;
"""

called = [False]


def act_sum(context, nodes):
    called[0] = True
    assert context.parser
    assert context.symbol
    assert context.layout_content is not None
    assert context.start_position == 3
    assert context.end_position == 8


actions = {
    "Result": pass_single,
    "E": [act_sum, pass_single],
    "number": lambda _, value: float(value),
}

g = Grammar.from_string(grammar)


def test_parse_context():
    parser = Parser(g, actions=actions, debug=True)

    parser.parse("   1 + 2  ")

    assert called[0]
