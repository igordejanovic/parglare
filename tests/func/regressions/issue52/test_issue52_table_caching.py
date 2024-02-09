import contextlib
import os

from parglare import Grammar, Parser


def test_table_from_cache_different_than_calculated():
    this_folder = os.path.dirname(__file__)
    grammar_file = os.path.join(this_folder, 'grammar.pg')
    table_file = os.path.join(this_folder, 'grammar.pgt')
    with contextlib.suppress(Exception):
        os.remove(table_file)

    g = Grammar.from_file(grammar_file)

    p = Parser(g)
    without_cache = p.parse('dynamic("OS")')

    p = Parser(g)
    with_cache = p.parse('dynamic("OS")')

    assert without_cache == with_cache
