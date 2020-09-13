# -*- coding: utf-8 -*-
import pytest

from parglare.builder import GrammarBuilder
from parglare.exceptions import GrammarBuilderValidationError


def test_iter_validation_errors_does_not_raise_error():
    for _ in GrammarBuilder().iter_validation_errors():
        pass
    for _ in GrammarBuilder().rule('a').iter_validation_errors():
        pass
    for _ in GrammarBuilder().rule('a').production().iter_validation_errors():
        pass
    for _ in GrammarBuilder().terminal('a').iter_validation_errors():
        pass


def test_missing_start():
    """If no start symbol is set, builder complains when getting results."""
    with pytest.raises(GrammarBuilderValidationError):
        GrammarBuilder().get_struct()


def test_undefined_start():
    """If start symbol has no rule, builder complains when getting results."""
    with pytest.raises(GrammarBuilderValidationError):
        GrammarBuilder().start('a').get_struct()


def test_terminal_start():
    """If start symbol is a terminal, builder complains when getting results."""
    with pytest.raises(GrammarBuilderValidationError):
        GrammarBuilder().start('a').terminal('a', 'a').get_struct()


def test_start_redefinition():
    """If start is set multiple times, builder complains when getting results."""
    with pytest.raises(GrammarBuilderValidationError):
        GrammarBuilder().start('a').start('b')


def test_rule_redefinition():
    """If symbol is already used in a rule, builder complains when adding second rule."""
    with pytest.raises(GrammarBuilderValidationError):
        GrammarBuilder().rule('a').production('b').rule('a')


def test_rule_to_terminal_redefinition():
    """If symbol is already used in a rule, builder complains when adding a terminal."""
    with pytest.raises(GrammarBuilderValidationError):
        GrammarBuilder().rule('a').production('b').terminal('a', 'a')


def test_terminal_redefinition():
    """If symbol is already used in a terminal, builder complains when adding second terminal."""
    with pytest.raises(GrammarBuilderValidationError):
        GrammarBuilder().terminal('a', 'a').terminal('a', 'a')


def test_terminal_to_rule_redefinition():
    """If symbol is already used in a terminal, builder complains when adding a rule."""
    with pytest.raises(GrammarBuilderValidationError):
        GrammarBuilder().terminal('a', 'a').rule('a')


def test_validation_recovery():
    """If a validation error occurs, changes are discarded and the parent builder is still usable."""
    grammar_builder = GrammarBuilder()
    grammar_builder.start('a')
    grammar_builder.rule('a').production('b', 'c').end().end()
    with pytest.raises(GrammarBuilderValidationError):
        grammar_builder.rule('a').end()
    grammar_builder.rule('b').production('c', 'd').end().end()
    struct = grammar_builder.get_struct()
    target = {
        'start': 'a',
        'rules': {'a': {'productions': [{'production': ['b', 'c']}]},
                  'b': {'productions': [{'production': ['c', 'd']}]}},
        'terminals': {}
    }
    assert struct == target
