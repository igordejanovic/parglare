import pytest  # noqa
from parglare import Parser, ParseError, Grammar
from parglare.actions import pass_single

grammar = r"""
Result: E EOF;
E: E '+' E  {left, 1}
 | E '-' E  {left, 1}
 | E '*' E  {left, 2}
 | E '/' E  {left, 2}
 | E '^' E  {right, 3}
 | '(' E ')'
 | number;

terminals
number: /\d+(\.\d+)?/;
"""

actions = {
    "Result": pass_single,
    "E": [lambda _, nodes: nodes[0] + nodes[2],
          lambda _, nodes: nodes[0] - nodes[2],
          lambda _, nodes: nodes[0] * nodes[2],
          lambda _, nodes: nodes[0] / nodes[2],
          lambda _, nodes: nodes[0] ** nodes[2],
          lambda _, nodes: nodes[1],
          lambda _, nodes: nodes[0]],
    "number": lambda _, value: float(value),
}

g = Grammar.from_string(grammar)


def test_error_recovery_uncomplete():
    """
    Test default recovery for partial parse.
    parglare will try to parse as much as possible for the given grammar and
    input. If the current input can be reduced to the start rule the parse
    will succeed. In order to prevent partial parse first grammar rule should
    be ended with EOF like in the case of 'Result' rule.
    """
    parser = Parser(g, start_production=2, actions=actions,
                    error_recovery=True, debug=True)

    result = parser.parse("1 + 2 + * 3 & 89 - 5")

    # '*' after '+' will be droped but when the parser reach '&'
    # it has a complete expression and will terminate successfuly and
    # report only one error ('*' after '+').
    # The parser should thus calculate '1 + 2 + 3'
    assert result == 6

    assert len(parser.errors) == 1

    e = parser.errors[0]

    assert e.position == 8
    assert e.length == 1
    assert 'Unexpected input at position (1, 8). Expected' in str(e)


def test_error_recovery_complete():
    """
    In this test we start from the 'Result' rule so parglare will require
    input to end with 'EOF' for the parse to be successful.
    """
    parser = Parser(g, actions=actions, error_recovery=True)

    result = parser.parse("1 + 2 + * 3 & 89 - 5")

    # Both '*' and '& 89' should be dropped now as the parser expects EOF at
    # the end. Thus the parser should calculate '1 + 2 + 3 - 5'
    assert result == 1

    assert len(parser.errors) == 2

    e1, e2 = parser.errors

    assert e1.position == 8
    assert e1.length == 1

    # Characters of the second error should be packed as a single error
    # spanning the whole erroneous region. Whitespaces should be included too.
    assert e2.position == 12
    assert e2.length == 4
    assert 'Unexpected input at position (1, 12)' in str(e2)


def test_error_recovery_parse_error():
    """In this test we have error that can't be recovered from by a simple
    dropping of characters as we'll end up with invalid expression at the EOF.

    The current solution is to throw ParseError at the beggining of the last
    error that couldn't be recovered from.

    """
    parser = Parser(g, actions=actions, error_recovery=True, debug=True)

    with pytest.raises(ParseError) as einfo:
        parser.parse("1 + 2 + * 3 + & -")

    assert einfo.value.location.start_position == 14


def test_custom_error_recovery():
    """
    Test that registered callable for error recovery is called with the
    right parameters.
    """

    called = [False]

    def my_recovery(parser, input, position, expected_symbols):
        called[0] = True
        assert isinstance(parser, Parser)
        assert input == '1 + 2 + * 3 - 5'
        assert position == 8
        assert type(expected_symbols) is set
        open_par = g.get_terminal('(')
        assert open_par in expected_symbols
        number = g.get_terminal('number')
        assert number in expected_symbols
        return None, None, position + 1

    parser = Parser(g, actions=actions, error_recovery=my_recovery, debug=True)

    result = parser.parse("1 + 2 + * 3 - 5")

    assert result == 1

    # Assert that recovery handler is called.
    assert called[0]
