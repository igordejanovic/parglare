# -*- coding: utf-8 -*-
import pytest  # noqa
import os
from parglare import Grammar, Parser
from .calcactions import actions


def test_load_from_file():

    grammar = Grammar.from_file(os.path.join(
        os.path.dirname(__file__), 'calc.pg'))
    parser = Parser(grammar, actions=actions, debug=True)

    res = parser.parse("""
    a = 5
    b = 10

    56.4 + a / 3 * 5 - b + 8 * 3
    """)

    res2 = 56.4 + 5. / 3 * 5 - 10 + 8 * 3
    print(res2, res)
    assert res == 56.4 + 5. / 3 * 5 - 10 + 8 * 3
