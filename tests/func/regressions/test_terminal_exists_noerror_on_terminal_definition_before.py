import pytest
from parglare import Grammar, GrammarError


def test_terminal_exists_noerror_on_terminal_definition_before():
    """
    Test the situation where we have inline terminal used but the
    same terminal is defined in the `terminals` section.
    """
    grammar = """
    Program: "begin"
             statements=Statement*
             ProgramEnd EOF;
    Statement: "end" "transaction"  // here we are using inline terminal `end`
                                    // instead of using a name reference
             | "command";

    terminals
    ProgramEnd: "end";
    """

    with pytest.raises(GrammarError) as e:
        Grammar.from_string(grammar)

    assert 'match the same string' in str(e)
