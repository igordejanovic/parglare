import pytest
from parglare import Parser, Grammar


def test_layout_whitespaces():
    grammar = r"""
    S = K EOF;
    K = A | B;
    A = 'a' A | 'a';
    B = 'b' B | 'b';
    LAYOUT = WS | EMPTY;
    WS = /\s+/;
    """

    g = Grammar.from_string(grammar)
    parser = Parser(g, debug=True)

    parser.parse("""aaa a    aaaa
    aa    aa a aaa

    aaa
    """)


def test_layout_simple_comments():
    grammar = r"""
    S = K EOF;
    K = A | B;
    A = 'a' A | 'a';
    B = 'b' B | 'b';
    LAYOUT = LayoutItem | LAYOUT LayoutItem;
    LayoutItem = WS | Comment | EMPTY;
    WS = /\s+/;
    Comment = /\/\/.*/;
    """

    g = Grammar.from_string(grammar)
    parser = Parser(g)

    parser.parse("""aaa a    aaaa
    aa    aa a aaa // This is a comment

    aaa
    """)


def test_layout_nested_comments():
    grammar = """
    S = K EOF;
    K = 'a' B | 'a' C;
    B = 'b' | B 'b';
    C = 'c' | C 'c';

    LAYOUT = LayoutItem | LAYOUT LayoutItem;
    LayoutItem = WS | Comment | EMPTY;
    WS = /\s+/;
    Comment = '/*' CorNCs '*/' | /\/\/.*/;
    CorNCs = CorNC | CorNCs CorNC | EMPTY;
    CorNC = Comment | NotComment | WS;
    NotComment = /((\*[^\/])|[^*\/]|\/[^\*])+/;
    """
    g = Grammar.from_string(grammar)
    parser = Parser(g)
    parser.parse("""
    a  b b b   b // This is line comment
    b b b b b b  /* This is block
    comment */

    bbbb  b b b b b
    /* Another block comment
       // With nested line comment
       /* And nested block
    comment */
    */

    bbbb b b b 
    """)
