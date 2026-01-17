from os.path import dirname, join
import weakref
import gc
import pytest

from parglare import Parser, GLRParser, Grammar, SyntaxError

@pytest.mark.parametrize("parser_type", [Parser, GLRParser])
def test_parser_memory_leak_through_storing_exception_instance(parser_type):
    this_folder = dirname(__file__)

    class Dummy:
        pass

    dummy = Dummy()
    dummy_ref = weakref.ref(dummy)

    grammar = Grammar.from_file(join(this_folder, "first.pg"))
    parser = parser_type(grammar)

    def raises_exception():
        _ = dummy  # Capture dummy in closure
        parser.parse("e e x")  # Invalid input to trigger SyntaxError

    try:
        raises_exception()
    except SyntaxError:
        pass

    del raises_exception
    del dummy

    gc.collect()

    assert dummy_ref() is None, "Parser is holding onto exception traceback"

    #import objgraph
    #objgraph.show_backrefs(dummy_ref(), 10, filename="parglare_parser_backrefs.png")

