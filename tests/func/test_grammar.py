# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import pytest
from parglare import Parser, Grammar, Terminal, NonTerminal
from parglare.grammar import ASSOC_LEFT, ASSOC_RIGHT, DEFAULT_PRIORITY
from parglare.exceptions import GrammarError, ParseError


def test_single_terminal():
    """
    Test that grammar may be just a single terminal.
    """
    grammar = r"""
    S: "a";
    """
    g = Grammar.from_string(grammar)
    parser = Parser(g)
    result = parser.parse('a')
    assert result == 'a'

    grammar = r"""
    S: /\d+/;
    """
    g = Grammar.from_string(grammar)
    parser = Parser(g)
    result = parser.parse('23')
    assert result == '23'


def test_undefined_grammar_symbol():
    "Tests that undefined grammar symbols raises errors."
    grammar = """
    S: A B;
    A: "a" | B;
    B: id;
    """
    with pytest.raises(GrammarError) as e:
        Grammar.from_string(grammar)

    assert 'Unknown symbol' in str(e)
    assert 'id' in str(e)


def test_terminal_nonterminal():

    # Production A is a terminal ("a") and non-terminal at the same time.
    # Thus, it must be recognized as non-terminal.
    grammar = """
    S: A B;
    A: "a" | B;
    B: "b";
    """
    g = Grammar.from_string(grammar)
    assert NonTerminal("A") in g.nonterminals
    assert Terminal("A") not in g.terminals
    assert Terminal("B") in g.terminals
    assert NonTerminal("B") not in g.nonterminals

    # Here A should be non-terminal while B should be terminal.
    grammar = """
    S: A B;
    A: B;
    B: "b";
    """

    g = Grammar.from_string(grammar)
    assert NonTerminal("A") in g.nonterminals
    assert Terminal("A") not in g.terminals
    assert Terminal("B") in g.terminals
    assert NonTerminal("B") not in g.nonterminals

    grammar = """
    S: A;
    A: S;
    A: 'x';
    """
    g = Grammar.from_string(grammar)
    assert NonTerminal("S") in g.nonterminals
    assert NonTerminal("A") in g.nonterminals
    assert Terminal("A") not in g.terminals
    assert Terminal("x") in g.terminals

    grammar = """
    S: S S;
    S: 'x';
    S: EMPTY;
    """
    g = Grammar.from_string(grammar)
    assert NonTerminal("S") in g.nonterminals
    assert Terminal("x") in g.terminals
    assert NonTerminal("x") not in g.nonterminals
    assert Terminal("S") not in g.terminals


def test_multiple_terminal_definition():

    # A is defined multiple times as terminal thus it must be recognized
    # as non-terminal with alternative expansions.
    grammar = """
    S: A A;
    A: "a";
    A: "b";
    """

    g = Grammar.from_string(grammar)

    assert NonTerminal("A") in g.nonterminals
    assert Terminal("A") not in g.terminals


def test_reserved_symbol_names():
    """
    Test that reserved symbol names can't be used.
    """
    grammar = """
    S: EOF "First";
    EOF: "eof";
    """
    with pytest.raises(GrammarError) as e:
        Grammar.from_string(grammar)
    assert 'is reserved' in str(e)

    grammar = """
    S: STOP "First";
    STOP: "stop";
    """
    with pytest.raises(GrammarError) as e:
        Grammar.from_string(grammar)
    assert 'is reserved' in str(e)

    grammar = """
    S: EMPTY "First";
    EMPTY: "stop";
    """
    with pytest.raises(GrammarError) as e:
        Grammar.from_string(grammar)
    assert 'is reserved' in str(e)


