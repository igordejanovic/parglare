"""
Test non-deterministic parsing.
"""
import pytest  # noqa
from parglare import Grammar, Parser
from parglare.exceptions import GrammarError


def todo_test_nondeterministic_LR_raise_error():
    """TODO: Language of even length palindromes.

    This is a non-deterministic grammar and the language is non-ambiguous.

    If the string is a even length palindrome parser should match EMPTY at he
    middle of the string and start to reduce.

    In parglare currently this can't happen because EMPTY will be overriden by
    '1' or '0' match using longest-match disambiguation strategy so it will try
    to reduce only at the end of the string.

    In GLR parsing this could be supported by using GLR fork/split to resolve
    all ambiguities, even lexical. Of course, this would be a big negative
    impact on preformances as each state that has EMPTY in the action table
    would need to fork as the EMPTY always matches.

    """
    grammar = """
    S = A | B | EMPTY;
    A = '1' S '1';
    B = '0' S '0';
    """

    g = Grammar.from_string(grammar)
    with pytest.raises(GrammarError):
        p = Parser(g, debug=True)
        p.parse('0101000110001010')
