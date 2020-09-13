from parglare.builder import GrammarBuilder


def test_end_closes_builder():
    """When end() is called on a builder, it is closed."""
    grammar_builder = GrammarBuilder()
    grammar_builder.start('a')
    rule_builder = grammar_builder.rule('a')
    production_builder = rule_builder.production('b', 'c')
    terminal_builder = grammar_builder.terminal('b', 'b')
    assert not grammar_builder.closed
    assert not rule_builder.closed
    assert not production_builder.closed
    assert not terminal_builder.closed
    production_builder.end()
    assert not grammar_builder.closed
    assert not rule_builder.closed
    assert production_builder.closed
    assert not terminal_builder.closed
    rule_builder.end()
    assert not grammar_builder.closed
    assert rule_builder.closed
    assert production_builder.closed
    assert not terminal_builder.closed
    terminal_builder.end()
    assert not grammar_builder.closed
    assert rule_builder.closed
    assert production_builder.closed
    assert terminal_builder.closed
    grammar_builder.end()
    assert grammar_builder.closed
    assert rule_builder.closed
    assert production_builder.closed
    assert terminal_builder.closed


def test_calling_end_twice_is_safe():
    """When end() has already been called, subsequent calls are no-ops."""
    grammar_builder = GrammarBuilder()
    grammar_builder.start('a')
    rule_builder = grammar_builder.rule('a')
    production_builder = rule_builder.production('b', 'c')
    production_builder.end()
    production_builder.end()
    rule_builder.end()
    rule_builder.end()
    grammar_builder.end()
    grammar_builder.end()


def test_end_closes_children():
    """When GrammarBuilder.end() is called, the children are closed as well."""
    grammar_builder = GrammarBuilder()
    grammar_builder.start('a')
    rule_builder = grammar_builder.rule('a')
    production_builder = rule_builder.production('b', 'c')
    assert not grammar_builder.closed
    assert not rule_builder.closed
    assert not production_builder.closed
    grammar_builder.end()
    assert grammar_builder.closed
    assert rule_builder.closed
    assert production_builder.closed


def test_to_string_auto_closes():
    """When GrammarBuilder.to_string is called, the builder automatically closes first."""
    grammar_builder = GrammarBuilder()
    grammar_builder.start('a')
    grammar_builder.rule('a').production('b', 'c')
    assert not grammar_builder.closed
    grammar_builder.to_string()
    assert grammar_builder.closed


def test_get_struct_auto_closes():
    """When GrammarBuilder.get_struct is called, the builder automatically closes first."""
    grammar_builder = GrammarBuilder()
    grammar_builder.start('a')
    grammar_builder.rule('a').production('b', 'c')
    assert not grammar_builder.closed
    grammar_builder.get_struct()
    assert grammar_builder.closed
