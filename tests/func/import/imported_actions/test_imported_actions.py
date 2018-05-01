import os
from parglare import Grammar, Parser

this_folder = os.path.dirname(__file__)

model_str = '''
modelID 42
component myComponent {
    in SomeInputSlot
    out SomeOutputSlot
}
'''


def test_imported_actions_connect_by_symbol_name():
    g = Grammar.from_file(os.path.join(this_folder, 'by_symbol_name/model.pg'))
    model = Parser(g).parse(model_str)
    # Check that base.pg actions are properly loaded and triggered.
    assert model.modelID == 42


def test_imported_actions_connect_by_action_name():
    g = Grammar.from_file(os.path.join(this_folder, 'by_action_name/model.pg'))
    model = Parser(g).parse(model_str)
    # Check that base.pg actions are properly loaded and triggered.
    assert model.modelID == 42


def test_imported_actions_connect_by_decorator_action_name():
    g = Grammar.from_file(os.path.join(this_folder,
                                       'by_decorator_action_name/model.pg'))
    model = Parser(g).parse(model_str)
    # Check that base.pg actions are properly loaded and triggered.
    assert model.modelID == 42


def test_imported_actions_override():
    """
    Test that actions loaded from `*_actions.py` files can be overriden by
    users actions.
    """

    # We can override either by fqn of symbol
    g = Grammar.from_file(os.path.join(this_folder, 'by_symbol_name/model.pg'))
    actions = {
        'base.NUMERIC_ID': lambda _, value: 43
    }
    model = Parser(g, actions=actions).parse(model_str)
    assert model.modelID == 43

    # Or by action name used in grammar for the given symbol
    g = Grammar.from_file(os.path.join(this_folder, 'by_action_name/model.pg'))
    actions = {
        'base.number': lambda _, value: 43
    }
    model = Parser(g, actions=actions).parse(model_str)
    assert model.modelID == 43

    # Override by FQN takes precendence
    g = Grammar.from_file(os.path.join(this_folder, 'by_action_name/model.pg'))
    actions = {
        'base.NUMERIC_ID': lambda _, value: 43
    }
    model = Parser(g, actions=actions).parse(model_str)
    assert model.modelID == 43


def test_imported_actions_override_by_grammar_actions():
    """
    Test that actions loaded from `*_actions.py` files can override actions
    imported from other grammar files.
    """

    g = Grammar.from_file(os.path.join(this_folder,
                                       'in_grammar_by_symbol_name/model.pg'))
    model = Parser(g).parse(model_str)
    assert model.modelID == 43

    g = Grammar.from_file(os.path.join(this_folder,
                                       'in_grammar_by_action_name/model.pg'))
    model = Parser(g).parse(model_str)
    assert model.modelID == 43
