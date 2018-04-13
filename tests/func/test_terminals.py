# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import pytest  # noqa
from parglare import Parser, Grammar


def test_str_terminals():
    g = r"""
    A: "a" B C D 'b';

    terminals
    B: "b\"";
    C: "\"c\" ";
    D: '\'d\'';
    """
    grammar = Grammar.from_string(g)
    p = Parser(grammar)
    tree = p.parse(r''' a b" "c" 'd' b ''')
    assert tree


def test_regex_terminals():
    g = r"""
    A: Aterm B C D 'b';
    C: 'c' Cterm;

    terminals
    Aterm: /a\//;
    Cterm: /a+/;
    B: /a'b[^"]/;
    D: /\d+\.\d+/;
    """
    grammar = Grammar.from_string(g)
    p = Parser(grammar)
    tree = p.parse(r''' a/ a'bc c aaaa 4.56 b ''')
    assert tree
