import os
from parglare import Grammar, Parser

this_folder = os.path.dirname(__file__)


def test_recursive_grammar_import():
    g = Grammar.from_file(os.path.join(this_folder, 'model.pg'))
    assert g

    input_str = '''

    package First
    package Second

    module SomeModule {

        component myComponent {
            in SomeInputSlot
            out SomeOutputSlot
        }


    }

    '''

    result = Parser(g).parse(input_str)
    assert result
