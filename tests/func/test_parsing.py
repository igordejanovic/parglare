# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import pytest
from os.path import join, dirname
from parglare import Parser, Grammar, GLRParser
from .expression_grammar import get_grammar
from parglare.exceptions import ParseError


def test_parsing():
    grammar = get_grammar()
    p = Parser(grammar)
    assert p.parse("id+id+id")


def test_parsing_from_file():
    grammar = get_grammar()
    p = Parser(grammar)
    assert p.parse_file(join(dirname(__file__), 'parsing_from_file.txt'))


def test_partial_parse():
    """
    Not giving EOF at the end of the sequence enables parsing of the beginning
    of the input string.
    """
    grammar = """
    S: 'a' B;
    B: 'b';
    """
    g = Grammar.from_string(grammar)
    parser = Parser(g)

    # Parser should succesfuly parse 'ab' at the beggining.
    parser.parse('abc')

    # But if EOF is given it will match only at the end of the string,
    # thus, the whole string must be parsed in order for parsing to
    # succeed.
    grammar = """
    S: 'a' B EOF;
    B: 'b';
    """
    g = Grammar.from_string(grammar)
    parser = Parser(g)
    parser.parse('a b')
    with pytest.raises(ParseError):
        parser.parse('a b c')


# TODO name this test accordingly to what it actually tests
def test_overlapping_terminals():
    g = Grammar.from_string("""
    expression: "1" s letter EOF
              | "2" s "A" EOF
              ;

    s: " ";

    terminals
    letter: /[A-Z]/;

    """)

    p = GLRParser(g, ws='')

    p.parse("2 A")
    p.parse("1 B")
    p.parse("1 A")
