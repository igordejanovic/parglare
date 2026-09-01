import contextlib
import os
import time

from parglare import Grammar, Parser

this_folder = os.path.dirname(__file__)


def test_save_load_table():
    """
    Test basic table save/load cycle with table file creation.
    """
    calc_file = os.path.join(this_folder, "calc.pg")
    variable_file = os.path.join(this_folder, "variable.pg")
    input_str = "a = 5   1 + 2 * a - 7"
    input_str_result = 1 + 2 * 5 - 7
    grammar = Grammar.from_file(calc_file)

    table_file = os.path.join(this_folder, "calc.pgc")
    # remove table file if exists
    with contextlib.suppress(OSError):
        os.remove(table_file)

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

    # Changing an imported grammar must invalidate and regenerate the cache.
    with open(variable_file, encoding="utf-8") as source:
        original = source.read()
    try:
        with open(variable_file, "a", encoding="utf-8") as source:
            source.write("\n// cache invalidation test\n")
        parser = Parser(grammar)
        assert parser.parse(input_str) == input_str_result
        assert last_mtime < os.path.getmtime(table_file)
    finally:
        with open(variable_file, "w", encoding="utf-8") as source:
            source.write(original)

    # force_load_table is strict: it accepts only a cache matching the current
    # grammar contents, rather than trusting modification times.
    parser = Parser(grammar)
    last_mtime = os.path.getmtime(table_file)
    parser = Parser(grammar, force_load_table=True)
    assert last_mtime == os.path.getmtime(table_file)
