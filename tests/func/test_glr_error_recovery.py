# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import pytest  # noqa
from parglare import GLRParser, Grammar, Error
from parglare.parser import Token
from parglare.actions import pass_single, pass_inner

grammar = r"""
Result: E EOF;
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
    "Result": pass_single,
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
    parser = GLRParser(g, actions=actions, error_recovery=True, debug=True)

    results = parser.parse('1 + 2 + * 3 & 89 - 5')

    assert len(parser.errors) == 2
    e1, e2 = parser.errors

    # First errors is '*' at position 8 and of length 1
    assert e1.position == 8
    assert e1.length == 1

    # Second error is '& 89' at position 12 and lenght 4
    assert e2.position == 12
    assert e2.length == 4

    # There are 5 trees for '1 + 2 + 3 - 5'
    # All results are the same
    assert len(results) == 5
    assert len(set(results)) == 1
    assert 1 in set(results)


def test_glr_recovery_custom_new_position():
    """
    Test that custom recovery that increment position works.
    """
    error = Error(0, 1, message="Error")

    def custom_recovery(parser, input_str, position, symbols):
        # This recovery will just skip over erroneous part of input '& 89'.
        return error, position + 4, None

    parser = GLRParser(g, actions=actions, error_recovery=custom_recovery,
                       debug=True)

    results = parser.parse('1 + 5 & 89 - 2')

    assert len(parser.errors) == 1
    assert parser.errors[0] is error
    assert len(results) == 2
    assert len(set(results)) == 1
    # Calculate results should be '1 + 5 - 2'
    assert results[0] == 4


def test_glr_recovery_custom_new_token():
    """
    Test that custom recovery that introduces new token works.
    """
    error = Error(0, 1, message="Error")

    def custom_recovery(parser, input_str, position, symbols):
        # Here we will introduce missing operation token
        return error, None, Token(g.get_terminal('-'), '-', 0)

    parser = GLRParser(g, actions=actions, error_recovery=custom_recovery,
                       debug=True)

    results = parser.parse('1 + 5 8 - 2')

    assert len(parser.errors) == 1
    assert parser.errors[0] is error
    assert len(results) == 5
    assert len(set(results)) == 2
    assert -4 in results
    assert 0 in results
