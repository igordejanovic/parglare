import pytest  # noqa
from parglare import Grammar, Parser
from parglare.exceptions import NoActionsForRootRule


def test_no_actions_root_rule():
    """
    If root rule have no recursion termination alternative as for example:

    Elements = Elements Element;

    instead of:
    Elements = Elements Element | Element;

    Action set for the first state will have no elements so parsing can't even
    begin as no SHIFT actions can occur.
    """

    grammar = """
    Elements = Elements Element;
    Element = "a" | "b";
    """

    g = Grammar.from_string(grammar)

    with pytest.raises(NoActionsForRootRule):
        Parser(g)
