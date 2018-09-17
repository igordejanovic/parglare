import json
from collections import OrderedDict


def save_table(file_name, table):

    # states
    states = []
    for state in table.states:
        states.append(_dump_state(state))

    with open(file_name, 'w') as f:
        json.dump(states, f)


def load_table(file_name, grammar):
    from parglare.tables import LRState, LRTable, Action

    with open(file_name) as f:
        json_states = json.load(f)

    states = []
    states_dict = {}
    for json_state in json_states:
        state = LRState(grammar, json_state['state_id'],
                        grammar.get_symbol(json_state['symbol']))
        states_dict[state.state_id] = state
        state.finish_flags = json_state['finish_flags']
        state.actions = json_state['actions']
        state.gotos = json_state['gotos']
        states.append(state)

    # Unpack actions and gotos
    for state in states:

        actions = OrderedDict()
        for json_action_fqn in state.actions:
            terminal_fqn, json_actions = json_action_fqn
            term_acts = []
            for json_action in json_actions:
                if 'state_id' in json_action:
                    act_state = states_dict[json_action['state_id']]
                else:
                    act_state = None
                if 'prod_id' in json_action:
                    act_prod = grammar.productions[json_action['prod_id']]
                else:
                    act_prod = None
                term_acts.append(Action(json_action['action'],
                                        act_state, act_prod))

            actions[grammar.get_terminal(terminal_fqn)] = term_acts
        state.actions = actions

        gotos = OrderedDict()
        for json_goto_fqn in state.gotos:
            nonterm_fqn, goto_state = json_goto_fqn
            gotos[grammar.get_nonterminal(nonterm_fqn)] = \
                states_dict[goto_state]
        state.gotos = gotos

    table = LRTable(states, calc_finish_flags=False)

    return table


def _dump_state(state):
    s = OrderedDict()
    s['state_id'] = state.state_id
    s['symbol'] = state.symbol.fqn
    action_items = list(state.actions.items())
    s['actions'] = [[terminal.fqn, _dump_actions(action)]
                    for terminal, action in action_items]
    goto_items = list(state.gotos.items())
    s['gotos'] = [[nonterminal.fqn, st.state_id]
                  for nonterminal, st in goto_items]
    s['finish_flags'] = state.finish_flags

    return s


def _dump_actions(actions):
    alist = []
    for action in actions:
        a = OrderedDict()
        a['action'] = action.action
        if action.state is not None:
            a['state_id'] = action.state.state_id
        if action.prod is not None:
            a['prod_id'] = action.prod.prod_id
        alist.append(a)

    return alist
