"""
Allow for rule level disambiguation and user meta-data.
See issue: https://github.com/igordejanovic/parglare/issues/57
"""
import pytest
from parglare import Grammar
from parglare.grammar import ASSOC_LEFT, ASSOC_RIGHT, ASSOC_NONE


def test_rule_meta():

    grammar_str = r'''
    MyRule {label: 'My Label', nops}: 'a' {left, 1, dynamic};
    '''

    grammar = Grammar.from_string(grammar_str)
    my_rule = grammar.get_nonterminal('MyRule')

    # User meta-data is accessible on non-terminal
    assert my_rule.label == 'My Label'

    # But built-in disambiguation rules are not
    with pytest.raises(AttributeError):
        assert my_rule.nops

    # Also for nonexisting attributes
    with pytest.raises(AttributeError):
        assert my_rule.nonexisting

    # Production has its own meta-data
    prod = my_rule.productions[0]
    assert prod.assoc == ASSOC_LEFT
    assert prod.prior == 1
    assert prod.dynamic


def test_rule_meta_override():
    """
    Test that meta-data are propagated to productions and can be overriden.
    """

    grammar_str = r'''
    MyRule {label: 'My Label', left}: 'a' {right, label: 'My overriden label'}
                                    | 'b';
    '''

    grammar = Grammar.from_string(grammar_str)
    my_rule = grammar.get_nonterminal('MyRule')

    # User meta-data is accessible on non-terminal
    assert my_rule.label == 'My Label'

    prod = my_rule.productions[0]
    # First production overrides meta-data
    assert prod.label == 'My overriden label'
    assert prod.assoc == ASSOC_RIGHT

    # If not overriden it uses meta-data from the rule.
    prod = my_rule.productions[1]
    assert prod.label == 'My Label'
    assert prod.assoc == ASSOC_LEFT


def test_multiple_rule_meta_override():
    """
    Test that meta-data are propagated to productions from containing rule
    and can be overriden.
    """

    grammar_str = r'''
    MyRule {label: 'My Label', left}: 'first' {right,
                                               label: 'My overriden label'}
                                    | 'second';

    MyRule {label: 'Other rule'}: 'third' {left}
                                | 'fourth' {label: 'Fourth prod'};
    '''

    grammar = Grammar.from_string(grammar_str)
    my_rule = grammar.get_nonterminal('MyRule')

    # User meta-data is accessible on non-terminal
    assert my_rule.label == 'My Label'

    assert len(my_rule.productions) == 4

    prod = my_rule.productions[0]
    # First production overrides meta-data
    assert prod.label == 'My overriden label'
    assert prod.assoc == ASSOC_RIGHT

    # If not overriden it uses meta-data from the rule.
    prod = my_rule.productions[1]
    assert prod.label == 'My Label'
    assert prod.assoc == ASSOC_LEFT

    # Third and fourth production belongs to the second rule so they
    # inherits its meta-data.
    prod = my_rule.productions[2]
    assert prod.label == 'Other rule'
    assert prod.assoc == ASSOC_LEFT

    prod = my_rule.productions[3]
    assert prod.label == 'Fourth prod'
    assert prod.assoc == ASSOC_NONE
