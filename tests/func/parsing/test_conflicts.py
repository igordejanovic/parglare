import pytest  # noqa
from parglare import Grammar, Parser
from parglare.exceptions import SRConflicts, RRConflicts


def test_sr_conflict():
    grammar = """
    S: As A A;
    As: As A | A;

    terminals
    A:"a";
    """
    g = Grammar.from_string(grammar)
    with pytest.raises(SRConflicts) as e:
        Parser(g, prefer_shifts=False)
    assert "whether to shift or reduce by production(s) '1: As = As A'" in \
        str(e.value.conflicts[0].message)


def test_rr_empty_conflict():
    grammar = """
    S: A B C | A D C;
    B: B1 | EMPTY;
    D: D1 | EMPTY;

    terminals
    A: "a";
    C: "c";
    B1: "b";
    D1: "d";
    """
    g = Grammar.from_string(grammar)
    with pytest.raises(RRConflicts) as e:
        Parser(g)

    # For B and D empty reductions both "A B C" and "A D C" can reduce to S
    assert "'2: B = EMPTY' or '4: D = EMPTY'" \
        in str(e.value.conflicts[0].message)


def test_rr_nonempty_conflict():
    grammar = """
    S: A | B;
    A: A1 B1;
    B: A1 B1;

    terminals
    A1: "a";
    B1: "b";
    """
    g = Grammar.from_string(grammar)
    with pytest.raises(RRConflicts) as e:
        Parser(g)

    # "A1 B1" can reduce to both A and B
    assert "'1: A = A1 B1' or '2: B = A1 B1'" \
        in str(e.value.conflicts[0].message)
