import pytest  # noqa
import os
import tempfile
from parglare import Grammar
from parglare.tables import create_table
from parglare.export import grammar_pda_export


def test_dot_export():
    grammar = 'S: S S | S S S | "b";'
    g = Grammar.from_string(grammar)

    table = create_table(g)

    tmp_dir = tempfile.mkdtemp()
    file_name = os.path.join(tmp_dir, 'testexport.dot')

    grammar_pda_export(table, file_name)

    with open(file_name) as f:
        assert 'label' in f.read()

    os.remove(file_name)
    os.rmdir(tmp_dir)
