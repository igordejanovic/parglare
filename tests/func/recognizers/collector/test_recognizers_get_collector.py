import pytest
import os
import re
from parglare import get_collector, Parser, Grammar, GrammarError

THIS_FOLDER = os.path.abspath(os.path.dirname(__file__))


def test_recognizer_explicit_get_collector():
    """
    Test the basic usage of `get_collector` API where we don't provide
    recognizers in a separate python module.
    """

    recognizer = get_collector()

    @recognizer
    def INT(input, pos):
        return re.compile(r'\d+').match(input[pos:])

    @recognizer
    def STRING(input, pos):
        return re.compile(r'\d+').match(input[pos:])

    grammar = Grammar.from_file(os.path.join(THIS_FOLDER, 'grammar.pg'),
                                recognizers=recognizer.all)
    parser = Parser(grammar)
    assert parser


def test_recognizer_explicit_get_collector_missing_recognizer():
    """
    Test when `get_collector` has a terminal without defined recognizer an
    exception is raised.
    """

    recognizer = get_collector()

    @recognizer
    def INT(input, pos):
        return re.compile(r'\d+').match(input[pos:])

    with pytest.raises(GrammarError,
                       match=r'Terminal "STRING" has no recognizer defined.'):
        Grammar.from_file(os.path.join(THIS_FOLDER, 'grammar.pg'),
                          recognizers=recognizer.all)


def test_recognizer_explicit_get_collector_recognizer_for_unexisting_terminal():  # noqa
    """
    Test for situation when `get_collector` has a recognizer for un-existing
    terminal.
    """

    recognizer = get_collector()

    @recognizer
    def INT(input, pos):
        return re.compile(r'\d+').match(input[pos:])

    @recognizer
    def STRING(input, pos):
        return re.compile(r'\d+').match(input[pos:])

    @recognizer
    def STRING2(input, pos):
        return re.compile(r'\d+').match(input[pos:])

    grammar = Grammar.from_file(os.path.join(THIS_FOLDER, 'grammar.pg'),
                                recognizers=recognizer.all)
    parser = Parser(grammar)
    assert parser
