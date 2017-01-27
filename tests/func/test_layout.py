import pytest
from parglare import Parser, Grammar


def test_layout_whitespaces():
    grammar = r"""
    S = A | B;
    A = 'a' A | 'a';
    B = 'b' B | 'b';
    LAYOUT = WS;
    WS = /\s+/;
    """

    g = Grammar.from_string(grammar)
    parser = Parser(g)

    parser.parse("""aaa a    aaaa
    aa    aa a aaa

    aaa
    """)


def test_layout_simple_comments():
    pass


def test_layout_nested_comments():
    pass
