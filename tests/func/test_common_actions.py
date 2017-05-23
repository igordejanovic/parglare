import pytest  # noqa
from parglare.actions import collect, collect_optional, \
    collect_sep, collect_sep_optional, collect_right, \
    collect_right_optional, collect_right_sep, \
    collect_right_sep_optional, pass_value
from parglare import Grammar, Parser


def test_collect_left():
    grammar = """
    Elements = Elements Element | Element;
    Element = "a" | "b";
    """

    g = Grammar.from_string(grammar)

    actions = {
        "Elements": collect,
        "Element": pass_value
    }

    parser = Parser(g, actions=actions, debug=True)

    result = parser.parse('a b a a b')

    assert result == ['a', 'b', 'a', 'a', 'b']


def test_collect_left_optional():
    grammar = """
    Elements = Elements Element | Element | EMPTY;
    Element = "a" | "b";
    """

    g = Grammar.from_string(grammar)

    actions = {
        "Elements": collect_optional,
        "Element": pass_value
    }

    parser = Parser(g, actions=actions, debug=True)

    result = parser.parse('a b a a b')
    assert result == ['a', 'b', 'a', 'a', 'b']

    # Empty parse returns None
    result = parser.parse('')
    assert result == []


def test_collect_left_sep():
    grammar = """
    Elements = Elements "," Element | Element;
    Element = "a" | "b";
    """

    g = Grammar.from_string(grammar)

    actions = {
        "Elements": collect_sep,
        "Element": pass_value
    }

    parser = Parser(g, actions=actions, debug=True)

    result = parser.parse('a, b, a ,a, b')

    assert result == ['a', 'b', 'a', 'a', 'b']


def test_collect_left_sep_optional():
    grammar = """
    Elements = Elements "," Element | Element | EMPTY;
    Element = "a" | "b";
    """

    g = Grammar.from_string(grammar)

    actions = {
        "Elements": collect_sep_optional,
        "Element": pass_value
    }

    parser = Parser(g, actions=actions, debug=True)

    result = parser.parse('a ,b, a, a, b')
    assert result == ['a', 'b', 'a', 'a', 'b']

    # Empty parse returns None
    result = parser.parse('')
    assert result == []


def test_collect_right():
    grammar = """
    Elements = Element Elements | Element;
    Element = "a" | "b";
    """

    g = Grammar.from_string(grammar)

    actions = {
        "Elements": collect_right,
        "Element": pass_value
    }

    parser = Parser(g, actions=actions, debug=True)

    result = parser.parse('a b a a b')

    assert result == ['a', 'b', 'a', 'a', 'b']


def test_collect_right_optional():
    grammar = """
    Elements = Element Elements | Element | EMPTY;
    Element = "a" | "b";
    """

    g = Grammar.from_string(grammar)

    actions = {
        "Elements": collect_right_optional,
        "Element": pass_value
    }

    parser = Parser(g, actions=actions, debug=True)

    result = parser.parse('a b a a b')
    assert result == ['a', 'b', 'a', 'a', 'b']

    # Empty parse returns None
    result = parser.parse('')
    assert result == []


def test_collect_right_sep():
    grammar = """
    Elements = Element "," Elements | Element;
    Element = "a" | "b";
    """

    g = Grammar.from_string(grammar)

    actions = {
        "Elements": collect_right_sep,
        "Element": pass_value
    }

    parser = Parser(g, actions=actions, debug=True)

    result = parser.parse('a, b, a ,a, b')

    assert result == ['a', 'b', 'a', 'a', 'b']


def test_collect_right_sep_optional():
    grammar = """
    Elements = Element "," Elements | Element | EMPTY;
    Element = "a" | "b";
    """

    g = Grammar.from_string(grammar)

    actions = {
        "Elements": collect_right_sep_optional,
        "Element": pass_value
    }

    parser = Parser(g, actions=actions, debug=True)

    result = parser.parse('a ,b, a, a, b')
    assert result == ['a', 'b', 'a', 'a', 'b']

    # Empty parse returns None
    result = parser.parse('')
    assert result == []
