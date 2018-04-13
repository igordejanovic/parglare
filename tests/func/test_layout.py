# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import pytest  # noqa
from parglare import Parser, GLRParser, Grammar, ParseError

parsers = pytest.mark.parametrize("parser_class", [Parser, GLRParser])


@parsers
def test_layout_whitespaces(parser_class):
    grammar = r"""
    S: K EOF;
    K: A | B;
    A: 'a' A | 'a';
    B: 'b' B | 'b';
    LAYOUT: WS | EMPTY;

    terminals
    WS: /\s+/;
    """
    g = Grammar.from_string(grammar)

    in_str = """aaa a    aaaa
    aa    aa a aaa

    aaa
    """

    parser = parser_class(g, debug=True)
    result = parser.parse(in_str)
    assert result


@parsers
def test_layout_simple_comments(parser_class):
    grammar = r"""
    S: K EOF;
    K: A | B;
    A: 'a' A | 'a';
    B: 'b' B | 'b';

    LAYOUT: LayoutItem | LAYOUT LayoutItem;
    LayoutItem: WS | Comment | EMPTY;

    terminals
    WS: /\s+/;
    Comment: /\/\/.*/;
    """
    g = Grammar.from_string(grammar)

    in_str = """aaa a    aaaa
    aa    aa a aaa // This is a comment

    aaa
    """

    parser = parser_class(g)
    parser.parse(in_str)


@parsers
def test_layout_nested_comments(parser_class):
    grammar = """
    S: K EOF;
    K: 'a' B | 'a' C;
    B: 'b' | B 'b';
    C: 'c' | C 'c';

    LAYOUT: LayoutItem | LAYOUT LayoutItem;
    LayoutItem: WS | Comment | EMPTY;
    Comment: '/*' CorNCs '*/' | LineComment;
    CorNCs: CorNC | CorNCs CorNC | EMPTY;
    CorNC: Comment | NotComment | WS;

    terminals
    WS: /\s+/;
    LineComment: /\/\/.*/;
    NotComment: /((\*[^\/])|[^\s*\/]|\/[^\*])+/;
    """
    g = Grammar.from_string(grammar)

    in_str = """//Line comment at beginning
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
    """

    parser = parser_class(g)
    parser.parse(in_str)


@parsers
def test_layout_context(parser_class):
    """
    Test that layout is passed in the action context.
    """
    grammar = r"""
    S: K EOF;
    K: A | B;
    A: 'a' A | 'a';
    B: 'b' B | 'b';

    LAYOUT: LayoutItem | LAYOUT LayoutItem;
    LayoutItem: WS | Comment | EMPTY;

    terminals
    WS: /\s+/;
    Comment: /\/\/.*/;
    """
    g = Grammar.from_string(grammar)

    in_str = """aaa a    aaaa
    aa    aa a aaa // This is a comment

    aaa
    """

    def layout_action(context, _):
        layout_called[0] = True
        if 'This is a comment' in context.layout_content:
            layout_passed[0] = True

    actions = {
        "a": layout_action
    }

    layout_called = [False]
    layout_passed = [False]

    parser = parser_class(g, actions=actions)

    parser.parse(in_str)

    assert layout_called[0]
    assert layout_passed[0]


@parsers
def test_layout_actions(parser_class):
    """
    Test that user provided actions for layout rules are called if given.
    """

    grammar = r"""
    S: K EOF;
    K: A | B;
    A: 'a' A | 'a';
    B: 'b' B | 'b';

    LAYOUT: LayoutItem | LAYOUT LayoutItem;
    LayoutItem: WS | Comment | EMPTY;

    terminals
    WS: /\s+/;
    Comment: /\/\/.*/;
    """
    g = Grammar.from_string(grammar)

    in_str = """aaa a    aaaa
    aa    aa a aaa // This is a comment

    aaa
    """

    def comment_action(_, nodes):
        layout_called[0] = True

    def layout_action(_, nodes):
        ret = ''
        for n in nodes:
            if n:
                ret += n
        return ret

    def a_action(context, _):
        called[0] = True

    actions = {
        'Comment': comment_action,
        'LAYOUT': layout_action,
        'a': a_action
    }

    called = [False]
    layout_called = [False]

    parser = parser_class(g, actions=actions, layout_actions=actions)
    parser.parse(in_str)

    assert called[0]
    assert layout_called[0]


def test_layout_terminal():
    """
    Test that layout definition may be just a terminal rule.
    """
    grammar = r"""
    S: "a" "b";
    LAYOUT: "c";
    """

    g = Grammar.from_string(grammar)
    parser = Parser(g)

    with pytest.raises(ParseError):
        parser.parse("a b")
    parser.parse("cacbc")

    grammar = r"""
    S: "a" "b";
    LAYOUT: DIGITS;

    terminals
    DIGITS: /\d*/;
    """

    g = Grammar.from_string(grammar)
    parser = Parser(g)

    with pytest.raises(ParseError):
        parser.parse("a b")
    result = parser.parse("4444a23b545")
    assert result == ['a', 'b']
