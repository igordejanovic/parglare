# -*- coding: utf-8 -*-
import pytest
from os.path import join, dirname
from parglare import Parser, Grammar
from ..grammar.expression_grammar import get_grammar
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
    Test `consume_input` parser parameter.
    """
    grammar = """
    S: 'a' B;
    B: 'b';
    """
    g = Grammar.from_string(grammar)
    parser = Parser(g, consume_input=False)

    # Parser should succesfuly parse 'ab' at the beginning.
    parser.parse('abc')

    # But if `consume_input` is not set to `False` it should be `True` by
    # default and the parser will not accept partial parses.
    grammar = """
    S: 'a' B;
    B: 'b';
    """
    g = Grammar.from_string(grammar)
    parser = Parser(g)
    parser.parse('a b')
    with pytest.raises(ParseError):
        parser.parse('a b c')
