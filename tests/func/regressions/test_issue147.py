from parglare import GLRParser, Grammar


def test_tostr_failure_with_ambiguous_grammar():
    '''
    Test by LVrecar@GitHub
    See: https://github.com/igordejanovic/parglare/issues/147
    '''

    grammar = r'''
    term: var | app;
    app: term " "? term;

    terminals
    var: /[a-z]+?/;
    '''

    g = Grammar.from_string(grammar, ignore_case=True)
    parser = GLRParser(g)

    result = parser.parse("x y z w")
    for _, tree in enumerate(result):
        print(tree.to_str())
