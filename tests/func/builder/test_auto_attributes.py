import pytest

from parglare.builder import GrammarBuilder


def test_bad_attribute():
    """If an attribute is requested that doesn't exist on the builder or any builder above it in the hierarchy,
    an AttributeError is raised."""
    with pytest.raises(AttributeError):
        GrammarBuilder().no_such_method()
    with pytest.raises(AttributeError):
        GrammarBuilder().rule('a').no_such_method()
    with pytest.raises(AttributeError):
        GrammarBuilder().rule('a').production('b').no_such_method()
    with pytest.raises(AttributeError):
        GrammarBuilder().terminal('a', 'a').no_such_method()


def test_parent_attribute():
    """If an attribute is requested that doesn't exist on the builder but does exist for some builder above it in the
    hierarchy, builders up to but not including the one with the attribute are closed and the attribute is returned."""

    grammar_builder = GrammarBuilder()
    rule_builder = grammar_builder.rule('a')
    production_builder = rule_builder.production('b', 'c')
    assert not rule_builder.closed
    assert not production_builder.closed
    assert rule_builder.get_struct == grammar_builder.get_struct
    assert production_builder.closed
    assert rule_builder.closed
    assert not grammar_builder.closed

    rule_builder2 = grammar_builder.rule('b')
    production_builder2 = rule_builder2.production('c', 'd')
    assert not rule_builder2.closed
    assert not production_builder2.closed
    assert production_builder2.production == rule_builder2.production
    assert production_builder2.closed
    assert not rule_builder2.closed
    assert not grammar_builder.closed
