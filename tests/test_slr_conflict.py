import pytest
from parglare import Grammar, Parser
from parglare.exceptions import ShiftReduceConflict


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
    with pytest.raises(ShiftReduceConflict):
        Parser(grammar)
