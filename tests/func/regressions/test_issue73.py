# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import pytest
from parglare import Grammar, Parser


@pytest.mark.skip
def test_recursive_rule():
    grammar = r"""
    s: as EOF;
    as: as "a" | EMPTY;
    """

    g = Grammar.from_string(grammar)
    parser = Parser(g)
    parser.parse('aaa')


@pytest.mark.skip
def test_recursive_rule_other_way():
    grammar = r"""
    s: as EOF;
    as: EMPTY | as "a";
    """

    g = Grammar.from_string(grammar)
    parser = Parser(g)
    parser.parse('aaa')
