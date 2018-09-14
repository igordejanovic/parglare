import os
import time
from parglare import Grammar, Parser

this_folder = os.path.dirname(__file__)


def test_save_load_table():
    """
    Test basic table save/load cycle with table file creation.
    """
    calc_file = os.path.join(this_folder, 'calc.pg')
    variable_file = os.path.join(this_folder, 'variable.pg')
    input_str = 'a = 5   1 + 2 * a - 7'
    input_str_result = 1 + 2 * 5 - 7
    grammar = Grammar.from_file(calc_file)

    table_file = os.path.join(this_folder, 'calc.pgt')
    # remove table file if exists
    try:
        os.remove(table_file)
    except OSError:
        pass

    parser = Parser(grammar)
    assert parser.parse(input_str) == input_str_result

    # Table file must be produced by parser construction.
    assert os.path.exists(table_file)

    last_mtime = os.path.getmtime(table_file)
    time.sleep(1)

    parser = Parser(grammar)

    # Last generated table should be used during parser construction.
    # Currently, it is hard to check this so we'll only check if
    # table_file is not regenerated.
    assert last_mtime == os.path.getmtime(table_file)
    # Parser constructed from persisted table should produce the same result.
    assert parser.parse(input_str) == input_str_result

    # We are now touching variable.pg file
    # This should trigger table file regeneration
    with open(variable_file, 'a'):
        os.utime(variable_file, None)
    parser = Parser(grammar)
    assert parser.parse(input_str) == input_str_result
    # We verify that the table file is newer.
    assert last_mtime < os.path.getmtime(table_file)

    # Now we test that force_load_table will load table even if not
    # newer than the grammar.
    time.sleep(1)
    with open(variable_file, 'a'):
        os.utime(variable_file, None)
    last_mtime = os.path.getmtime(table_file)
    parser = Parser(grammar, force_load_table=True)
    assert last_mtime == os.path.getmtime(table_file)
    parser = Parser(grammar)
    assert last_mtime < os.path.getmtime(table_file)
