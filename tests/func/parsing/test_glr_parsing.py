# -*- coding: utf-8 -*-
import pytest
import sys
from parglare import GLRParser, Grammar, Parser, ParseError
from parglare.exceptions import SRConflicts


def test_lr2_grammar():

    grammar = r"""
    Model: Prods;
    Prods: Prod | Prods Prod;
    Prod: ID "=" ProdRefs;
    ProdRefs: ID | ProdRefs ID;

    terminals
    ID: /\w+/;
    """

    input_str = """
    First = One Two three
    Second = Foo Bar
    Third = Baz
    """

    g = Grammar.from_string(grammar)

    # This grammar is not LR(1) as it requires
    # at least two tokens of lookahead to decide
    # what to do on each ID from the right side.
    # If '=' is after ID than it should reduce "Prod"
    # else it should reduce ID as ProdRefs.
    with pytest.raises(SRConflicts):
        Parser(g, prefer_shifts=False)

    # prefer_shifts strategy (the default)
    # will remove conflicts but the resulting parser
    # will fail to parse any input as it will consume
    # greadily next rule ID as the body element of the previous Prod rule.
    parser = Parser(g)
    with pytest.raises(ParseError):
        parser.parse(input_str)

    # But it can be parsed unambiguously by GLR.
    p = GLRParser(g)

    results = p.parse(input_str)
    assert len(results) == 1


def test_nops():
    """
    Test that nops (no prefer shifts) will honored per rule.
    """
    grammar = """
    Program: "begin"
             statements=Statements
             ProgramEnd;
    Statements: Statements1 | EMPTY;
    Statements1: Statements1 Statement | Statement;
    ProgramEnd: End;
    Statement: End "transaction" | "command";

    terminals
    End: "end";
    """

    g = Grammar.from_string(grammar, ignore_case=True)
    parser = GLRParser(g, build_tree=True, prefer_shifts=True)

    # Here we have "end transaction" which is a statement and "end" which
    # finish program. Prefer shift strategy will make parser always choose to
    # shift "end" in anticipation of "end transaction" statement instead of
    # reducing by "Statements" and finishing.
    with pytest.raises(ParseError):
        parser.parse("""
        begin
            command
            end transaction
            command
            end transaction
            command
        end
        """)

    # When {nops} is used, GLR parser will investigate both possibilities at
    # this place and find the correct interpretation while still using
    # prefer_shift strategy globaly.
    grammar = """
    Program: "begin"
             statements=Statements
             ProgramEnd;
    Statements: Statements1 {nops} | EMPTY;
    Statements1: Statements1 Statement | Statement;
    ProgramEnd: End;
    Statement: End "transaction" | "command";

    terminals
    End: "end";
    """

    g = Grammar.from_string(grammar, ignore_case=True)
    parser = GLRParser(g, build_tree=True, prefer_shifts=True)
    parser.parse("""
    begin
        command
        end transaction
        command
        end transaction
        command
    end
    """)


