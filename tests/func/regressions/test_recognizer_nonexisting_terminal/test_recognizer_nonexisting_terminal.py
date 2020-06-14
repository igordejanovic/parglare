# -*- coding: utf-8 -*-
import pytest  # noqa
from os.path import join, dirname
from parglare import Grammar, GrammarError


def test_recognizer_for_unexisting_terminal_raises_exception():
    """
    If a recognizer is given for a terminal that can't be found in the grammar
    raise an exception.
    """

    with pytest.raises(GrammarError,
                       match=r'.*given for unknown terminal "B".'):
        Grammar.from_file(join(dirname(__file__), 'grammar.pg'))
