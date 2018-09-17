# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import pytest  # noqa
from parglare import Grammar, Parser, GLRParser, EMPTY, STOP, EOF
from parglare.tables import first, follow, create_table, SHIFT, REDUCE
from .expression_grammar import OPEN, ID, T, E, MULT, CLOSE, PLUS, get_grammar


def test_first():
    """
    Tests FIRST function.

    FIRST function returns a set of terminals that could start the sentence
    derived from the given non-terminal.
    """

    expression_grammar = get_grammar()
    first_set = first(expression_grammar)

    assert OPEN in first_set[T]
    assert ID in first_set[T]


def test_first_empty_in_rhs():
    """
    Test FIRST calculation when there are empty derivations in RHS of a
    production.
    """

    grammar = """
    S: A C;
    A: B | EMPTY;

    terminals
    B: "b";
    C: "c";
    """

    g = Grammar.from_string(grammar)

    first_set = first(g)

    A = g.get_nonterminal('A')
    B = g.get_terminal('B')
    C = g.get_terminal('C')
    S = g.get_nonterminal('S')

    assert EMPTY in first_set[A]
    assert B in first_set[A]

    assert B in first_set[S]

    # 'A' can derive empty, thus 'C' must be in firsts of 'S'.
    assert C in first_set[S]


def test_follow():
    """Tests FOLLOW function.

    FOLLOW function calculates a set of terminals that can follow each grammar
    non-terminal in any of derived sentential forms.
    """

    expression_grammar = get_grammar()
    follow_set = follow(expression_grammar)

    assert follow_set[E] == set([CLOSE, PLUS, EOF])

    # Follow of T must contain all of follow of E
    assert follow_set[T] == set([MULT, CLOSE, PLUS, EOF])


def test_table_construction():
    """
    Tests LR table construction.
    """
    # From the Knuth's 1965 paper: On the Translation of Languages from Left to
    # Right
    grammar = r"""
    S: 'a' A 'd' | 'b' A 'd';
    A: 'c' A | 'c';
    """

    g = Grammar.from_string(grammar)
    table = create_table(g)

    c = g.get_terminal('c')
    d = g.get_terminal('d')

    assert len(table.states) == 11
    assert table.states[0].symbol.name == "S'"
    state = table.states[2]
    assert state.symbol.name == 'a'
    assert len(state.kernel_items) == 1
    assert len(state.items) == 3
    assert len(state.actions) == 1
    assert len(state.actions[c]) == 1
    action = list(state.actions.values())[0][0]
    assert action.action == SHIFT
    assert action.state.state_id == 6

    state = table.states[6]
    assert state.symbol.name == 'c'
    assert len(state.kernel_items) == 2
    assert len(state.items) == 4
    assert len(state.actions) == 2
    assert len(state.actions[c]) == 1
    assert len(state.actions[d]) == 1
    action = list(state.actions.values())[0][0]
    assert action.action == REDUCE
    assert action.prod.prod_id == 4
    action = list(state.actions.values())[1][0]
    assert action.action == SHIFT
    assert action.state.state_id == 6


def test_associativity_conflicts_resolving():
    """
    Test that using associativity will resolve conflicts.
    """
    grammar = r"""
    E: E '+' E | number;

    terminals
    number: /d+/;
    """

    g = Grammar.from_string(grammar)
    table = create_table(g)

    assert len(table.sr_conflicts) == 1

    grammar = r"""
    E: E '+' E {left} | number;

    terminals
    number: /d+/;
    """

    g = Grammar.from_string(grammar)
    table = create_table(g)

    assert len(table.sr_conflicts) == 0


def test_priority_conflicts_resolving():
    """
    Test that using priority will resolve conflicts.
    """


def test_prefer_shifts_no_sr_conflicts():
    """
    Test that grammar with S/R conflict will be resolved to SHIFT actions
    if prefer_shift option is used.
    """
    # This grammar has S/R conflict as B+ may consume multiple single "a" A
    # because "b" is optional. Thus, parser can't decide if it should shift "a"
    # or reduce by 'B: "b"? A+' and later by 'S: B+'; Most of the time we want
    # gready behavior so in case of doubt parser will choose shift if
    # prefer_shift is set to `True`. This means that the parser will first
    # consume all "a" using A+ and that reduce B at the end.
    grammar = r"""
    S: B+;
    B: "b"? A+;

    terminals
    A: "a";
    """
    g = Grammar.from_string(grammar)

    # There is a shift reduce conflict so we can't use LR parser.
    table = create_table(g)
    assert len(table.sr_conflicts) == 1

    # But we can eliminate conflict by prefer_shifts strategy.
    table = create_table(g, prefer_shifts=True)
    assert len(table.sr_conflicts) == 0

    # With prefer_shifts we get a greedy behavior
    input_str = 'b a a a b a a'
    output = [['b', ['a', 'a', 'a']], ['b', ['a', 'a']]]
    parser = Parser(g, prefer_shifts=True)
    result = parser.parse(input_str)
    assert result == output

    # GLR parser can parse without prefer_shifts strategy. This grammar is
    # ambiguous but, in this case, implicit elimination of empty trees (due to
    # optional "b") will yield a single result.
    parser = GLRParser(g)
    result = parser.parse(input_str)
    assert len(result) == 1
    assert result[0] == output

    parser = GLRParser(g, prefer_shifts=True)
    result = parser.parse(input_str)
    assert len(result) == 1
    assert result[0] == output


def test_prefer_shifts_over_empty_reductions():
    """
    Test strategy that will choose SHIFT when in conflict with EMPTY reduction.
    """
    # TODO
