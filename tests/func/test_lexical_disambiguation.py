import pytest  # noqa
from parglare import Parser, Grammar


def assert_false(_, __):
    assert False


def test_priority():
    """
    Terminal priority is first checked. If there is multiple terminals
    that can match at given location, the one with the highest priority
    will be used.
    """

    grammar = """
    S = First | Second | Third;
    First = /\d+\.\d+/;
    Second = '14';
    Third = /\d+/ {15};
    """

    called = [False]

    def act_called(_, __):
        called[0] = True

    g = Grammar.from_string(grammar)
    actions = {
        "First": assert_false,
        "Second": assert_false,
        "Third": act_called,
    }
    parser = Parser(g, actions=actions)

    parser.parse('14')

    assert called[0]


def test_longest_match():
    "If priorities are the same longest-match strategy is used."

    grammar = """
    S = First | Second | Third;
    First = /\d+\.\d+/;
    Second = /\d+/;
    Third = /\d+a/;
    """
    g = Grammar.from_string(grammar)

    called = [False]

    def act_called(_, __):
        called[0] = True

    actions = {
        "First": act_called,
        "Second": assert_false,
        "Third": assert_false,
    }
    parser = Parser(g, actions=actions)

    # "First" will be used as it can match longer string.
    parser.parse('45.67')
    assert called[0]

    called = [False]

    def act_called(_, __):
        called[0] = True

    actions = {
        "First": assert_false,
        "Second": assert_false,
        "Third": act_called
    }
    parser = Parser(g, actions=actions)

    # "Third" will be used as it can match longer string.
    parser.parse('45a')
    assert called[0]


def test_most_specific():
    """If multiple terminals are of the same priority and matches the same length
    strings we shall prefer the result of the most specific recognizer, i.e.
    StringRecognizer over RegExRecognizer.
    """

    grammar = """
    S = First | Second | Third;
    First = "45";
    Second = /\d+/;
    Third = /\d+\.\d+/;
    """

    called = [False]

    def act_called(_, __):
        called[0] = True

    g = Grammar.from_string(grammar)
    actions = {
        "First": act_called,
        "Second": assert_false,
        "Third": assert_false,
    }
    parser = Parser(g, actions=actions)

    # "First" will be used as it is the most specific.
    parser.parse('45')
    assert called[0]


def test_if_all_fails():
    """
    If all strategies doesn't result in single terminal, choose first.
    TODO: Maybe some kind of warning would be useful.
    """

    # In this grammar all three terminal rules could be applied for string
    # "b56". They are of the same priority, same length match and all are
    # regexes. In this case choose the first one.
    grammar = """
    S = First | Second | Third;
    First = /(a|b)\d+/;
    Second = /(a|b|c)\d+/;
    Third = /(a|b|c|d)\d+/;
    """

    called = [False]

    def act_called(_, __):
        called[0] = True

    g = Grammar.from_string(grammar)
    actions = {
        "First": act_called,
        "Second": assert_false,
        "Third": assert_false,
    }
    parser = Parser(g, actions=actions)

    parser.parse("b56")
