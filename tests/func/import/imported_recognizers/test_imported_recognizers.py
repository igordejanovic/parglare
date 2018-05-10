import pytest
import os
from types import FunctionType
from parglare import Grammar, Parser, GrammarError, ParseError
from .base_recognizers import number

this_folder = os.path.dirname(__file__)

model_str = '''
modelID 42.23.5
component myComponent extends some.fqn.name {
    in SomeInputSlot
    out SomeOutputSlot
}
'''


def comma_recognizer(input, pos):
    if input[pos] == ',':
        return input[pos:pos + 1]


def test_imported_recognizers_error_undefined_recognizer():

    with pytest.raises(GrammarError,
                       match=r'has no recognizer defined and no recognizers '
                       'are given'):
        Grammar.from_file(os.path.join(this_folder, 'model.pg'))

    # If we define COMMA recognizer grammar will construct without exceptions.
    g = Grammar.from_file(os.path.join(this_folder, 'model.pg'),
                          recognizers={'base.COMMA': comma_recognizer})
    assert g


def test_imported_recognizers_connect_from_external_file():
    g = Grammar.from_file(os.path.join(this_folder, 'model.pg'),
                          recognizers={'base.COMMA': comma_recognizer})

    # Check that recognizers are loaded and connected.
    rec_fqn = g.get_terminal('base.FQN')
    assert rec_fqn.recognizer
    assert type(rec_fqn.recognizer) is FunctionType
    assert rec_fqn.recognizer.__name__ == 'FQN'

    rec_fqn = g.get_terminal('base.NUMERIC_ID')
    assert rec_fqn.recognizer
    assert type(rec_fqn.recognizer) is FunctionType
    assert rec_fqn.recognizer.__name__ == 'number'


def test_imported_recognizers_override():
    """
    Test that recognizers loaded from `*_recognizers.py` files can be
    overriden by users provided recognizers.
    """

    called = [False, False]

    def numeric_id(input, pos):
        called[0] = True

    def fqn(input, pos):
        called[0] = True

    recognizers = {
        'base.COMMA': comma_recognizer,
        'base.NUMERIC_ID': numeric_id,
        'base.FQN': fqn
    }

    g = Grammar.from_file(os.path.join(this_folder, 'model.pg'),
                          recognizers=recognizers)
    assert g
    with pytest.raises(ParseError):
        Parser(g).parse(model_str)
    assert any(called)

    called = [False]

    def numeric_id(input, pos):
        called[0] = True
        return number(input, pos)

    recognizers = {
        'base.COMMA': comma_recognizer,
        'base.NUMERIC_ID': numeric_id,
    }

    g = Grammar.from_file(os.path.join(this_folder, 'model.pg'),
                          recognizers=recognizers)
    assert g
    Parser(g).parse(model_str)
    assert called[0]


def test_imported_recognizers_override_by_importing_grammar_file():
    """
    Test that recognizers loaded from `*_recognizers.py` files can be
    overriden in importing grammar `*_recognizers.py` file by providing
    FQN of the imported terminal relative from the importing grammar file.
    """

    g = Grammar.from_file(os.path.join(this_folder, 'model_override.pg'))
    assert g

    t = g.get_terminal('base.NUMERIC_ID')
    assert t is not None

    assert t.recognizer.__doc__ == 'Check override'
