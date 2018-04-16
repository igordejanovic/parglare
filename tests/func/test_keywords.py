"""
Test special KEYWORD rule.
"""
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import pytest
from parglare import Parser, Grammar, RegExRecognizer, StringRecognizer
from parglare.exceptions import GrammarError, ParseError


def test_keyword_must_be_regex():
    grammar = r"""
    S: "for" name=ID "=" from=INT "to" to=INT;

    terminals
    KEYWORD: "id";
    ID: /\w+/;
    INT: /\d+/;
    """

    with pytest.raises(GrammarError) as e:
        Grammar.from_string(grammar)

    assert 'must have a regex recognizer defined' in str(e)


def test_keyword_grammar_init():
    grammar = r"""
    S: "for" name=ID "=" from=INT "to" to=INT;

    terminals
    KEYWORD: /\w+/;
    ID: /\w+/;
    INT: /\d+/;
    """

    g = Grammar.from_string(grammar)

    # 'for' term matches KEYWORD rule so it'll be replaced by
    # RegExRecognizer instance.
    for_term = g.get_terminal('for')
    assert type(for_term.recognizer) is RegExRecognizer
    assert for_term.recognizer._regex == r'\bfor\b'

    # '=' term doesn't match KEYWORD rule so it will not change
    eq_term = g.get_terminal('=')
    assert type(eq_term.recognizer) is StringRecognizer


def test_keyword_matches_on_word_boundary():
    grammar = r"""
    S: "for" name=ID "=" from=INT "to" to=INT EOF;

    terminals
    ID: /\w+/;
    INT: /\d+/;
    """

    g = Grammar.from_string(grammar)

    parser = Parser(g)
    # This will not raise an error
    parser.parse('forid=10 to20')

    # We add KEYWORD rule to the grammar to match ID-like keywords.
    grammar += r"KEYWORD: /\w+/;"

    g = Grammar.from_string(grammar)
    parser = Parser(g)
    with pytest.raises(ParseError) as e:
        # This *will* raise an error
        parser.parse('forid=10 to20')
    assert '"*forid=10 t" => Expected: for' in str(e)
    with pytest.raises(ParseError) as e:
        # This *will* also raise an error
        parser.parse('for id=10 to20')
    assert 'Expected: to' in str(e)

    # But this is OK
    parser.parse('for id=10 to 20')
    parser.parse('for for=10 to 20')


def test_keyword_preferred_over_regexes():
    """
    Test that keyword matches (internally converted to regex matches) are
    preferred over ordinary regex matches of the same length.
    """

    grammar = r"""
    S: "for"? name=ID? "=" from=INT "to" to=INT EOF;

    terminals
    ID: /\w+/;
    INT: /\d+/;
    KEYWORD: /\w+/;
    """
    g = Grammar.from_string(grammar)

    parser = Parser(g)

    # 'for' is ambiguous as it can be keyword or ID(name)
    # ParseError could be thrown but parglare will prefer
    # StringRecognizer and keywords over RegExRecognizer for
    # the match of the same lenght (i.e. "more specific match")
    parser.parse("for = 10 to 100")
