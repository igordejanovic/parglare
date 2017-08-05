import pytest  # noqa
import os
from tempfile import mkstemp
from parglare import Grammar
from parglare.tables import create_table
from parglare.export import grammar_pda_export


def test_dot_export():
    grammar = 'S: S S | S S S | "b";'
    g = Grammar.from_string(grammar)

    table = create_table(g)

    f, file_name = mkstemp()
    grammar_pda_export(table, file_name)

    assert os.path.exists(file_name)
    with open(file_name) as f:
        assert 'label' in f.read()

    os.remove(file_name)
