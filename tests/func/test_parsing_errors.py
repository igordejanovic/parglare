# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import pytest  # noqa
import os
from parglare.parser import Parser
from parglare.exceptions import ParseError
from .expression_grammar import get_grammar


def test_invalid_input():

    grammar = get_grammar()
    p = Parser(grammar)

    with pytest.raises(ParseError) as e:
        p.parse("id+id*+id")

    assert e.value.location.start_position == 6
    assert "(" in str(e)
    assert "id" in str(e)


def test_premature_end():

    grammar = get_grammar()
    p = Parser(grammar)

    with pytest.raises(ParseError) as e:
        p.parse("id+id*")

    assert e.value.location.start_position == 6
    assert "(" in str(e)
    assert "id" in str(e)


def test_line_column():
    grammar = get_grammar()
    p = Parser(grammar)

    try:
        p.parse("""id + id * id + id + error * id""")
    except ParseError as e:
        loc = e.location
        assert loc.start_position == 20
        assert loc.line == 1
        assert loc.column == 20

    try:
        p.parse("""id + id * id + id + error * id

        """)
    except ParseError as e:
        loc = e.location
        assert loc.start_position == 20
        assert loc.line == 1
        assert loc.column == 20

    try:
        p.parse("""

id + id * id + id + error * id""")
    except ParseError as e:
        loc = e.location
        assert loc.start_position == 22
        assert loc.line == 3
        assert loc.column == 20

    try:
        p.parse("""

id + id * id + id + error * id

        """)
    except ParseError as e:
        loc = e.location
        assert loc.start_position == 22
        assert loc.line == 3
        assert loc.column == 20


def test_file_name():
    "Test that file name is given in the error string when parsing file."
    grammar = get_grammar()
    p = Parser(grammar)

    input_file = os.path.join(os.path.dirname(__file__),
                              'parsing_errors.txt')

    try:
        p.parse_file(input_file)
    except ParseError as e:
        assert 'parsing_errors.txt' in str(e)
