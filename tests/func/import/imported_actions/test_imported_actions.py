import os
from parglare import Grammar, Parser

this_folder = os.path.dirname(__file__)


def test_imported_actions():
    g = Grammar.from_file(os.path.join(this_folder, 'model.pg'))

    input_str = '''
    modelID 42
    component myComponent {
        in SomeInputSlot
        out SomeOutputSlot
    }
    '''

    model = Parser(g).parse(input_str)
    # Check that base.pg actions are properly loaded and triggered.
    assert model.modelID == 42
