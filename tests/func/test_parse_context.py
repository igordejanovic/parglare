import pytest  # noqa
from parglare import Grammar, Parser
from parglare.parser import NodeNonTerm, Context
from parglare.actions import pass_single


grammar = r"""
Result = E EOF;
E = E '+' E  {left}
  | number;
number = /\d+(\.\d+)?/;
"""

called = [False]
node_exists = [False]


def act_sum(context, nodes):
    called[0] = True
    assert context.parser
    assert context.symbol
    assert context.layout_content is not None
    assert context.start_position == 3
    assert context.end_position == 8
    if hasattr(context, 'call_actions'):
        assert type(context.node) is NodeNonTerm \
            and context.node.symbol.name == 'E'
        node_exists[0] = True


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


def test_parse_context_call_actions():
    """
    Test that valid context attributes are available when calling
    actions using `call_actions`.
    """
    called[0] = False

    parser = Parser(g, debug=True)

    tree = parser.parse("   1 + 2  ")
    context = Context()
    context.call_actions = True
    parser.call_actions(tree, actions=actions, context=context)

    assert called[0]
    assert node_exists[0]
