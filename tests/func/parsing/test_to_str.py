import pytest  # noqa
from parglare import Parser, GLRParser, Grammar
from ..grammar.expression_grammar import get_grammar


def test_parse_tree_to_str():

    grammar = get_grammar()
    p = Parser(grammar, build_tree=True)

    res = p.parse("""id+  id * (id
    +id  )
    """)

    ts = res.to_str()

    assert '+[18->19, "+"]' in ts
    assert ')[23->24, ")"]' in ts
    assert 'F[10->24]' in ts


def test_forest_to_str():

    grammar = Grammar.from_string(r'''
    E: E "+" E | E "-" E | "(" E ")" | "id";
    ''')
    p = GLRParser(grammar)

    forest = p.parse("""id+  id - (id
    +id  )
    """)

    ts = forest.to_str()

    assert 'E - ambiguity[2]' in ts
    assert 'E[10->24]' in ts
    assert '      E[11->21]' in ts
    assert '        +[18->19, "+"]' in ts


def test_ast_to_str():
    """
    Test produced str tree from dynamically constructed AST object.
    """
    grammar = r"""
    S: "1" second=Second third=Third+ fourth=Fourth;
    Second: val="2";
    Third: "3";
    Fourth: "4" val=Second;
    """

    g = Grammar.from_string(grammar)
    parser = Parser(g)

    result = parser.parse('1 2 3 3 3 4 2')
    print(result.to_str())
    assert result.to_str().strip() == """
S [0->13]
  second=Second [2->3]
    val='2'
  third=    [
    '3'
    '3'
    '3'
    ]
  fourth=Fourth [10->13]
    val=Second [12->13]
      val='2'""".strip()


def test_ast_to_str_with_bnf_extensions():
    """
    Tests `to_str` with lists returned by BNF extensions.
    """
    grammar = r"""
    S: "1" second=Second third=Third+ fourth=Fourth;
    Second: val="2";
    Third: val="3";
    Fourth: "4" val=Second;
    """

    g = Grammar.from_string(grammar)
    parser = Parser(g)

    result = parser.parse('1 2 3 3 3 4 2')
    print(result.to_str())
    assert result.to_str().strip() == """
S [0->13]
  second=Second [2->3]
    val='2'
  third=    [
    Third [4->5]
      val='3'
    Third [6->7]
      val='3'
    Third [8->9]
      val='3'
    ]
  fourth=Fourth [10->13]
    val=Second [12->13]
      val='2'""".strip()
