import pytest  # noqa
from parglare import Parser, ParseError, Grammar
from parglare.actions import pass_single

grammar = r"""
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
    will succeed.
    """

    parser = Parser(g, actions=actions, consume_input=False,
                    error_recovery=True)

    result = parser.parse("1 + 2 + * 3 & 89 - 5")

    # '*' after '+' will be dropped but when the parser reach '&'
    # it has a complete expression and will terminate successfully and
    # report only one error ('*' after '+').
    # The parser should thus calculate '1 + 2 + 3'
    assert result == 6

    assert len(parser.errors) == 1

    e = parser.errors[0]

    assert e.location.start_position == 8
    assert e.location.end_position == 10
    assert 'Error at 1:8:"1 + 2 +  **> * 3 & 89 -" => '\
        'Expected: ( or number but found <*(*)>' in str(e)


def test_error_recovery_complete():
    """
    In this test we are using complete parse.
    """
    parser = Parser(g, actions=actions, error_recovery=True)

    result = parser.parse("1 + 2 + * 3 & 89 - 5")

    # Both '*' and '& 89' should be dropped now as the parser expects to
    # consume all the input. Thus the parser should calculate '1 + 2 + 3 - 5'
    assert result == 1

    assert len(parser.errors) == 2

    e1, e2 = parser.errors

    assert e1.location.start_position == 8
    assert e1.location.end_position == 10

    # Characters of the second error should be packed as a single error
    # spanning the whole erroneous region. Whitespaces should be included too.
    assert e2.location.start_position == 12
    assert e2.location.end_position == 17
    assert 'Error at 1:12:"+ 2 + * 3  **> & 89 - 5" => '\
        'Expected: ) or * or + or - or / or STOP or ^' in str(e2)


def test_error_recovery_parse_error():
    """
    In this test we have error that can't be recovered from by a simple
    dropping of characters as we'll end up with invalid expression at the end
    of the input.

    The current solution is to throw ParseError at the beggining of the last
    error that couldn't be recovered from.
    """
    parser = Parser(g, actions=actions, error_recovery=True)

    with pytest.raises(ParseError) as einfo:
        parser.parse("1 + 2 + * 3 + & -")

    assert einfo.value.location.start_position == 14


def test_custom_error_recovery():
    """
    Test that registered callable for error recovery is called with the
    right parameters.
    """

    called = [False]

    def my_recovery(context, error):
        expected_symbols = context.state.actions.keys()
        called[0] = True
        assert isinstance(context.parser, Parser)
        assert context.input_str == '1 + 2 + * 3 - 5'
        assert context.position == 8
        open_par = g.get_terminal('(')
        assert open_par in expected_symbols
        number = g.get_terminal('number')
        assert number in expected_symbols
        context.position += 1
        return True

    parser = Parser(g, actions=actions, error_recovery=my_recovery)

    result = parser.parse("1 + 2 + * 3 - 5")

    assert result == 1

    # Assert that recovery handler is called.
    assert called[0]


def test_recovery_custom_unsuccessful():
    """
    Test unsuccessful error recovery.
    """

    def custom_recovery(context, error):
        return False

    parser = Parser(g, actions=actions, error_recovery=custom_recovery)

    with pytest.raises(ParseError) as e:
        parser.parse('1 + 5 8 - 2')

    error = e.value
    assert error.location.start_position == 6
