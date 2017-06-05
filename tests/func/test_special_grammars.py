"""
Test non-deterministic parsing.
"""
import pytest  # noqa
from parglare import Parser, Grammar, SLR, LALR
from parglare.exceptions import GrammarError, SRConflicts, RRConflicts


def test_lr_1_grammar():
    """From the Knuth's 1965 paper: On the Translation of Languages from Left to
    Right

    """
    grammar = """
    S = 'a' A 'd' | 'b' A 'd';
    A = 'c' A | 'c';
    """

    g = Grammar.from_string(grammar)
    parser = Parser(g)

    parser.parse("acccccccccd")
    parser.parse("bcccccccccd")


def test_slr_conflict():
    """
    Unambiguous grammar which is not SLR(1).
    From the Dragon Book.
    This grammar has a S/R conflict if SLR tables are used.
    """

    grammar = """
    S = L '=' R | R;
    L = '*' R | 'id';
    R = L;
    """

    grammar = Grammar.from_string(grammar)
    with pytest.raises(SRConflicts):
        Parser(grammar, tables=SLR)

    Parser(grammar, tables=LALR)


def test_lalr_reduce_reduce_conflict():
    """
    Naive merging of states can lead to R/R conflict as shown in this grammar
    from the Dragon Book.
    """

    grammar = """
    S = 'a' A 'd' | 'b' B 'd' | 'a' B 'e' | 'b' A 'e';
    A = C;
    B = C;
    C = 'c';
    """
    grammar = Grammar.from_string(grammar)
    Parser(grammar)


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


def test_cyclic_grammar_1():
    """
    From the paper: "GLR Parsing for e-Grammers" by Rahman Nozohoor-Farshi
    TODO: This should be a problem for GLR.
    """
    grammar = """
    S = A;
    A = S;
    A = 'x';
    """
    g = Grammar.from_string(grammar)
    with pytest.raises(SRConflicts):
        Parser(g)


def test_cyclic_grammar_2():
    """
    From the paper: "GLR Parsing for e-Grammers" by Rahman Nozohoor-Farshi
    """
    grammar = """
    S = S S;
    S = 'x';
    S = EMPTY;
    """
    g = Grammar.from_string(grammar, debug=True)

    with pytest.raises(SRConflicts):
        Parser(g, debug=True)


def test_highly_ambiguous_grammar():
    """
    This grammar has both Shift/Reduce and Reduce/Reduce conflicts and
    thus can't be parsed by a deterministic LR parsing.
    Shift/Reduce can be resolved by prefer_shifts strategy.
    """
    grammar = """
    S = "b" | S S | S S S;
    """

    g = Grammar.from_string(grammar, debug=True)

    with pytest.raises(SRConflicts):
        Parser(g, debug=True)

    # S/R are resolved by selecting prefer_shifts strategy.
    # But R/R conflicts remain.
    with pytest.raises(RRConflicts):
        Parser(g, prefer_shifts=True, debug=True)


def test_indirect_left_recursive():
    """Grammar with indirect/hidden left recursion.

    parglare will handle this using implicit longest-match disambiguation
    between "b" and EMPTY, i.e. it will greadily match "b" tokens and than
    match EMPTY before "a" and start to reduce by 'B="b" B' production.

    """

    grammar = """
    S = B "a";
    B = "b" B | EMPTY;
    """

    g = Grammar.from_string(grammar)
    p = Parser(g)

    p.parse("bbbbbbbbbbbba")
