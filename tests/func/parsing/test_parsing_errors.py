# -*- coding: utf-8 -*-
import pytest  # noqa
import os
from parglare import Grammar, Parser, GLRParser, ParseError
from ..grammar.expression_grammar import get_grammar


parsers = pytest.mark.parametrize("parser_class", [Parser, GLRParser])


@parsers
def test_grammar_in_error(parser_class):

    grammar = get_grammar()
    p = parser_class(grammar)

    with pytest.raises(ParseError) as e:
        p.parse("id+id*+id")

    assert e.value.grammar is grammar


def test_glr_last_heads_in_error():

    grammar = get_grammar()
    p = GLRParser(grammar)

    with pytest.raises(ParseError) as e:
        p.parse("id+id*+id")

    assert len(e.value.last_heads) == 1


@parsers
def test_invalid_input(parser_class):

    grammar = get_grammar()
    p = parser_class(grammar)

    with pytest.raises(ParseError) as e:
        p.parse("id+id*+id")

    assert e.value.location.start_position == 6
    assert "(" in str(e.value)
    assert "id" in str(e.value)
    assert '*' in [s.name for s in e.value.symbols_before]
    assert '+' in [t.value for t in e.value.tokens_ahead]
    expected_names = [s.name for s in e.value.symbols_expected]
    assert 'id' in expected_names
    assert '(' in expected_names


@parsers
def test_premature_end(parser_class):

    grammar = get_grammar()
    p = parser_class(grammar)

    with pytest.raises(ParseError) as e:
        p.parse("id+id*")

    assert e.value.location.start_position == 6
    expected_names = [s.name for s in e.value.symbols_expected]
    assert 'id' in expected_names
    assert '(' in expected_names
    assert '*' in [s.name for s in e.value.symbols_before]
    assert e.value.tokens_ahead == []


def test_ambiguous_glr():
    grammar = r"""
    E: E '+' E
     | E '*' E
     | number;

    terminals
    number: /\d+(\.\d+)?/;
    """
    g = Grammar.from_string(grammar)
    parser = GLRParser(g)

    with pytest.raises(ParseError) as e:
        parser.parse("1 + 2 * 3 / 5")

    assert e.value.location.start_position == 10
    assert 'number' in [s.name for s in e.value.symbols_before]


@parsers
def test_line_column(parser_class):
    grammar = get_grammar()
    p = parser_class(grammar)

    with pytest.raises(ParseError) as e:
        p.parse("""id + id * id + id + error * id""")

    loc = e.value.location
    assert loc.start_position == 20
    assert loc.line == 1
    assert loc.column == 20

    with pytest.raises(ParseError) as e:
        p.parse("""id + id * id + id + error * id

        """)
    loc = e.value.location
    assert loc.start_position == 20
    assert loc.line == 1
    assert loc.column == 20

    with pytest.raises(ParseError) as e:
        p.parse("""

id + id * id + id + error * id""")
    loc = e.value.location
    assert loc.start_position == 22
    assert loc.line == 3
    assert loc.column == 20

    with pytest.raises(ParseError) as e:
        p.parse("""

id + id * id + id + error * id

        """)
    loc = e.value.location
    assert loc.start_position == 22
    assert loc.line == 3
    assert loc.column == 20


@parsers
def test_file_name(parser_class):
    "Test that file name is given in the error string when parsing file."
    grammar = get_grammar()
    p = parser_class(grammar)

    input_file = os.path.join(os.path.dirname(__file__),
                              'parsing_errors.txt')

    with pytest.raises(ParseError) as e:
        p.parse_file(input_file)

    assert 'parsing_errors.txt' in str(e.value)
    assert 'parsing_errors.txt' in e.value.location.file_name
