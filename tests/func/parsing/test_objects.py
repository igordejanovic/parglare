"""
Test for class/object auto AST building.
"""
import pytest  # noqa
from parglare import Grammar, Parser
from parglare.grammar import MULT_ONE, MULT_ONE_OR_MORE, MULT_ZERO_OR_MORE, \
    MULT_OPTIONAL
from parglare.actions import obj


grammar = """
A: simple=B
   one_or_more=C+
   zero_or_more=D*
   optional=E?
   bool_attr?=F
   obj=Obj;

Obj: a=D b=B+;

terminals
B: "b";
C: "c";
D: "d";
E: "e";
F: "f";
"""


def test_grammar_rule_assignment_create_class():
    g = Grammar.from_string(grammar)
    assert 'A' in g.classes
    assert 'Obj' in g.classes
    assert len(g.classes) == 2


def test_class_attributes():
    g = Grammar.from_string(grammar)

    A = g.classes['A']
    assert len(A._pg_attrs) == 6

    assert 'simple' in A._pg_attrs
    simple = A._pg_attrs['simple']
    assert simple.name == 'simple'
    assert simple.type_name == 'B'
    assert simple.multiplicity == MULT_ONE

    assert 'one_or_more' in A._pg_attrs
    one_or_more = A._pg_attrs['one_or_more']
    assert one_or_more.name == 'one_or_more'
    assert one_or_more.type_name == 'C'
    assert one_or_more.multiplicity == MULT_ONE_OR_MORE

    assert 'zero_or_more' in A._pg_attrs
    zero_or_more = A._pg_attrs['zero_or_more']
    assert zero_or_more.name == 'zero_or_more'
    assert zero_or_more.type_name == 'D'
    assert zero_or_more.multiplicity == MULT_ZERO_OR_MORE

    assert 'optional' in A._pg_attrs
    optional = A._pg_attrs['optional']
    assert optional.name == 'optional'
    assert optional.type_name == 'E'
    assert optional.multiplicity == MULT_OPTIONAL

    assert 'bool_attr' in A._pg_attrs
    bool_attr = A._pg_attrs['bool_attr']
    assert bool_attr.name == 'bool_attr'
    assert bool_attr.type_name == 'F'
    assert bool_attr.multiplicity == MULT_ONE

    assert 'obj' in A._pg_attrs
    obj = A._pg_attrs['obj']
    assert obj.name == 'obj'
    assert obj.type_name == 'Obj'
    assert obj.multiplicity == MULT_ONE

    Obj = g.classes['Obj']
    a = Obj._pg_attrs['a']
    assert a.name == 'a'
    assert a.type_name == 'D'
    assert a.multiplicity == MULT_ONE


def test_default_object_create():
    """
    Test that default action will create object of the constructed class
    for rules using named matches (assignments).
    """
    g = Grammar.from_string(grammar)

    p = Parser(g)
    a = p.parse('b c c d f d b')

    assert isinstance(a, g.classes['A'])
    assert isinstance(a.obj, g.classes['Obj'])
    assert a.simple == 'b'
    assert a.one_or_more == ['c', 'c']
    assert a.zero_or_more == ['d']
    assert a.optional is None
    assert a.bool_attr is True
    assert a.obj.a == 'd'
    assert a.obj.b == ['b']


def test_obj_action_override():
    """
    Test that default common action for object can be overriden in grammar.
    """
    grammar = """
    A: b=B;
    B: "b";
    """
    g = Grammar.from_string(grammar)
    A = g.get_nonterminal('A')
    assert A.action_name == 'obj'
    assert A.action is obj

    grammar = """
    @myaction
    A: b=B;
    B: "b";
    """
    g = Grammar.from_string(grammar)
    A = g.get_nonterminal('A')
    assert A.action_name == 'myaction'
    assert A.action is None


def test_obj_position():
    """
    Test that object start/end position is set properly.
    """
    grammar = r"""
    S: "first" seconds=Second+;
    Second: value=digits;

    terminals
    digits:/\d+/;
    """
    g = Grammar.from_string(grammar)
    parser = Parser(g)

    result = parser.parse("""
    first 45 56
    66 3434342
    """)

    n = result.seconds[1]
    assert n._pg_start_position == 14
    assert n._pg_end_position == 16

    n = result.seconds[3]
    assert n._pg_start_position == 24
    assert n._pg_end_position == 31
