from parglare import Grammar, GLRParser


def test_glr_list_building_bug():
    """Test regression for a bug in building lists from default `collect` actions.

    """
    grammar = r"""
        S: B+;
        B: "b"? A+;
        A: "a";
    """
    g = Grammar.from_string(grammar)
    parser = GLRParser(g, prefer_shifts=True)
    result = parser.parse('b a b a a a')
    assert len(result) == 1
    assert parser.call_actions(result[0]) == [['b', ['a']], ['b', ['a', 'a', 'a']]]
