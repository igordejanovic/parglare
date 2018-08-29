"""
Allow arbitrary user meta-data.
See issue: https://github.com/igordejanovic/parglare/issues/57
"""
import pytest
from parglare import Grammar, ParseError
from parglare.grammar import ASSOC_LEFT


def test_production_meta_data():

    grammar_str = r'''
    MyRule: 'a' {left, 1, dynamic, nops, label:'My Label'};
    '''

    grammar = Grammar.from_string(grammar_str)
    my_rule = grammar.get_nonterminal('MyRule')

    prod = my_rule.productions[0]
    assert prod.assoc == ASSOC_LEFT
    assert prod.prior == 1
    assert prod.dynamic
    assert prod.label == 'My Label'

    with pytest.raises(AttributeError):
        prod.non_existing


def test_production_meta_data_must_be_key_value():

    grammar_str = r'''
    MyRule: 'a' {left, 1, dynamic, nops, label:'My Label', not_allowed};
    '''

    with pytest.raises(ParseError, match=r'ot_allowed\*}'):
        Grammar.from_string(grammar_str)


def test_terminal_meta_data():

    grammar_str = r'''
    MyRule: a;
    terminals
    a: 'a' {dynamic, 1, label: 'My Label'};
    '''

    grammar = Grammar.from_string(grammar_str)
    term_a = grammar.get_terminal('a')

    assert term_a.prior == 1
    assert term_a.dynamic
    assert term_a.label == 'My Label'

    with pytest.raises(AttributeError):
        term_a.non_existing


def test_terminal_meta_data_must_be_key_value():

    grammar_str = r'''
    MyRule: a;
    terminals
    a: 'a' {dynamic, 1, label: 'My Label', not_allowed};
    '''

    with pytest.raises(ParseError, match=r'ot_allowed\*}'):
        Grammar.from_string(grammar_str)