def test_assoc_prior():
    """Test that associativity and priority can be defined for productions and
    terminals.
    """

    grammar = """
    E: E '+' E {left, 1};
    E: E '*' E {2, left};
    E: E '^' E {right};
    E: id;
    id: /\d+/;
    """

    g = Grammar.from_string(grammar)

    assert g.productions[1].prior == 1
    assert g.productions[1].assoc == ASSOC_LEFT
    assert g.productions[3].assoc == ASSOC_RIGHT
    assert g.productions[3].prior == DEFAULT_PRIORITY

    assert g.productions[3].prior == DEFAULT_PRIORITY

    # Repeat the same but for alternative keywords "shift" and "reduce"
    grammar = """
    E: E '+' E {reduce, 1};
    E: E '*' E {2, reduce};
    E: E '^' E {shift};
    E: id;
    id: /\d+/;
    """

    g = Grammar.from_string(grammar)

    assert g.productions[1].prior == 1
    assert g.productions[1].assoc == ASSOC_LEFT
    assert g.productions[3].assoc == ASSOC_RIGHT
    assert g.productions[3].prior == DEFAULT_PRIORITY

    assert g.productions[3].prior == DEFAULT_PRIORITY


def test_terminal_priority():
    "Terminals might define priority which is used for lexical disambiguation."

    grammar = """
    S: A | B;
    A: 'a' {15};
    B: 'b';
    """

    g = Grammar.from_string(grammar)

    for t in g.terminals:
        if t.name == 'A':
            assert t.prior == 15
        else:
            assert t.prior == DEFAULT_PRIORITY


def test_no_terminal_associavitity():
    "Tests that terminals can't have associativity defined."
    grammar = """
    S: A | B;
    A: 'a' {15, left};
    B: 'b';
    """

    with pytest.raises(ParseError) as e:
        Grammar.from_string(grammar)

    assert 'Error at position 3,16' in str(e)


def test_terminal_empty_body():
    """
    Test that terminals may have empty bodies (when defined using
    recognizers)
    """
    grammar = """
    S: A | B;
    A: {15};
    B: ;
    """

    g = Grammar.from_string(grammar, recognizers={'B': None, 'A': None})

    a = g.get_terminal('A')
    assert a.prior == 15
    b = g.get_terminal('B')
    assert b.recognizer is None


def test_builtin_grammar_action():
    """
    Builtin actions can be referenced from a grammar.
    """

    grammar = """
    @collect
    Ones: Ones One | One;

    One: "1";
    """

    g = Grammar.from_string(grammar)

    ones = g.get_nonterminal('Ones')
    from parglare.actions import collect
    assert ones.action == collect

    p = Parser(g)
    result = p.parse('1 1 1 1 1')

    assert result == "1 1 1 1 1".split()


def test_multiple_grammar_action_raises_error():
    """
    If multiple actions are given for the same non-terminal GrammarError
    should be raised.
    """

    grammar = """
    S: Ones;

    @collect
    Ones: Ones One | One;

    @something
    Ones: 'foo';

    One: "1";
    """

    # Actions 'collect' and 'something' defined for rule 'Ones'
    with pytest.raises(GrammarError) as e:
        Grammar.from_string(grammar)

    assert 'Multiple' in str(e)


def test_action_override():
    """
    Explicitely provided action in `actions` param overrides default or
    grammar provided.
    """
    grammar = """
    S: Foo Bar;
    @pass_nochange
    Foo: 'foo';
    @pass_nochange
    Bar: "1" a;
    a: "a";
    """

    g = Grammar.from_string(grammar)
    p = Parser(g)
    input_str = "foo 1 a"
    result = p.parse(input_str)
    assert result == ["foo", ["1", "a"]]

    actions = {
        "Foo": lambda _, __: "eggs",
        "Bar": lambda _, __: "bar reduce"}

    p = Parser(g, actions=actions)
    result = p.parse(input_str)
    assert result == ["eggs", "bar reduce"]

    # Test with actions call postponing
    p = Parser(g, build_tree=True, actions=actions)
    tree = p.parse(input_str)
    result = p.call_actions(tree)
    assert result == ["eggs", "bar reduce"]


def test_repeatable_zero_or_more():
    """
    Tests zero or more repeatable operator.
    """

    grammar = """
    S: "2" b* "3";
    b: "1";
    """

    g = Grammar.from_string(grammar)
    assert g.get_nonterminal('b_0')

    p = Parser(g)

    input_str = '2 1 1 1 3'
    result = p.parse(input_str)
    assert result == ["2", ["1", "1", "1"], "3"]

    input_str = '2 3'
    result = p.parse(input_str)
    assert result == ["2", [], "3"]


