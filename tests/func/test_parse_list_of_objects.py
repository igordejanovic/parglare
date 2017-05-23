import pytest  # noqa
from parglare import Grammar, Parser
from parglare.exceptions import ParseError
from parglare.actions import pass_single, collect


def test_parse_list_of_integers():

    grammar = """
    Numbers = all_less_than_five EOF;
    all_less_than_five = all_less_than_five int_less_than_five
                         | int_less_than_five;
    """

    def int_less_than_five(input, pos):
        if input[pos] < 5:
            return [input[pos]]

    recognizers = {
        'int_less_than_five': int_less_than_five
    }
    g = Grammar.from_string(grammar, recognizers=recognizers, debug=True)

    actions = {
        'Numbers': pass_single,
        'all_less_than_five': collect,
        'int_less_than_five': pass_single
    }
    parser = Parser(g, actions=actions)

    ints = [3, 4, 1, 4]
    p = parser.parse(ints)
    assert p == ints

    # Test that error is correctly reported.
    with pytest.raises(ParseError) as e:
        parser.parse([4, 2, 1, 6, 3])
    assert 'Error at position 1,3 => "[4, 2, 1]*[6, 3]".' in str(e)
    assert 'int_less_than_five' in str(e)
