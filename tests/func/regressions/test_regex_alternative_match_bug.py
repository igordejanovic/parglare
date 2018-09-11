from parglare import Grammar, GLRParser


def test_regex_alternative_match_bug():
    """
    """

    grammar = """
    A: "Begin" Eq "End";

    terminals
    Eq: /=|EQ/;
    """
    g = Grammar.from_string(grammar)
    parser = GLRParser(g)
    parser.parse('Begin EQ End')
