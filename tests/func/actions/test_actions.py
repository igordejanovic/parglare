import pytest  # noqa
from parglare import Grammar, Parser, NodeNonTerm
from parglare.exceptions import ParserInitError
from parglare import get_collector
from ..grammar.expression_grammar_numbers import get_grammar


def get_actions():

    def sum_act(_, nodes):
        return nodes[0] + nodes[2]

    def t_act(_, nodes):
        if len(nodes) == 3:
            return nodes[0] * nodes[2]
        else:
            return nodes[0]

    def parenthesses_act(_, nodes):
        return nodes[1]

    def pass_act(_, nodes):
        return nodes[0]

    actions = {
        "number": lambda _, value: float(value),
        # Check action for each alternative
        "E": [sum_act, pass_act],
        # Check symbol-level action
        "T": t_act,
        # Again action for each alternative
        "F": [parenthesses_act, pass_act]
    }

    return actions


def test_actions():

    grammar = get_grammar()
    p = Parser(grammar, actions=get_actions())

    result = p.parse("""34.7+78*34 +89+
    12.223*4""")

    assert result == 34.7 + 78 * 34 + 89 + 12.223 * 4


def test_actions_manual():
    """
    Actions may be called as a separate step.
    """

    grammar = get_grammar()
    p = Parser(grammar, build_tree=True, actions=get_actions())

    result = p.parse("""34.7+78*34 +89+
    12.223*4""")

    assert type(result) is NodeNonTerm

    assert p.call_actions(result) == \
        34.7 + 78 * 34 + 89 + 12.223 * 4


def test_action_list_assigned_to_terminal():
    """
    Test that list of actions can't be assigned to a Terminal.
    """
    grammar = '''
    S: A+;

    terminals
    A: 'a';
    '''
    g = Grammar.from_string(grammar)

    def some_action(_, nodes):
        return nodes[0]

    actions = {
        'S': some_action,
        'A': [some_action, some_action]
    }

    with pytest.raises(ParserInitError,
                       match=r'Cannot use a list of actions for terminal.*'):
        Parser(g, actions=actions)


def test_invalid_number_of_actions():
    """
    Test that parser error is raised if rule is given list of actions
    where there is less/more actions than rule productions.
    """
    grammar = '''
    S: A+ | B+;
    A: 'a';
    B: 'b';
    '''
    g = Grammar.from_string(grammar)

    def some_action(_, nodes):
        return nodes[0]

    actions = {
        'S': [some_action, some_action]
    }
    Parser(g, actions=actions)

    actions = {
        'S': [some_action]
    }
    with pytest.raises(ParserInitError,
                       match=r'Length of list of actions must match.*'):
        Parser(g, actions=actions)

    actions = {
        'S': [some_action, some_action, some_action]
    }
    with pytest.raises(ParserInitError,
                       match=r'Length of list of actions must match.*'):
        Parser(g, actions=actions)


def test_action_decorator():
    """
    Test collecting actions using action decorator.
    """

    action = get_collector()

    @action
    def number(_, value):
        return float(value)

    @action('E')
    def sum_act(_, nodes):
        return nodes[0] + nodes[2]

    @action('E')
    def pass_act_E(_, nodes):
        return nodes[0]

    @action
    def T(_, nodes):
        if len(nodes) == 3:
            return nodes[0] * nodes[2]
        else:
            return nodes[0]

    @action('F')
    def parenthesses_act(_, nodes):
        return nodes[1]

    @action('F')
    def pass_act_F(_, nodes):
        return nodes[0]

    grammar = get_grammar()
    p = Parser(grammar, actions=action.all)

    result = p.parse("""34.7+78*34 +89+
    12.223*4""")

    assert result == 34.7 + 78 * 34 + 89 + 12.223 * 4
