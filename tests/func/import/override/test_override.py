import os

import pytest

from parglare import Grammar, GrammarError, Parser

this_folder = os.path.dirname(__file__)


def test_override_base():
    """
    Test overrides with two level of nesting.
    """
    g = Grammar.from_file(os.path.join(this_folder, 'base.pg'))
    p = Parser(g)
    result = p.parse('bb bb k bb')
    assert result


def test_override_first():
    """
    Loading grammar from the lower level of import hierarchy works correctly
    also.
    """
    g = Grammar.from_file(os.path.join(this_folder, 'first.pg'))
    p = Parser(g)
    result = p.parse('bf bf sec bf sec bf')
    assert result


def test_override_nonexisting_symbol():
    """
    Test override that doesn't exist. By default it could go unnoticed and
    the intended rule would not be overriden. This verifies that typo errors
    would not go unnoticed.
    """
    with pytest.raises(GrammarError,
                       match='Unexisting name for symbol override f.NonExisting'):
        Grammar.from_file(os.path.join(this_folder, 'nonexisting.pg'))
