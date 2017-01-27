import pytest
from parglare.parser import Parser
from parglare.exceptions import ParseError
from .expression_grammar import get_grammar, E


def test_invalid_input():

    grammar = get_grammar()
    p = Parser(grammar, E)

    try:
        p.parse("id+id*+id")
    except ParseError as e:
        assert e.position == 6
        symbol_names = [s.name for s in e.symbols]
        assert "(" in symbol_names
        assert "id" in symbol_names
        assert len(symbol_names) == 2


def test_premature_end():

    grammar = get_grammar()
    p = Parser(grammar, E)

    try:
        p.parse("id+id*")
    except ParseError as e:
        assert e.position == 6
        symbol_names = [s.name for s in e.symbols]
        assert "(" in symbol_names
        assert "id" in symbol_names
        assert len(symbol_names) == 2


def test_line_column():
    grammar = get_grammar()
    p = Parser(grammar, E)

    try:
        p.parse("""id + id * id + id + error * id""")
    except ParseError as e:
        assert e.position == 20
        assert e.line == 1
        assert e.column == 20

    try:
        p.parse("""id + id * id + id + error * id

        """)
    except ParseError as e:
        assert e.position == 20
        assert e.line == 1
        assert e.column == 20

    try:
        p.parse("""

id + id * id + id + error * id""")
    except ParseError as e:
        assert e.position == 22
        assert e.line == 3
        assert e.column == 20

    try:
        p.parse("""

id + id * id + id + error * id

        """)
    except ParseError as e:
        assert e.position == 22
        assert e.line == 3
        assert e.column == 20
