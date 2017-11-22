import pytest
from parglare import Grammar, GrammarError


def test_terminal_exists_noerror_on_terminal_definition_before():
    """
    Test for regression bug where error is not reported if terminal is
    defined before its usage in production by a literal str match.
    """
    grammar = """
    Program: "begin"
             statements=Statement*
             ProgramEnd EOF;
    ProgramEnd: "end"; // here we are registering a terminal
    Statement: "end" "transaction"  // here we are making the same terminal
                                    // instead of using a name reference
             | "command";
    """

    with pytest.raises(GrammarError) as e:
        Grammar.from_string(grammar)

    assert 'already exists by the name' in str(e)
