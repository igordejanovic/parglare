from parglare.builder import GrammarBuilder


def test_builder_can_be_used_as_context_manager():
    with GrammarBuilder() as grammar_builder:
        grammar_builder.start('a')
        with grammar_builder.rule('a') as rule:
            with rule.production('b', 'c') as production:
                assert not production.closed
            assert production.closed
            assert not rule.closed
        assert rule.closed
        assert not grammar_builder.closed
    assert grammar_builder.closed
