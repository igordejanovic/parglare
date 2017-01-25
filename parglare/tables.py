from collections import OrderedDict
from parglare.parser import LRItem, LRState
from parglare import NonTerminal
from .grammar import AUGSYMBOL, ASSOC_RIGHT, ASSOC_NONE, EOF
from .exceptions import ShiftReduceConflict, ReduceReduceConflict
from .parser import Action, SHIFT, REDUCE, ACCEPT, first, follow
from .closure import closure, LR_1


def create_tables(parser, itemset_type):

    first_sets = first(parser.grammar)
    follow_sets = follow(parser.grammar, first_sets)

    # Create a state for the first production (augmented)
    s = LRState(parser, 0, AUGSYMBOL,
                [LRItem(parser.grammar.productions[0], 0, set([EOF]))])

    state_queue = [s]
    state_id = 1

    while state_queue:
        # For each state calculate its closure first, i.e. starting from a
        # so called "kernel items" expand collection with non-kernel items.
        # We will also calculate GOTO and ACTIONS dicts for each state. These
        # dicts will be keyed by a grammar symbol.
        state = state_queue.pop(0)
        closure(state, itemset_type, first_sets)
        parser._states.append(state)

        # Each state has its corresponding GOTO and ACTION table
        goto = OrderedDict()
        parser._goto.append(goto)
        actions = OrderedDict()
        parser._actions.append(actions)

        # To find out other states we examine following grammar symbols
        # in the current state (symbols following current position/"dot")
        # and group all items by a grammar symbol.
        per_next_symbol = OrderedDict()

        # Each production has a priority. We are interested to find a
        # priority of each grammar symbol. To do that we take the maximal
        # priority given for all productions of the given grammar symbol.
        max_prior_per_symbol = {}

        for i in state.items:
            symbol = i.production.rhs[i.position]
            if symbol:
                per_next_symbol.setdefault(symbol, []).append(i)
                prod_prior = i.production.prior
                old_prior = max_prior_per_symbol.setdefault(symbol,
                                                            prod_prior)
                max_prior_per_symbol[symbol] = max(prod_prior, old_prior)
            else:
                # If the position is at the end then this item
                # would call for reduction but only for terminals
                # from the FOLLOW set of item (LR(1))or the production LHS
                # non-terminal (LR(0)).
                if itemset_type is LR_1:
                    f_set = i.follow
                else:
                    f_set = follow_sets[i.production.symbol]
                for t in f_set:
                    if t is EOF and i.production.prod_id == 0:
                        actions[t] = Action(ACCEPT)
                    elif t in actions:
                        if actions[t].prod != i.production:
                            raise ReduceReduceConflict(state,
                                                       t,
                                                       actions[t].prod,
                                                       i.production)
                    else:
                        actions[t] = Action(REDUCE, prod=i.production)

        # For each group symbol we create new state and form its kernel
        # items from the group items with positions moved one step ahead.
        for symbol, items in per_next_symbol.items():
            inc_items = [i.get_pos_inc() for i in items]
            maybe_new_state = LRState(parser, state_id, symbol, inc_items)
            target_state = maybe_new_state
            try:
                idx = parser._states.index(maybe_new_state)
                target_state = parser._states[idx]
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
                    # LALR: Merge follows of the kernel items.
                    for i in [ti for ti in target_state.items if ti.is_kernel]:
                        new_item = maybe_new_state.items[
                            maybe_new_state.items.index(i)]
                        i.follow.update(new_item.follow)

            if isinstance(symbol, NonTerminal):
                # For each non-terminal symbol we create an entry in GOTO
                # table.
                goto[symbol] = target_state
            else:
                if symbol in actions:
                    # SHIFT/REDUCE conflict
                    # Try to resolve using priority and associativity
                    prod = actions[symbol].prod
                    prior = max_prior_per_symbol[symbol]
                    if prod.prior == prior:
                        if prod.assoc == ASSOC_NONE:
                            parser.print_debug()
                            raise ShiftReduceConflict(state, symbol, prod)
                        elif prod.assoc == ASSOC_RIGHT:
                            actions[symbol] = \
                                Action(SHIFT, state=target_state)
                        # If associativity is left leave reduce operation
                    elif prod.prior < prior:
                        # Next operation priority is higher => shift
                        actions[symbol] = \
                            Action(SHIFT, state=target_state)
                    # If priority of next operation is lower then reduce
                    # before shift
                else:
                    actions[symbol] = Action(SHIFT, state=target_state)

    if parser.debug:
        parser.print_debug()
