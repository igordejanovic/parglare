import pytest  # noqa
import re
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

    # Test that re.VEROSE flag is the default for regex matches
    assert grammar.get_terminal('Aterm').recognizer.regex.flags & re.VERBOSE == re.VERBOSE
