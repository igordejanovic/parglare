from parglare import Grammar, Parser, GLRParser

grammar = r"""
S: A A B;
A: letter;
B: letter | EMPTY;

terminals
letter: /\w/;
"""

expression = "ab"


def test_positions():
    """
    See https://github.com/igordejanovic/parglare/issues/110
    """
    g = Grammar.from_string(grammar)
    parser = Parser(g, build_tree=True)
    result = parser.parse(expression)

    assert result.start_position == 0
    assert result.end_position == 2


def test_positions_glr():
    """
    See https://github.com/igordejanovic/parglare/issues/110
    """
    g = Grammar.from_string(grammar)
    parser = GLRParser(g, build_tree=True)
    result = parser.parse(expression)

    assert result[0].start_position == 0
    assert result[0].end_position == 2
