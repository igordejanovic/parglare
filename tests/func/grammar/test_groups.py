"""
Grammar rules can use groups in parentheses.
The group should be treated the same as any other rule reference,
it can be used in assignments, repetitions etc.
"""
from parglare import Grammar, GLRParser
from parglare.grammar import ASSOC_LEFT, MULT_ONE


def test_group_with_sequence():
    grammar_str = r'''
    a: (b* c);
    b: c;
    terminals
    c: "c";
    '''
    grammar = Grammar.from_string(grammar_str)

    # Check initial rule
    assert grammar.productions[0].rhs[0].name == 'a'

    # Check that A references A_g1
    assert grammar.get_productions('a')[0].rhs[0].name == 'a_g1'

    # Check group rule
    assert grammar.get_nonterminal('a_g1')
    prods = grammar.get_productions('a_g1')
    assert len(prods) == 1
    assert len(prods[0].rhs) == 2
    assert prods[0].rhs[0].name == 'b_0'
    assert prods[0].rhs[1].name == 'c'


def test_group_with_choice():
    grammar_str = r'''
    a: c (b* c | b);
    b: c;
    terminals
    c: "c";
    '''
    grammar = Grammar.from_string(grammar_str)

    # Check initial rule
    assert grammar.productions[0].rhs[0].name == 'a'

    # Check that A references A_g1
    assert grammar.get_productions('a')[0].rhs[1].name == 'a_g1'

    assert grammar.get_nonterminal('a_g1')
    prods = grammar.get_productions('a_g1')
    assert len(prods) == 2
    assert len(prods[0].rhs) == 2
    assert prods[0].rhs[0].name == 'b_0'
    assert prods[0].rhs[1].name == 'c'
    assert len(prods[1].rhs) == 1
    assert prods[1].rhs[0].name == 'b'


def test_group_with_metadata():
    grammar_str = r'''
    a: (b* c {left} | c);
    b: c;
    terminals
    c: "c";
    '''
    grammar = Grammar.from_string(grammar_str)
    assert grammar.get_nonterminal('a_g1')
    prods = grammar.get_productions('a_g1')
    assert len(prods) == 2
    assert len(prods[0].rhs) == 2
    assert prods[0].rhs[0].name == 'b_0'
    assert prods[0].rhs[1].name == 'c'
    assert prods[0].assoc == ASSOC_LEFT


def test_group_with_assignment():
    grammar_str = r'''
    a: c c=(b* c);
    terminals
    b: "b";
    c: "c";
    '''
    grammar = Grammar.from_string(grammar_str)
    assert grammar.get_nonterminal('a_g1')
    prods = grammar.get_productions('a_g1')
    assert len(prods) == 1
    prods_a = grammar.get_productions('a')
    assert len(prods_a) == 1

    assert not prods[0].assignments
    assert prods_a[0].assignments
    assig_c = prods_a[0].assignments['c']
    assert assig_c.op == '='
    assert assig_c.multiplicity == MULT_ONE
    assert assig_c.symbol.name == 'a_g1'


def test_group_complex():
    grammar_str = r'''
    @obj
    s: (b c)*[comma];
    s: (b c)*[comma] a=(a+ (b | c)*)+[comma];
    terminals
    a: "a";
    b: "b";
    c: "c";
    comma: ",";
    '''
    grammar = Grammar.from_string(grammar_str)

    assert len(grammar.get_productions('s_g1')) == 1
    # B | C
    prods = grammar.get_productions('s_g3')
    assert len(prods) == 2
    assert prods[0].rhs[0].name == 'b'
    assert prods[1].rhs[0].name == 'c'

    # Nesting
    prods = grammar.get_productions('s_g2')
    assert len(prods) == 1
    assert prods[0].rhs[0].name == 'a_1'
    assert prods[0].rhs[1].name == 's_g3_0'
    assert grammar.get_productions('s')[1].rhs[1].name == 's_g2_1_comma'

    assert 's_g5' not in grammar

    parser = GLRParser(grammar)

    forest = parser.parse('b c, b c a a a b c c b, a b b')
    result = parser.call_actions(forest[0])
    assert result.a == [[['a', 'a', 'a'],
                         ['b', 'c', 'c', 'b']], [['a'], ['b', 'b']]]
