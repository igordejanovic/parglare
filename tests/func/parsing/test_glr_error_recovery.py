# -*- coding: utf-8 -*-
import pytest  # noqa
from parglare import GLRParser, Grammar, ParseError
from parglare.parser import Token
from parglare.actions import pass_single, pass_inner

grammar = r"""
E: E '+' E
 | E '-' E
 | E '*' E
 | E '/' E
 | E '^' E
 | '(' E ')'
 | number;

terminals
number: /\d+(\.\d+)?/;
"""

actions = {
    "E": [lambda _, nodes: nodes[0] + nodes[2],
          lambda _, nodes: nodes[0] - nodes[2],
          lambda _, nodes: nodes[0] * nodes[2],
          lambda _, nodes: nodes[0] / nodes[2],
          lambda _, nodes: nodes[0] ** nodes[2],
          pass_inner,
          pass_single],
    "number": lambda _, value: float(value),
}

g = Grammar.from_string(grammar)


def test_glr_recovery_default():
    """
    Test default error recovery in GLR parsing. Default recovery should report
    the error, drop current input at position and try to recover.
    In case of multiple subsequent errouneous chars only one error should be
    reported.
    """
    parser = GLRParser(g, actions=actions, error_recovery=True)

    results = parser.parse('1 + 2 + * 3 & 89 - 5')

    assert len(parser.errors) == 2
    e1, e2 = parser.errors

    # First errors is '*' at position 8 and of length 2
    assert e1.location.start_position == 8
    assert e1.location.end_position == 10

    # Second error is '& 89' at position 12 and length 5
    assert e2.location.start_position == 12
    assert e2.location.end_position == 17

    # There are 5 trees for '1 + 2 + 3 - 5'
    # All results are the same
    assert len(results) == 5
    result_set = set([parser.call_actions(tree) for tree in results])
    assert len(result_set) == 1
    assert 1 in set(result_set)


def test_glr_recovery_custom_new_position():
    """
    Test that custom recovery that increment position works.
    """

    def custom_recovery(head, error):
        # This recovery will just skip over erroneous part of input '& 89'.
        head.position += 4
        return head.parser.default_error_recovery(head)

    parser = GLRParser(g, actions=actions, error_recovery=custom_recovery)

    results = parser.parse('1 + 5 & 89 - 2')

    assert len(parser.errors) == 1
    assert len(results) == 2
    result_set = set([parser.call_actions(tree) for tree in results])
    assert len(result_set) == 1
    # Calculated result should be '1 + 5 - 2'
    assert result_set.pop() == 4


def test_glr_recovery_custom_new_token():
    """
    Test that custom recovery that introduces new token works.
    """

    def custom_recovery(head, error):
        # Here we will introduce missing operation token
        head.token_ahead = Token(g.get_terminal('-'), '-', head.position, length=0)
        return True

    parser = GLRParser(g, actions=actions, error_recovery=custom_recovery)

    results = parser.parse('1 + 5 8 - 2')

    assert len(parser.errors) == 1
    assert len(results) == 5
    result_set = set([parser.call_actions(tree) for tree in results])
    assert len(result_set) == 2
    assert -4 in result_set
    assert 0 in result_set


def test_glr_recovery_custom_unsuccessful():
    """
    Test unsuccessful error recovery.
    """

    def custom_recovery(head, error):
        return False

    parser = GLRParser(g, actions=actions, error_recovery=custom_recovery)

    with pytest.raises(ParseError) as e:
        parser.parse('1 + 5 8 - 2')

    error = e.value
    assert error.location.start_position == 6
