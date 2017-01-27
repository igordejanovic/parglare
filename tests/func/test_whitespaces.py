import pytest
from parglare.parser import Parser
from parglare.exceptions import ParseError
from .expression_grammar import get_grammar, E


def test_default_whitespaces():

    grammar = get_grammar()
    p = Parser(grammar, E)

    p.parse("""id+  id * (id
    +id  )
    """)


def test_whitespace_redefinition():

    grammar = get_grammar()

    # Make newline treated as non-ws characted
    p = Parser(grammar, E, ws=' \t')

    p.parse("""id+  id * (id +id  ) """)

    try:
        p.parse("""id+  id * (id
        +id  )
        """)
    except ParseError as e:
        assert e.position == 13


def test_whitespace_noskip():

    grammar = get_grammar()

    # Make newline treated as non-ws characted
    p = Parser(grammar, E, skip_ws=False)

    try:
        p.parse("""id+  id * (id +id  ) """)
    except ParseError as e:
        assert e.position == 3
