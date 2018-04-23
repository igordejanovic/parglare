import os
from parglare import Grammar, Parser

this_folder = os.path.dirname(__file__)


def test_diamond_import():
    g = Grammar.from_file(os.path.join(this_folder, 'model.pg'))
    assert g
    assert g.get_terminal('packages.base.COMMA')
    assert g.get_nonterminal('Model')

    # First path used for import of Component is going
    # modules->components->Component
    assert g.get_nonterminal('m.c.Component')

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

    model = Parser(g).parse(input_str)
    assert model
    assert model.__class__.__name__ == 'Model'
    assert type(model.packages) is list
    assert len(model.packages) == 2
    assert model.packages[0].name == 'First'
    assert type(model.modules) is list
    assert len(model.modules) == 1

    module = model.modules[0]
    assert module.__class__.__name__ == 'm.Module'
    assert module.name == 'SomeModule'
    assert len(module.components) == 1

    component = module.components[0]
    assert component.name == 'myComponent'
    assert len(component.slots) == 2

    slot = component.slots[1]
    assert slot.__class__.__name__ == 'm.c.SlotOut'
    assert slot.name == 'SomeOutputSlot'
