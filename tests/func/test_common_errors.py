import pytest  # noqa
from parglare import Grammar, Parser
from parglare.exceptions import GrammarError


def test_infinite_recursions():
    """
    If rule have no recursion termination alternative as for example:

    Elements: Elements Element;

    instead of:
    Elements: Elements Element | Element;

    first set of "Elements" will be empty. GrammarError will be produced during
    parser construction.
    """

    grammar = """
    Elements: Elements Element;
    Element: "a" | "b";
    """

    g = Grammar.from_string(grammar)

    with pytest.raises(GrammarError) as e:
        Parser(g)

    assert 'First set empty for grammar symbol "Elements"' in str(e)
    assert 'infinite recursion' in str(e)


def todo_test_grammar_without_valid_inputs():
    """
    TODO: There is no valid input for this grammar. This should be detected by
    the parser.
   """
    grammar = """
    S: A | B;
    A: '1' S '1';
    B: '0' S '0';
    """

    g = Grammar.from_string(grammar)
    p = Parser(g)
    p.parse('0101000110001010')
