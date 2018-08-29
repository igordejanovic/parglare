# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import pytest
from parglare import GLRParser, Grammar, Parser, ParseError
from parglare.exceptions import SRConflicts


def test_lr2_grammar():

    grammar = """
    Model: Prods EOF;
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
             ProgramEnd EOF;
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
             ProgramEnd EOF;
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
        "E": [
            lambda _, nodes: nodes[0] + nodes[2],
            lambda _, nodes: nodes[0] * nodes[2],
            lambda _, nodes: nodes[1],
            lambda _, nodes: int(nodes[0])
        ]
    }

    # This grammar is highly ambiguous if priorities and
    # associativities are not defined to disambiguate.
    grammar = """
    E: E "+" E | E "*" E | "(" E ")" | Number;
    terminals
    Number: /\d+/;
    """
    g = Grammar.from_string(grammar)
    p = GLRParser(g, actions=actions, debug=True)

    # Even this simple expression has 2 different interpretations
    # (4 + 2) * 3 and
    # 4 + (2 * 3)
    results = p.parse("4 + 2 * 3")
    assert len(results) == 2
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
    grammar = """
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
    grammar = """
    E: E "+" E {left}| E "*" E {left, 15}| "(" E ")" | Number;
    terminals
    Number: /\d+/;
    """
    g = Grammar.from_string(grammar)
    p = GLRParser(g, actions=actions)

    results = p.parse("4 + 2 * 3 + 8 * 5 * 3")
    assert len(results) == 1
    assert results[0] == 4 + 2 * 3 + 8 * 5 * 3


def test_epsilon_grammar():

    grammar = """
    Model: Prods EOF;
    Prods: Prod | Prods Prod | EMPTY;
    Prod: ID "=" ProdRefs;
    ProdRefs: ID | ProdRefs ID;

    terminals
    ID: /\w+/;
    """

    g = Grammar.from_string(grammar)
    p = GLRParser(g, debug=True)

    txt = """
    First = One Two three
    Second = Foo Bar
    Third = Baz
    """

    results = p.parse(txt)
    assert len(results) == 1

    results = p.parse("")
    assert len(results) == 1


def test_non_eof_grammar_nonempty():
    """
    Grammar that is not anchored by EOF at the end might
    result in multiple trees that are produced by sucessful
    parses of the incomplete input.
    """
    grammar_nonempty = """
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

    p = GLRParser(g_nonempty, debug=True)
    results = p.parse(txt)
    # There is three succesful parses.
    # e.g. one would be the production 'First = One Two three Second' and the
    # parser could not continue as the next token is '=' but it succeds as
    # we haven't terminated our model with EOF so we allow partial parses.
    assert len(results) == 3


def test_non_eof_grammar_empty():
    """
    Grammar that is not anchored by EOF at the end might
    result in multiple trees that are produced by sucessful
    parses of the incomplete input.
    """
    grammar_empty = """
    Model: Prods;
    Prods: Prod | Prods Prod | EMPTY;
    Prod: ID "=" ProdRefs;
    ProdRefs: ID | ProdRefs ID;

    terminals
    ID: /\w+/;
    """

    g_empty = Grammar.from_string(grammar_empty)

    txt = """
    First = One Two three
    Second = Foo Bar
    Third = Baz
    """

    p = GLRParser(g_empty, debug=True)

    results = p.parse(txt)
    assert len(results) == 3

    results = p.parse("")
    assert len(results) == 1
