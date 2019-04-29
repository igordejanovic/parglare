"""
Allow arbitrary user meta-data on both production and rule-level.
See issue: https://github.com/igordejanovic/parglare/issues/57
"""
import pytest
from parglare import Grammar, ParseError
from parglare.grammar import ASSOC_LEFT, ASSOC_RIGHT, ASSOC_NONE


def test_production_meta_data():

    grammar_str = r'''
    MyRule: 'a' {left, 1, dynamic, nops,
                 some_string:'My Label with \\ and \' end',
                 some_bool: true,
                 some_int: 3,
                 some_float: 4.5};
    '''

    grammar = Grammar.from_string(grammar_str)
    my_rule = grammar.get_nonterminal('MyRule')

    prod = my_rule.productions[0]
    assert prod.assoc == ASSOC_LEFT
    assert prod.prior == 1
    assert prod.dynamic
    assert prod.some_string == r"My Label with \ and ' end"
    assert prod.some_bool is True
    assert prod.some_int == 3
    assert prod.some_float == 4.5

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

    # Rule-level meta-data are propagated to productions
    assert prod.label == 'My Label'


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
    # Rule level meta-data are only those defined on the
    # first rule in the order of the definition.
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
