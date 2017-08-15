import pytest  # noqa
from parglare import GLRParser, Grammar, Parser
from parglare.exceptions import SRConflicts
from parglare.parser import REDUCE


grammar = """
E: E '+' E {dynamic}
 | E '*' E {dynamic}
 | /\d+/;
"""
instr1 = '1 + 2 * 5 + 3'
instr2 = '1 * 2 + 5 * 3'

actions = {
    'E': [lambda _, nodes: nodes[0] + nodes[2],
          lambda _, nodes: nodes[0] * nodes[2],
          lambda _, nodes: float(nodes[0].value)]
}


g = Grammar.from_string(grammar)


operations = []


def custom_disambiguation(actions, token_ahead):
    """Make first operation that appears in the input as lower priority.
    This demonstrates how priority rule can change dynamically depending
    on the input.
    """
    global operations

    # At the start of parsing this function is called with actions set to
    # None to give a change for the strategy to initialize.
    if actions is None:
        operations = []
        return

    # Find symbol of operation in reduction production (operation to the left)
    redop = [a for a in actions if a.action == REDUCE][0]
    redop_symbol = redop.prod.rhs[1]

    if not operations:
        # At the beggining
        # Add the first operation from reduction
        operations.append(redop_symbol)

    if token_ahead.symbol not in operations:
        operations.append(token_ahead.symbol)

    if operations.index(token_ahead.symbol) > operations.index(redop_symbol):
        return [actions[0]]
    else:
        return [redop]


def test_dynamic_disambiguation():
    """
    Test disambiguation determined at run-time based on the input.
    This tests LR parsing.
    """

    # This grammar is ambiguous
    with pytest.raises(SRConflicts):
        Parser(g)

    # But if we provide dynamic disambiguation filter
    # the conflicts can be handled at run-time.
    p = Parser(g, actions=actions,
               dynamic_disambiguation=custom_disambiguation)

    # * operation will be of higher priority as it appears later in the stream.
    result1 = p.parse(instr1)
    assert result1 == 1 + (2 * 5) + 3

    # + operation will be of higher priority here.
    result2 = p.parse(instr2)
    assert result2 == 1 * (2 + 5) * 3


def test_dynamic_disambiguation_glr():
    """
    Test disambiguation determined at run-time based on the input.
    This tests GLR parsing.
    """
    p = GLRParser(g, actions=actions,
                  dynamic_disambiguation=custom_disambiguation)

    # * operation will be of higher priority as it appears later in the stream.
    result1 = p.parse(instr1)
    assert len(result1) == 1
    assert result1[0] == 1 + (2 * 5) + 3

    # + operation will be of higher priority here.
    result2 = p.parse(instr2)
    assert len(result2) == 1
    assert result2[0] == 1 * (2 + 5) * 3
