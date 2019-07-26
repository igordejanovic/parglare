# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import pytest  # noqa
from parglare import Grammar, Parser, Actions
from parglare.parser import NodeNonTerm, Context


grammar = r"""
Result: E EOF;
E: E '+' E  {left}
 | number;

terminals
number: /\d+(\.\d+)?/;
"""


class MyActions(Actions):

    def __init__(self):
        self.called = [False, False, False]
        self.node_exists = False

    def sum(self, nodes):
        self.called[0] = True
        context = self.context
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
            self.node_exists = True

    def E(self, nodes):
        return [self.sum, self.pass_single][self.prod_idx](nodes)

    def EOF(self, nodes):
        self.called[1] = True
        assert self.context.symbol.name == 'EOF'
        # The remaining layout at the end of input
        assert self.context.layout_content == '  '

    def number(self, value):
        self.called[2] = True
        context = self.context
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


g = Grammar.from_string(grammar)


def test_parse_context():
    actions = MyActions()
    parser = Parser(g, actions=actions)

    parser.parse("   1 + 2  ")

    assert all(actions.called)


def test_parse_context_call_actions():
    """
    Test that valid context attributes are available when calling
    actions using `call_actions`.
    """

    actions = MyActions()
    parser = Parser(g, build_tree=True, actions=actions)

    tree = parser.parse("   1 + 2  ")
    context = Context()

    context.extra = True
    parser.call_actions(tree, context=context)

    assert all(actions.called)
    assert actions.node_exists
