# -*- coding: utf-8 -*-
# Tests for issue #73 (see https://github.com/igordejanovic/parglare/issues/73)
from parglare import Grammar, Parser


def test_recursive_rule():
    grammar = r"""
    s: as;
    as: as "a" | EMPTY;
    """

    g = Grammar.from_string(grammar)
    parser = Parser(g)
    parser.parse('aaa')


def test_recursive_rule_other_way():
    grammar = r"""
    s: as;
    as: EMPTY | as "a";
    """

    g = Grammar.from_string(grammar)
    parser = Parser(g)
    parser.parse('aaa')
