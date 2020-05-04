from parglare import Grammar, GLRParser


def test_issue31_glr_drop_parses_on_lexical_ambiguity():
    grammar = """
    model: element+;
    element: title
           | table_with_note
           | table_with_title;
    table_with_title: table_title table_with_note;
    table_with_note: table note*;

    terminals
    title: /title/;   // <-- This is lexically ambiguous with the next.
    table_title: /title/;
    table: "table";
    note: "note";
    """

    # this input should yield 4 parse trees.
    input = "title table title table"

    g = Grammar.from_string(grammar)
    parser = GLRParser(g, debug=True, debug_colors=True)
    results = parser.parse(input)

    # We should have 4 solutions for the input.
    assert len(results) == 4
