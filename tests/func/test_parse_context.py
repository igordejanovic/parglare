# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import pytest  # noqa
from parglare import Grammar, Parser
from parglare.parser import NodeNonTerm, Context
from parglare.actions import pass_single


grammar = r"""
Result: E EOF;
E: E '+' E  {left}
 | number;

terminals
number: /\d+(\.\d+)?/;
"""

called = [False, False, False]
node_exists = [False]


def act_sum(context, nodes):
    called[0] = True
    assert context.parser
    assert context.symbol.name == 'E'
    assert context.production.symbol.name == 'E'
    assert len(context.production.rhs) == 3
    assert context.layout_content == '   '
    assert context.start_position == 3
    assert context.end_position == 8
    if context.extra:
        assert type(context.node) is NodeNonTerm \
            and context.node.symbol.name == 'E'
        node_exists[0] = True


def act_eof(context, nodes):
    called[1] = True
    assert context.symbol.name == 'EOF'
    # The remaining layout at the end of input
    assert context.layout_content == '  '


def act_number(context, value):
    called[2] = True
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
    "E": [act_sum, pass_single],
    "number": act_number,
    "EOF": act_eof
}

g = Grammar.from_string(grammar)


def test_parse_context():
    global called
    called = [False, False, False]

    parser = Parser(g, actions=actions, debug=True)

    parser.parse("   1 + 2  ")

    assert all(called)


def test_parse_context_call_actions():
    """
    Test that valid context attributes are available when calling
    actions using `call_actions`.
    """
    global called
    called = [False, False, False]

    parser = Parser(g, build_tree=True, actions=actions, debug=True)

    tree = parser.parse("   1 + 2  ")
    context = Context()

    context.extra = True
    parser.call_actions(tree, context=context)

    assert all(called)
    assert node_exists[0]
