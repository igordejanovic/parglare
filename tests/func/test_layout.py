import pytest  # noqa
from parglare import Parser, Grammar
from parglare.actions import pass_single_if_exists


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
    parser = Parser(g)

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
    NotComment = /((\*[^\/])|[^\s*\/]|\/[^\*])+/;
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


def test_layout_context():
    """
    Test that layout is passed in the action context.
    """
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

    layout_called = [False]
    layout_passed = [False]

    def layout_action(context, _):
        layout_called[0] = True
        if 'This is a comment' in context.layout_content:
            layout_passed[0] = True

    actions = {
        "a": layout_action
    }

    g = Grammar.from_string(grammar)
    parser = Parser(g, actions=actions)

    parser.parse("""aaa a    aaaa
    aa    aa a aaa // This is a comment

    aaa
    """)

    assert layout_called[0]
    assert layout_passed[0]


def test_layout_actions():
    """
    Test that user provided actions for layout rules are used if given.
    """

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

    called = [False]
    layout_called = [False]
    layout_passed = [False]

    def comment_action(_, nodes):
        called[0] = True
        # If layout action return non-None value it should be used as a
        # layout_content in the context object
        return "This is processed comment"

    def layout_action(_, nodes):
        ret = ''
        for n in nodes:
            if n:
                ret += n
        return ret

    def a_action(context, _):
        layout_called[0] = True
        if 'This is processed comment' in context.layout_content:
            layout_passed[0] = True

    actions = {
        'Comment': comment_action,
        'LayoutItem': pass_single_if_exists,
        'LAYOUT': layout_action,
        'a': a_action
    }
    parser = Parser(g, actions=actions)
    parser.parse("""aaa a    aaaa
    aa    aa a aaa // This is a comment

    aaa
    """)

    assert called[0]
    assert layout_called[0]
    assert layout_passed[0]
