import contextlib
import json
import os

from parglare import Grammar, Parser

this_folder = os.path.dirname(__file__)

input_str = """

package First
package Second {
    component packageComponent {

    }
}

module SomeModule {

    component myComponent {
        in SomeInputSlot
        out SomeOutputSlot
    }


}

"""


def test_diamond_import_resolving_and_model_creation():
    grammar_file = os.path.join(this_folder, "model.pg")
    table_file = os.path.join(this_folder, "model.pgc")
    table_cmp_file = os.path.join(this_folder, "model_compare.pgc")

    g = Grammar.from_file(grammar_file)
    with contextlib.suppress(Exception):
        os.remove(table_file)

    parser = Parser(g)

    # Check generated table file. The versioned cache wraps the unchanged table
    # serialization in metadata tied to this grammar/import closure.
    with open(table_file, encoding="utf-8") as source:
        generated = json.load(source)
    with open(table_cmp_file, encoding="utf-8") as source:
        expected_table = json.load(source)
    assert generated["table"] == expected_table
    assert generated["format_version"] == 1
    assert generated["grammar_fingerprint"]

    # Check that parser loaded from the table will correctly parse
    parser = Parser(g, force_load_table=True)

    model = parser.parse(input_str)
    assert model
    assert model.__class__.__name__ == "Model"
    assert isinstance(model.packages, list)
    assert len(model.packages) == 2
    assert model.packages[0].name == "First"
    assert isinstance(model.modules, list)
    assert len(model.modules) == 1

    packageComponent = model.packages[1].body.components[0]
    assert packageComponent.name == "packageComponent"

    module = model.modules[0]
    assert module.__class__.__name__ == "m.Module"
    assert module.name == "SomeModule"
    assert len(module.components) == 1

    component = module.components[0]
    assert type(component) is type(packageComponent)
    assert component.name == "myComponent"
    assert len(component.slots) == 2

    slot = component.slots[1]
    assert slot.__class__.__name__ == "packages.components.SlotOut"
    assert slot.name == "SomeOutputSlot"
