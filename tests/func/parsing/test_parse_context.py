# -*- coding: utf-8 -*-
import pytest  # noqa
from parglare import Grammar, Parser
from parglare.actions import pass_single


grammar = r"""
E: E '+' E  {left}
 | number;

terminals
number: /\d+(\.\d+)?/;
"""

called = [False, False]


def act_sum(is_tree):
    def act_sum(context, nodes):
        called[0] = True
        assert context.parser
        assert context.state.symbol.name == 'E'
        assert context.production.symbol.name == 'E'
        assert len(context.production.rhs) == 3
        assert context.layout_content == '   '
        assert context.start_position == 3
        assert context.end_position == 8
        if is_tree:
            # If parse tree is constructed `node` is available on
            # the context.
            assert context.node.is_nonterm() \
                and context.node.symbol.name == 'E'
        else:
            context.node is None

    return act_sum


def act_number(context, value):
    called[1] = True
    value = float(value)
    assert context.symbol.name == 'number'
    if value == 1:
        assert context.start_position == 3
        assert context.end_position == 4
        assert context.layout_content == '   '
    else:
        assert context.start_position == 7
        assert context.end_position == 8
        assert context.layout_content == ' '
    return value


actions = {
    "Result": pass_single,
    "E": [None, pass_single],
    "number": act_number,
}

g = Grammar.from_string(grammar)


def test_parse_context():
    global called
    called = [False, False]

    actions["E"][0] = act_sum(is_tree=False)
    parser = Parser(g, actions=actions)

    parser.parse("   1 + 2  ")

    assert all(called)


def test_parse_context_call_actions():
    """
    Test that valid context attributes are available when calling
    actions using `call_actions`.
    """
    global called
    called = [False, False]

    actions["E"][0] = act_sum(is_tree=True)
    parser = Parser(g, build_tree=True, actions=actions)

    tree = parser.parse("   1 + 2  ")

    parser.call_actions(tree)

    assert all(called)
