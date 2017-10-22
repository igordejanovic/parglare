import pytest  # noqa
from parglare.actions import collect, collect_optional, \
    collect_sep, collect_sep_optional, collect_right, \
    collect_right_optional, collect_right_sep, \
    collect_right_sep_optional, pass_single
from parglare import Grammar, Parser
from parglare.exceptions import ParserInitError


def test_collect_left():
    grammar = """
    Elements: Elements Element | Element;
    Element: "a" | "b";
    """

    g = Grammar.from_string(grammar)

    actions = {
        "Elements": collect,
        "Element": pass_single
    }

    parser = Parser(g, actions=actions, debug=True)

    result = parser.parse('a b a a b')

    assert result == ['a', 'b', 'a', 'a', 'b']


def test_collect_left_optional():
    grammar = """
    Elements: Elements Element | Element | EMPTY;
    Element: "a" | "b";
    """

    g = Grammar.from_string(grammar)

    actions = {
        "Elements": collect_optional,
        "Element": pass_single
    }

    parser = Parser(g, actions=actions, debug=True)

    result = parser.parse('a b a a b')
    assert result == ['a', 'b', 'a', 'a', 'b']

    # Empty parse returns None
    result = parser.parse('')
    assert result == []


def test_collect_left_sep():
    grammar = """
    Elements: Elements "," Element | Element;
    Element: "a" | "b";
    """

    g = Grammar.from_string(grammar)

    actions = {
        "Elements": collect_sep,
        "Element": pass_single
    }

    parser = Parser(g, actions=actions, debug=True)

    result = parser.parse('a, b, a ,a, b')

    assert result == ['a', 'b', 'a', 'a', 'b']


def test_collect_left_sep_optional():
    grammar = """
    Elements: Elements "," Element | Element | EMPTY;
    Element: "a" | "b";
    """

    g = Grammar.from_string(grammar)

    actions = {
        "Elements": collect_sep_optional,
        "Element": pass_single
    }

    parser = Parser(g, actions=actions, debug=True)

    result = parser.parse('a ,b, a, a, b')
    assert result == ['a', 'b', 'a', 'a', 'b']

    # Empty parse returns None
    result = parser.parse('')
    assert result == []


def test_collect_right():
    grammar = """
    Elements: Element Elements | Element;
    Element: "a" | "b";
    """

    g = Grammar.from_string(grammar)

    actions = {
        "Elements": collect_right,
        "Element": pass_single
    }

    parser = Parser(g, actions=actions, debug=True)

    result = parser.parse('a b a a b')

    assert result == ['a', 'b', 'a', 'a', 'b']


def test_collect_right_optional():
    grammar = """
    Elements: Element Elements | Element | EMPTY;
    Element: "a" | "b";
    """

    g = Grammar.from_string(grammar)

    actions = {
        "Elements": collect_right_optional,
        "Element": pass_single
    }

    parser = Parser(g, actions=actions, debug=True)

    result = parser.parse('a b a a b')
    assert result == ['a', 'b', 'a', 'a', 'b']

    # Empty parse returns None
    result = parser.parse('')
    assert result == []


def test_collect_right_sep():
    grammar = """
    Elements: Element "," Elements | Element;
    Element: "a" | "b";
    """

    g = Grammar.from_string(grammar)

    actions = {
        "Elements": collect_right_sep,
        "Element": pass_single
    }

    parser = Parser(g, actions=actions, debug=True)

    result = parser.parse('a, b, a ,a, b')

    assert result == ['a', 'b', 'a', 'a', 'b']


def test_collect_right_sep_optional():
    grammar = """
    Elements: Element "," Elements | Element | EMPTY;
    Element: "a" | "b";
    """

    g = Grammar.from_string(grammar)

    actions = {
        "Elements": collect_right_sep_optional,
        "Element": pass_single
    }

    parser = Parser(g, actions=actions, debug=True)

    result = parser.parse('a ,b, a, a, b')
    assert result == ['a', 'b', 'a', 'a', 'b']

    # Empty parse returns None
    result = parser.parse('')
    assert result == []


def test_user_grammar_actions():
    """
    Test that user supplied actions are used.
    """
    grammar = """
    S: A B C;
    @nonterm_action
    C: A B;
    A: "a";
    @term_action
    B: "b";
    """

    called = [False, False]

    def nonterm_action(_, __):
        called[0] = True

    def term_action(_, __):
        called[1] = True

    my_actions = {
        "nonterm_action": nonterm_action,
        "term_action": term_action,
    }

    g = Grammar.from_string(grammar)
    p = Parser(g, actions=my_actions)
    assert p.parse("a b a b")
    assert all(called)


def test_parglare_builtin_action_override():
    """
    """
    grammar = """
    S: As EOF;
    @collect
    As: As A | A;
    A: "a";
    """

    called = [False]

    def my_collect(_, __):
        called[0] = True

    my_actions = {
        "collect": my_collect,
    }

    g = Grammar.from_string(grammar)
    p = Parser(g, actions=my_actions)
    assert p.parse("a a ")
    assert called[0]


def test_parglare_builtin_action_override_repetition():
    """
    Test that user given action can override actions attached to
    repetition operator generated rule actions.
    """
    # B+ will product B_1 rule with `collect` common action
    grammar = """
    S: B+;
    B: "b";
    """

    called = [False]

    def my_collect(_, __):
        called[0] = True
        return "pass"

    my_actions = {
        "collect": my_collect,
    }

    g = Grammar.from_string(grammar)
    p = Parser(g, actions=my_actions)
    assert p.parse("b b") == 'pass'
    assert called[0]


def test_unexisting_builtin_action_raises_exception():
    """
    """
    grammar = """
    S: A;
    @a_action_unexisting
    A: "a";
    """

    my_actions = {
        "collect": lambda _, __: None,
    }

    g = Grammar.from_string(grammar)
    with pytest.raises(ParserInitError) as e:
        Parser(g, actions=my_actions)

    assert 'a_action_unexisting' in str(e)
