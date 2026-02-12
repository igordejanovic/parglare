import contextlib
import gc
import weakref
from os.path import dirname, join

import pytest

from parglare import GLRParser, Grammar, Parser, SyntaxError


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
        nonlocal dummy
        _ = dummy  # Capture dummy in closure
        parser.parse("e e x")  # Invalid input to trigger SyntaxError

    with contextlib.suppress(SyntaxError):
        raises_exception()

    del raises_exception
    del dummy

    gc.collect()

    assert dummy_ref() is None, "Parser is holding onto exception traceback"

    # import objgraph
    # objgraph.show_backrefs(dummy_ref(), 10, filename="parglare_parser_backrefs.png")


@pytest.mark.parametrize("parser_type", [Parser, GLRParser])
def test_parser_memory_leak(parser_type):
    this_folder = dirname(__file__)

    grammar = Grammar.from_file(join(this_folder, "first.pg"))
    parser = parser_type(grammar)
    parser_ref = weakref.ref(parser)

    # parser instance should be deallocated on delete as long as we are not
    # holding onto parse result
    parser.parse("e e")
    del parser

    gc.collect()

    assert parser_ref() is None, "Parser is not deallocated"