def test_repeatable_zero_or_more_with_separator():
    """
    Tests zero or more repeatable operator with separator.
    """

    grammar = """
    S: "2" b*[comma] "3";
    b: "1";
    comma: ",";
    """

    g = Grammar.from_string(grammar)
    assert g.get_nonterminal('b_0_comma')

    p = Parser(g)

    input_str = '2 1, 1 , 1 3'
    result = p.parse(input_str)
    assert result == ["2", ["1", "1", "1"], "3"]

    input_str = '2 3'
    result = p.parse(input_str)
    assert result == ["2", [], "3"]


def test_repeatable_one_or_more():
    """
    Tests one or more repeatable operator.
    """

    grammar = """
    S: "2" b+ "3";
    b: "1";
    """

    g = Grammar.from_string(grammar)
    assert g.get_nonterminal('b_1')

    p = Parser(g)

    input_str = '2 1 1 1 3'
    result = p.parse(input_str)
    assert result == ["2", ["1", "1", "1"], "3"]

    input_str = '2 3'
    with pytest.raises(ParseError) as e:
        result = p.parse(input_str)
    assert 'Expected: b' in str(e)


def test_repeatable_one_or_more_with_separator():
    """
    Tests one or more repeatable operator with separator.
    """

    grammar = """
    S: "2" b+[comma] "3";
    b: "1";
    comma: ",";
    """

    g = Grammar.from_string(grammar)
    assert g.get_nonterminal('b_1_comma')

    p = Parser(g)

    input_str = '2 1, 1 , 1 3'
    result = p.parse(input_str)
    assert result == ["2", ["1", "1", "1"], "3"]

    input_str = '2 3'
    with pytest.raises(ParseError) as e:
        p.parse(input_str)
    assert 'Expected: b' in str(e)


def test_optional():
    """
    Tests optional operator.
    """

    grammar = """
    S: "2" b? "3"? EOF;
    b: "1";
    """

    g = Grammar.from_string(grammar)
    assert g.get_nonterminal('b_opt')

    p = Parser(g)

    input_str = '2 1 3'
    result = p.parse(input_str)
    assert result == ["2", "1", "3", None]

    input_str = '2 3'
    result = p.parse(input_str)
    assert result == ["2", None, "3", None]

    input_str = '2 1'
    result = p.parse(input_str)
    assert result == ["2", "1", None, None]

    input_str = ' 1 3'
    with pytest.raises(ParseError) as e:
        p.parse(input_str)
    assert 'Expected: 2' in str(e)


def test_optional_no_modifiers():
    """
    Tests that optional operator doesn't allow modifiers.
    """

    grammar = """
    S: "2" b?[comma] "3"? EOF;
    b: "1";
    comma: ",";
    """

    with pytest.raises(GrammarError) as e:
        Grammar.from_string(grammar)

    assert "Repetition modifier not allowed" in str(e)


def test_multiple_repetition_operators():
    """
    Test using of multiple repetition operators.
    """
    grammar = """
    S: "2" b*[comma] c+ "3"? EOF;
    b: "b";
    c: "c";
    comma: ",";
    """

    g = Grammar.from_string(grammar)
    assert g.get_nonterminal('b_0_comma')
    assert g.get_nonterminal('c_1')

    p = Parser(g)

    input_str = '2 b, b  c 3'
    result = p.parse(input_str)
    assert result == ["2", ["b", "b"], ["c"], "3", None]


def test_repetition_operator_many_times_same():
    """
    Test using the same repetition operator multiple times.
    """

    grammar = """
    S: "2" b*[comma] "3"? b*[semicolon] EOF;
    b: "b";
    comma: ",";
    semicolon: ";";
    """

    g = Grammar.from_string(grammar)
    assert g.get_nonterminal('b_0_comma')
    assert g.get_nonterminal('b_0_semicolon')

    p = Parser(g)

    input_str = '2 b, b  3 b; b; b'
    result = p.parse(input_str)
    assert result == ["2", ["b", "b"], "3", ["b", "b", "b"], None]