def test_expressions():

    actions = {
        "s": lambda _, c: c[0],
        "E": [
            lambda _, nodes: nodes[0] + nodes[2],
            lambda _, nodes: nodes[0] * nodes[2],
            lambda _, nodes: nodes[1],
            lambda _, nodes: int(nodes[0])
        ]
    }

    # This grammar is highly ambiguous if priorities and
    # associativities are not defined to disambiguate.
    grammar = r"""
    E: E "+" E | E "*" E | "(" E ")" | Number;
    terminals
    Number: /\d+/;
    """
    g = Grammar.from_string(grammar)
    p = GLRParser(g, actions=actions)

    # Even this simple expression has 2 different interpretations
    # (4 + 2) * 3 and
    # 4 + (2 * 3)
    forest = p.parse("4 + 2 * 3")
    assert len(forest) == 2
    results = [p.call_actions(tree) for tree in forest]
    assert 18 in results and 10 in results

    # Adding one more operand rises number of interpretations to 5
    results = p.parse("4 + 2 * 3 + 8")
    assert len(results) == 5

    # One more and there are 14 interpretations
    results = p.parse("4 + 2 * 3 + 8 * 5")
    assert len(results) == 14

    # The number of interpretation will be the Catalan number of n
    # where n is the number of operations.
    # https://en.wikipedia.org/wiki/Catalan_number
    # This number rises very fast. For 10 operations number of interpretations
    # will be 16796!

    # If we rise priority for multiplication operation we reduce ambiguity.
    # Default production priority is 10. Here we will raise it to 15 for
    # multiplication.
    grammar = r"""
    E: E "+" E | E "*" E {15}| "(" E ")" | Number;
    terminals
    Number: /\d+/;
    """
    g = Grammar.from_string(grammar)
    p = GLRParser(g, actions=actions)

    # This expression now has 2 interpretation:
    # (4 + (2*3)) + 8
    # 4 + ((2*3) + 8)
    # This is due to associativity of + operation which is not defined.
    results = p.parse("4 + 2 * 3 + 8")
    assert len(results) == 2

    # If we define associativity for both + and * we have resolved all
    # ambiguities in the grammar.
    grammar = r"""
    E: E "+" E {left}| E "*" E {left, 15}| "(" E ")" | Number;
    terminals
    Number: /\d+/;
    """
    g = Grammar.from_string(grammar)
    p = GLRParser(g, actions=actions)

    results = p.parse("4 + 2 * 3 + 8 * 5 * 3")
    assert len(results) == 1
    assert p.call_actions(results[0]) == 4 + 2 * 3 + 8 * 5 * 3


@pytest.mark.skipif(sys.version_info < (3, 6),
                    reason="list comparison doesn't work "
                    "correctly in pytest 4.1")
def test_epsilon_grammar():

    grammar = r"""
    Model: Prods;
    Prods: Prod | Prods Prod | EMPTY;
    Prod: ID "=" ProdRefs;
    ProdRefs: ID | ProdRefs ID;

    terminals
    ID: /\w+/;
    """

    g = Grammar.from_string(grammar)
    p = GLRParser(g)

    txt = """
    First = One Two three
    Second = Foo Bar
    Third = Baz
    """

    forest = p.parse(txt)

    expected = [
        # First solution
        [[['First', '=', [['One', 'Two'], 'three']],
          ['Second', '=', ['Foo', 'Bar']]],
         ['Third', '=', 'Baz']],

        # Second solution
        [[[[], ['First', '=', [['One', 'Two'], 'three']]],
          ['Second', '=', ['Foo', 'Bar']]],
         ['Third', '=', 'Baz']]
    ]
    assert [p.call_actions(tree) for tree in forest] == expected

    results = p.parse("")
    assert len(results) == 1


def test_no_consume_input_multiple_trees():
    """
    When GLR parser is run with `consume_input=False` it could result in
    multiple trees that are produced by successful parses of the incomplete
    input.
    """
    grammar_nonempty = r"""
    Model: Prods;
    Prods: Prod | Prods Prod;
    Prod: ID "=" ProdRefs;
    ProdRefs: ID | ProdRefs ID;

    terminals
    ID: /\w+/;
    """

    g_nonempty = Grammar.from_string(grammar_nonempty)

    txt = """
    First = One Two three
    Second = Foo Bar
    Third = Baz
    """

    p = GLRParser(g_nonempty, consume_input=False)
    results = p.parse(txt)
    # There are eight successful parses:
    # 1. First = One
    # 2. First = One Two
    # 3. First = One Two three
    # 4. First = One Two three Second
    # 5. ... Second = Foo
    # 6. ... Second = Foo Bar
    # 7. ... Second = Foo Bar Third
    # 8. everyting parsed
    assert len(results) == 8

    # With lexical disambiguation turned on there are only 3 parses,
    # because regular tokens are preferred over STOP tokens.
    # So STOP token gets fed to the parser head only if there is nothing else.
    # This is the situation when head parsing ProdRefs encounters "=".
    # Namely the three parses are:
    # 1. First = One Two three Second
    # 2. ... Second = Foo Bar Third
    # 3. everything parsed
    disambig_p = GLRParser(g_nonempty, consume_input=False,
                           lexical_disambiguation=True)
    assert len(disambig_p.parse(txt)) == 3


