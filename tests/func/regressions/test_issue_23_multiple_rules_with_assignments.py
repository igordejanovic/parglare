from parglare import Grammar, Parser


def test_multiple_rules_with_assignments():
    '''
    See https://github.com/igordejanovic/parglare/issues/23
    '''

    text = "a"

    grammar_str = """\
    A : "a" ;
    A : "b" ;
    """

    grammar = Grammar.from_string(grammar_str)
    parser = Parser(grammar)
    result = parser.parse(text)
    assert result == 'a'

    grammar_str = """\
    A : t="a" | t="b" ;
    """

    grammar = Grammar.from_string(grammar_str)
    parser = Parser(grammar)
    result = parser.parse(text)
    assert type(result).__name__ == 'A'
    assert result.t == 'a'

    # Must be equvalent with the previous
    grammar_str = """\
    A : t="a" ;
    A : t="b" ;
    """

    grammar = Grammar.from_string(grammar_str)
    parser = Parser(grammar)
    result = parser.parse(text)
    assert type(result).__name__ == 'A'
    assert result.t == 'a'