def assignment_in_productions(prods, symbol_name, assgn_name):
    found = False
    for p in prods:
        if p.symbol.name == symbol_name:
            found = assgn_name in p.assignments
    return found


def test_assignment_plain():
    """
    Test plain assignment.
    """

    grammar = """
    S: "1" first=some_match "3";
    some_match: "2";
    """

    g = Grammar.from_string(grammar)
    assert assignment_in_productions(g.productions, 'S', 'first')

    called = [False]

    def act_s(_, nodes, first):
        called[0] = True
        assert first == "2"
        return nodes

    actions = {
        "S": act_s
    }

    p = Parser(g, actions=actions)

    input_str = '1 2 3'

    result = p.parse(input_str)
    assert result == ["1", "2", "3"]
    assert called[0]


def test_assignment_bool():
    """
    Test bool assignment.
    """

    grammar = """
    S: "1" first?=some_match "3";
    some_match: "2";
    """

    g = Grammar.from_string(grammar)
    assert assignment_in_productions(g.productions, 'S', 'first')

    called = [False]

    def act_s(_, nodes, first):
        called[0] = True
        assert first is True
        return nodes

    actions = {
        "S": act_s
    }

    p = Parser(g, actions=actions)

    input_str = '1 2 3'

    result = p.parse(input_str)
    assert result == ["1", "2", "3"]
    assert called[0]


def test_assignment_of_repetition():
    """
    Test assignment of repetition.
    """

    grammar = """
    S: "1" first=some_match+ "3";
    some_match: "2";
    """

    g = Grammar.from_string(grammar)
    assert assignment_in_productions(g.productions, 'S', 'first')

    called = [False]

    def act_s(_, nodes, first):
        called[0] = True
        assert first == ["2", "2"]
        return nodes

    actions = {
        "S": act_s
    }

    p = Parser(g, actions=actions)

    input_str = '1 2 2 3'

    result = p.parse(input_str)
    assert result == ["1", ["2", "2"], "3"]
    assert called[0]


def test_assignment_of_repetition_with_sep():
    """
    Test assignment of repetition.
    """

    grammar = """
    S: "1" first=some_match+[comma] "3";
    some_match: "2";
    comma: ",";
    """

    g = Grammar.from_string(grammar)
    assert assignment_in_productions(g.productions, 'S', 'first')

    called = [False]

    def act_s(_, nodes, first):
        called[0] = True
        assert first == ["2", "2"]
        return nodes

    actions = {
        "S": act_s
    }

    p = Parser(g, actions=actions)

    input_str = '1 2, 2 3'

    result = p.parse(input_str)
    assert result == ["1", ["2", "2"], "3"]
    assert called[0]


def test_multiple_assignment_with_repetitions():
    """
    Test assignment of repetition.
    """

    grammar = """
    S: "1" first=some_match+[comma] second?=some_match* "3";
    some_match: "2";
    comma: ",";
    """

    g = Grammar.from_string(grammar)
    assert assignment_in_productions(g.productions, 'S', 'first')
    assert assignment_in_productions(g.productions, 'S', 'second')

    called = [False]

    def act_s(_, nodes, first, second):
        called[0] = True
        assert first == ["2", "2"]
        assert second is True
        return nodes

    actions = {
        "S": act_s
    }

    p = Parser(g, actions=actions)

    input_str = '1 2, 2 2 2 2 3'

    result = p.parse(input_str)
    assert result == ["1", ["2", "2"], ["2", "2", "2"], "3"]
    assert called[0]


def test_case_insensitive_parsing():
    """
    By default parglare is case sensitive. This test parsing without case
    sensitivity.
    """

    grammar = """
    S: "one" "Two" /Aa\w+/;
    """

    g = Grammar.from_string(grammar)

    # By default parsing is case sensitive for both string and regex matches.
    parser = Parser(g)
    with pytest.raises(ParseError):
        parser.parse('One Two Aaa')

    with pytest.raises(ParseError):
        parser.parse('one Two AAa')

    g = Grammar.from_string(grammar, ignore_case=True)
    parser = Parser(g)
    parser.parse('One Two Aaa')
    parser.parse('one Two AAa')
