from collections import OrderedDict
from parglare.parser import LRItem, LRState
from parglare import NonTerminal
from .grammar import ProductionRHS, AUGSYMBOL, ASSOC_LEFT, ASSOC_NONE, STOP
from .exceptions import ShiftReduceConflict, ReduceReduceConflict, \
    NoActionsForStartRule
from .parser import Action, SHIFT, REDUCE, ACCEPT, first, follow
from .closure import closure, LR_1


def create_tables(grammar, itemset_type, start_production=1):

    first_sets = first(grammar)
    follow_sets = follow(grammar, first_sets)

    start_prod_symbol = grammar.productions[start_production].symbol
    grammar.productions[0].rhs = ProductionRHS([start_prod_symbol, STOP])

    # Create a state for the first production (augmented)
    s = LRState(grammar, 0, AUGSYMBOL,
                [LRItem(grammar.productions[0], 0, set())])

    state_queue = [s]
    state_id = 1

    states = []
    all_goto = []
    all_actions = []

    while state_queue:
        # For each state calculate its closure first, i.e. starting from a
        # so called "kernel items" expand collection with non-kernel items.
        # We will also calculate GOTO and ACTIONS dicts for each state. These
        # dicts will be keyed by a grammar symbol.
        state = state_queue.pop(0)
        closure(state, itemset_type, first_sets)
        states.append(state)

        # Each state has its corresponding GOTO and ACTION tables
        goto = OrderedDict()
        all_goto.append(goto)
        actions = OrderedDict()
        all_actions.append(actions)

        # To find out other states we examine following grammar symbols
        # in the current state (symbols following current position/"dot")
        # and group all items by a grammar symbol.
        state._per_next_symbol = OrderedDict()

        # Each production has a priority. But since productions are grouped
        # by grammar symbol that is ahead we take the maximal
        # priority given for all productions for the given grammar symbol.
        state._max_prior_per_symbol = {}

        for i in state.items:
            symbol = i.production.rhs[i.position]
            if symbol:
                state._per_next_symbol.setdefault(symbol, []).append(i)

                # Here we calculate max priorities for each grammar symbol to
                # use it for SHIFT/REDUCE conflict resolution
                prod_prior = i.production.prior
                old_prior = state._max_prior_per_symbol.setdefault(
                    symbol, prod_prior)
                state._max_prior_per_symbol[symbol] = max(prod_prior,
                                                          old_prior)

        # For each group symbol we create new state and form its kernel
        # items from the group items with positions moved one step ahead.
        for symbol, items in state._per_next_symbol.items():
            inc_items = [i.get_pos_inc() for i in items]
            maybe_new_state = LRState(grammar, state_id, symbol, inc_items)
            target_state = maybe_new_state
            try:
                idx = states.index(maybe_new_state)
                target_state = states[idx]
            except ValueError:
                try:
                    idx = state_queue.index(maybe_new_state)
                    target_state = state_queue[idx]
                except ValueError:
                    pass

            # We've found a new state. Register it for later processing.
            if target_state is maybe_new_state:
                state_queue.append(target_state)
                state_id += 1
            else:
                # State with this kernel items already exists.
                if itemset_type is LR_1:
                    # LALR: Try to merge states.
                    if not merge_states(target_state, maybe_new_state):
                        target_state = maybe_new_state
                        state_queue.append(target_state)
                        state_id += 1

            # Create entries in GOTO and ACTION tables
            if isinstance(symbol, NonTerminal):
                # For each non-terminal symbol we create an entry in GOTO
                # table.
                goto[symbol] = target_state

            else:
                if symbol is STOP:
                    actions[symbol] = Action(ACCEPT)
                else:
                    # For each terminal symbol we create SHIFT action in the
                    # ACTION table.
                    actions[symbol] = Action(SHIFT, state=target_state)

    # Sanity check. First rule must have SHIFT actions.
    if not all_actions[0]:
        raise NoActionsForStartRule()

    # For LR(1) itemsets refresh/propagate item's follows as the LALR
    # merging might change item's follow in previous states
    if itemset_type is LR_1:
        for state in states:

            # First refresh current state's follows
            closure(state, LR_1, first_sets)

            # Propagate follows to next states. GOTO table keeps information
            # about states created from this state
            inc_items = [i.get_pos_inc() for i in state.items]
            for target_state in all_goto[state.state_id].values():
                for next_item in target_state.kernel_items:
                    next_item.follow.update(
                        inc_items[inc_items.index(next_item)].follow)

    # Calculate REDUCTION entries in ACTION tables and resolve possible
    # conflicts.
    for state in states:
        actions = all_actions[state.state_id]

        for i in state.items:
            if i.is_at_end:
                # If the position is at the end then this item
                # would call for reduction but only for terminals
                # from the FOLLOW set of item (LR(1)) or the production LHS
                # non-terminal (LR(0)).
                if itemset_type is LR_1:
                    f_set = i.follow
                else:
                    f_set = follow_sets[i.production.symbol]
                for t in f_set:
                    if t in actions:
                        # Conflict! Try to resolve
                        act = actions[t]
                        if act.action is SHIFT:
                            # SHIFT/REDUCE conflict. Use assoc and priority to
                            # resolve
                            act_prior = state._max_prior_per_symbol[
                                act.state.symbol]
                            prod = i.production
                            if prod.prior == act_prior:
                                if prod.assoc == ASSOC_NONE:
                                    raise ShiftReduceConflict(state,
                                                              act.state.symbol,
                                                              prod)
                                elif prod.assoc == ASSOC_LEFT:
                                    # Override with REDUCE
                                    actions[t] = Action(REDUCE, prod=prod)
                                # If associativity is right leave SHIFT
                                # action
                            elif prod.prior > act_prior:
                                # This item operation priority is higher =>
                                # override with reduce
                                actions[t] = Action(REDUCE, prod=prod)
                                # If priority of existing SHIFT action is
                                # higher then leave it instead

                        elif act.action is REDUCE:
                            # REDUCE/REDUCE conflict
                            # Try to resolve using priorities
                            assert act.prod != i.production
                            prod = i.production
                            if act.prod.prior == prod.prior:
                                raise ReduceReduceConflict(state,
                                                           t,
                                                           act.prod,
                                                           i.production)
                            elif prod.prior > act.prod.prior:
                                actions[t] = Action(REDUCE, prod=prod)

                    else:
                        actions[t] = Action(REDUCE, prod=i.production)

    return states, all_actions, all_goto


def merge_states(old_state, new_state):
    """Try to merge new_state on old_state if possible. If not possible return
    False.
    """

    item_pairs = []
    for i in old_state.kernel_items:
        new_item = new_state.get_item(i)
        item_pairs.append((i, new_item))

    # Check if merging would result in R/R conflict
    check_set = set()
    for old, new in [x for x in item_pairs if x[0].is_at_end]:
        if old.follow.intersection(check_set) \
               or new.follow.intersection(check_set):
            return False
        check_set.update(old.follow)
        check_set.update(new.follow)

    for old, new in item_pairs:
        old.follow.update(new.follow)
    return True
