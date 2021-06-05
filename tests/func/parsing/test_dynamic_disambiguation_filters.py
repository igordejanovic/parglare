import pytest  # noqa
from parglare import GLRParser, Grammar, Parser, SHIFT, REDUCE
from parglare.exceptions import SRConflicts


grammar = r"""
E: E op_sum E {dynamic}
 | E op_mul E {dynamic}
 | number;

terminals
number: /\d+/;
op_sum: '+' {dynamic};
op_mul: '*' {dynamic};
"""
instr1 = '1 + 2 * 5 + 3'
instr2 = '1 * 2 + 5 * 3'

actions = {
    'E': [lambda _, nodes: nodes[0] + nodes[2],
          lambda _, nodes: nodes[0] * nodes[2],
          lambda _, nodes: float(nodes[0])]
}


g = Grammar.from_string(grammar)


operations = []


def custom_disambiguation_filter(context, from_state, to_state, action,
                                 production, subresults):
    """
    Make first operation that appears in the input as lower priority.
    This demonstrates how priority rule can change dynamically depending
    on the input or how disambiguation can be decided during parsing.
    """
    global operations

    # At the start of parsing this function is called with actions set to None
    # to give a chance for the strategy to initialize.
    if action is None:
        operations = []
        return

    if action is SHIFT:
        operation = context.token.symbol
    else:
        operation = context.token_ahead.symbol

    actions = from_state.actions[operation]
    if operation not in operations and operation.name != 'STOP':
        operations.append(operation)

    if action is SHIFT:
        shifts = [a for a in actions if a.action is SHIFT]
        if not shifts:
            return False

        reductions = [a for a in actions if a.action is REDUCE]
        if not reductions:
            return True

        red_op = reductions[0].prod.rhs[1]
        return operations.index(operation) > operations.index(red_op)

    elif action is REDUCE:

        # Current reduction operation
        red_op = production.rhs[1]

        # If operation ahead is STOP or is of less or equal priority -> reduce.
        return ((operation not in operations)
                or (operations.index(operation)
                    <= operations.index(red_op)))


def test_dynamic_disambiguation():
    """
    Test disambiguation determined at run-time based on the input.
    This tests LR parsing.
    """

    # This grammar is ambiguous if no prefer_shift strategy is used.
    with pytest.raises(SRConflicts):
        Parser(g, prefer_shifts=False)

    # But if we provide dynamic disambiguation filter
    # the conflicts can be handled at run-time.
    p = Parser(g, actions=actions, prefer_shifts=False,
               dynamic_filter=custom_disambiguation_filter)

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
                  dynamic_filter=custom_disambiguation_filter)

    # * operation will be of higher priority as it appears later in the stream.
    result1 = p.parse(instr1)
    assert len(result1) == 1
    assert p.call_actions(result1[0]) == 1 + (2 * 5) + 3

    # + operation will be of higher priority here.
    result2 = p.parse(instr2)
    assert len(result2) == 1
    assert p.call_actions(result2[0]) == 1 * (2 + 5) * 3
