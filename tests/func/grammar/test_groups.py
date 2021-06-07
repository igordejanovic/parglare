"""
Grammar rules can use groups in parentheses.
The group should be treated the same as any other rule reference,
it can be used in assignments, repetitions etc.
"""
from parglare import Grammar
from parglare.grammar import ASSOC_LEFT, MULT_ONE


def test_group_with_sequence():
    grammar_str = r'''
    A: (B* C);
    B: C;
    terminals
    C: "c";
    '''
    grammar = Grammar.from_string(grammar_str)

    assert grammar.get_nonterminal('A_g1')
    prods = grammar.get_productions('A_g1')
    assert len(prods) == 1
    assert len(prods[0].rhs) == 2
    assert prods[0].rhs[0].name == 'B_0'
    assert prods[0].rhs[1].name == 'C'


def test_group_with_choice():
    grammar_str = r'''
    A: C (B* C | B);
    B: C;
    terminals
    C: "c";
    '''
    grammar = Grammar.from_string(grammar_str)
    assert grammar.get_nonterminal('A_g1')
    prods = grammar.get_productions('A_g1')
    assert len(prods) == 2
    assert len(prods[0].rhs) == 2
    assert prods[0].rhs[0].name == 'B_0'
    assert prods[0].rhs[1].name == 'C'
    assert len(prods[1].rhs) == 1
    assert prods[1].rhs[0].name == 'B'


def test_group_with_metadata():
    grammar_str = r'''
    A: (B* C {left} | C);
    B: C;
    terminals
    C: "c";
    '''
    grammar = Grammar.from_string(grammar_str)
    assert grammar.get_nonterminal('A_g1')
    prods = grammar.get_productions('A_g1')
    assert len(prods) == 2
    assert len(prods[0].rhs) == 2
    assert prods[0].rhs[0].name == 'B_0'
    assert prods[0].rhs[1].name == 'C'
    assert prods[0].assoc == ASSOC_LEFT


def test_group_with_assignment():
    grammar_str = r'''
    A: C c=(B* C);
    B: C;
    terminals
    C: "c";
    '''
    grammar = Grammar.from_string(grammar_str)
    assert grammar.get_nonterminal('A_g1')
    prods = grammar.get_productions('A_g1')
    assert len(prods) == 1
    prods_A = grammar.get_productions('A')
    assert len(prods_A) == 1

    assert not prods[0].assignments
    assert prods_A[0].assignments
    assig_c = prods_A[0].assignments['c']
    assert assig_c.op == '='
    assert assig_c.multiplicity == MULT_ONE
    assert assig_c.symbol.name == 'A_g1'


def test_group_complex():
    grammar_str = r'''
    A: (B C)*[COMMA];
    A: (B C)*[COMMA] a=(A+ (B | C)*)+[COMMA];
    B: C;
    terminals
    C: "c";
    COMMA: ",";
    '''
    grammar = Grammar.from_string(grammar_str)

    assert len(grammar.get_productions('A_g1')) == 1
    # B | C
    prods = grammar.get_productions('A_g3')
    assert len(prods) == 2
    assert prods[0].rhs[0].name == 'B'
    assert prods[1].rhs[0].name == 'C'

    # Nesting
    prods = grammar.get_productions('A_g2')
    assert len(prods) == 1
    assert prods[0].rhs[0].name == 'A_1'
    assert prods[0].rhs[1].name == 'A_g3_0'
    assert grammar.get_productions('A')[1].rhs[1].name == 'A_g2_1_COMMA'

    assert 'A_g5' not in grammar