def test_empty_terminal():
    g = Grammar.from_string("""
    a: a t | t;
    terminals
    t: /b*/;
    """)
    p = GLRParser(g)
    with pytest.raises(ParseError):
        p.parse("a")


def test_empty_recognizer():
    """This test verifies if custom recorgnizer matching on empty string
    can throw parser into infinite loop."""

    def match_bs(input_str, pos):
        end_pos = pos
        while end_pos < len(input_str) and input_str[end_pos] == 'b':
            end_pos += 1
        return input_str[pos:end_pos]

    g = Grammar.from_string("""
    a: a t | t;
    terminals
    t: ;
    """, recognizers={'t': match_bs})
    p = GLRParser(g)
    with pytest.raises(ParseError):
        p.parse("a")


def test_terminal_collision():
    g = Grammar.from_string("""
    expression: "1" s letter
              | "2" s "A"
              ;

    s: " ";

    terminals
    letter: /[A-Z]/;
    """)

    p = GLRParser(g, ws='')

    p.parse("2 A")
    p.parse("1 B")
    p.parse("1 A")


def test_lexical_ambiguity():
    g = Grammar.from_string("""
    expression: a a
              | b
              ;

    terminals
    a: "x";
    b: "xx";
    """)

    p = GLRParser(g)

    assert all([p.call_actions(x) in ['xx', ['x', 'x']] for x in p.parse('xx')])

    disambig_p = GLRParser(g, lexical_disambiguation=True)
    assert p.call_actions(disambig_p.parse("xx")[0]) == 'xx'


def test_lexical_ambiguity2():
    g = Grammar.from_string(r'''
    Stuff: Stuff "+" Stuff | Something;
    Something: INT | FLOAT | Object;
    Object: INT DOT INT;

    terminals
    INT: /\d+/;
    FLOAT: /\d+(\.\d+)?/;
    DOT: ".";
    ''')

    parser = GLRParser(g)

    # Lexical ambiguity between FLOAT and INT . INT
    forest = parser.parse('42.12')
    assert len(forest) == 2
    assert forest.ambiguities == 1

    # Here also we have two ambiguities
    forest = parser.parse('42.12 + 3.8')
    assert len(forest) == 4
    assert forest.ambiguities == 2

    # Here we have 3 lexical ambiguities and 1 ambiguity
    # for + operation
    forest = parser.parse('34.78 + 8 + 3.3')
    assert len(forest) == 16
    assert forest.ambiguities == 4

    # Here we have 4 lexical ambiguities and 3 ambiguities
    # for + operation therefore 5 * 2 ^ 4 solutions
    forest = parser.parse('34.78 + 8 + 3.3 + 1.2')
    assert len(forest) == 80
    assert forest.ambiguities == 7

    # When default lexical disambiguation is activated
    # We should have only syntactical ambiguities where
    # default lexical disambiguation can resolve
    parser = GLRParser(g, lexical_disambiguation=True)

    # Longest match is used to choose FLOAT
    forest = parser.parse('42.12')
    assert len(forest) == 1
    forest[0].symbol.name == 'FLOAT'
    assert forest.ambiguities == 0

    # Also, longest match will choose FLOAT in both cases
    forest = parser.parse('42.12 + 3.8')
    assert len(forest) == 1
    assert forest.ambiguities == 0

    # Here we still have lexical ambiguity on "8"
    forest = parser.parse('34.78 + 8 + 3.3')
    assert len(forest) == 4
    assert forest.ambiguities == 2

    # Lexical ambiguity on "8" and 3 syntactical ambiguities
    # on + operations
    forest = parser.parse('34.78 + 8 + 3.3 + 1.2')
    assert len(forest) == 10
    assert forest.ambiguities == 4
