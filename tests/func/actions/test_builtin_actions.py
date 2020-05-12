import pytest  # noqa
from parglare import Grammar, Parser, Actions
from parglare.exceptions import ParserInitError


def test_collect_left():
    grammar = """
    @collect
    Elements: Elements Element | Element;
    @pass_single
    Element: "a" | "b";
    """

    g = Grammar.from_string(grammar)

    parser = Parser(g, actions=Actions(), debug=True)

    result = parser.parse('a b a a b')

    assert result == ['a', 'b', 'a', 'a', 'b']


def test_collect_left_optional():
    grammar = """
    @collect_optional
    Elements: Elements Element | Element | EMPTY;
    @pass_single
    Element: "a" | "b";
    """

    g = Grammar.from_string(grammar)

    parser = Parser(g, actions=Actions(), debug=True)

    result = parser.parse('a b a a b')
    assert result == ['a', 'b', 'a', 'a', 'b']

    # Empty parse returns None
    result = parser.parse('')
    assert result == []


def test_collect_left_sep():
    grammar = """
    @collect_sep
    Elements: Elements "," Element | Element;
    @pass_single
    Element: "a" | "b";
    """

    g = Grammar.from_string(grammar)

    parser = Parser(g, actions=Actions(), debug=True)

    result = parser.parse('a, b, a ,a, b')

    assert result == ['a', 'b', 'a', 'a', 'b']


def test_collect_left_sep_optional():
    grammar = """
    @collect_sep_optional
    Elements: Elements "," Element | Element | EMPTY;
    @pass_single
    Element: "a" | "b";
    """

    g = Grammar.from_string(grammar)

    parser = Parser(g, actions=Actions(), debug=True)

    result = parser.parse('a ,b, a, a, b')
    assert result == ['a', 'b', 'a', 'a', 'b']

    # Empty parse returns None
    result = parser.parse('')
    assert result == []


def test_collect_right():
    grammar = """
    @collect_right
    Elements: Element Elements | Element;
    @pass_single
    Element: "a" | "b";
    """

    g = Grammar.from_string(grammar)

    parser = Parser(g, actions=Actions(), debug=True)

    result = parser.parse('a b a a b')

    assert result == ['a', 'b', 'a', 'a', 'b']


def test_collect_right_optional():
    grammar = """
    @collect_right_optional
    Elements: Element Elements | Element | EMPTY;
    @pass_single
    Element: "a" | "b";
    """

    g = Grammar.from_string(grammar)

    parser = Parser(g, actions=Actions(), debug=True)

    result = parser.parse('a b a a b')
    assert result == ['a', 'b', 'a', 'a', 'b']

    # Empty parse returns None
    result = parser.parse('')
    assert result == []


def test_collect_right_sep():
    grammar = """
    @collect_right_sep
    Elements: Element "," Elements | Element;
    @pass_single
    Element: "a" | "b";
    """

    g = Grammar.from_string(grammar)

    parser = Parser(g, actions=Actions(), debug=True)

    result = parser.parse('a, b, a ,a, b')

    assert result == ['a', 'b', 'a', 'a', 'b']


def test_collect_right_sep_optional():
    grammar = """
    @collect_right_sep_optional
    Elements: Element "," Elements | Element | EMPTY;
    @pass_single
    Element: "a" | "b";
    """

    g = Grammar.from_string(grammar)

    parser = Parser(g, actions=Actions(), debug=True)

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

    class MyActions(Actions):
        called = [False, False]

        def nonterm_action(self, _):
            self.called[0] = True

        def term_action(self, _):
            self.called[1] = True

    g = Grammar.from_string(grammar)
    p = Parser(g, actions=MyActions())
    assert p.parse("a b a b")
    assert all(MyActions.called)


def test_parglare_builtin_action_override():
    """
    """
    grammar = """
    @collect
    As: As A | A;
    A: "a";
    """

    class MyActions(Actions):
        called = [False]

        def collect(self, _):
            self.called[0] = True
            return True

    g = Grammar.from_string(grammar)
    p = Parser(g, actions=MyActions())
    assert p.parse("a a ") is True
    assert MyActions.called[0]


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

    class MyActions(Actions):
        called = [False]

        def collect(self, _):
            self.called[0] = True
            return "pass"

    g = Grammar.from_string(grammar)
    p = Parser(g, actions=MyActions())
    assert p.parse("b b") == 'pass'
    assert MyActions.called[0]


def test_unexisting_builtin_action_raises_exception():
    """
    """
    grammar = """
    S: A;
    @a_action_unexisting
    A: "a";
    """

    g = Grammar.from_string(grammar)
    with pytest.raises(ParserInitError) as e:
        Parser(g, actions=Actions())

    assert 'a_action_unexisting' in str(e.value)
