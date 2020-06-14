import os
from parglare import get_collector, Parser, Grammar

THIS_FOLDER = os.path.abspath(os.path.dirname(__file__))


def test_action_explicit_get_collector():
    """
    Test the basic usage of `get_collector` API where we don't provide
    actions in a separate python module.
    """

    action = get_collector()

    @action
    def INT(context, value):
        return int(value)

    @action
    def STRING(context, value):
        return "#{}#".format(value)

    grammar = Grammar.from_file(os.path.join(THIS_FOLDER, 'grammar.pg'))
    Parser(grammar, actions=action.all)


def test_action_explicit_get_collector_missing_action():
    """
    Test when `get_collector` has a terminal without defined action nothing
    happens as the default implicit action will be used.
    """

    action = get_collector()

    @action
    def INT(context, value):
        return int(value)

    grammar = Grammar.from_file(os.path.join(THIS_FOLDER, 'grammar.pg'))
    Parser(grammar, actions=action.all)


def test_actions_explicit_get_collector_action_for_unexisting_terminal():
    """
    Test for situation when `get_collector` has an action for un-existing
    terminal.
    """

    action = get_collector()

    @action
    def INT(context, value):
        return int(value)

    @action
    def STRING(context, value):
        return "#{}#".format(value)

    @action
    def STRING2(context, value):
        return "#{}#".format(value)

    grammar = Grammar.from_file(os.path.join(THIS_FOLDER, 'grammar.pg'))
    Parser(grammar, actions=action.all)
