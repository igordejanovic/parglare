from __future__ import print_function, unicode_literals
from collections import OrderedDict
from itertools import chain
from parglare.parser import LRItem, LRState
from parglare import NonTerminal
from .grammar import ProductionRHS, AUGSYMBOL, ASSOC_LEFT, ASSOC_RIGHT, STOP, \
    StringRecognizer
from .exceptions import GrammarError, SRConflict, RRConflict
from .parser import Action, SHIFT, REDUCE, ACCEPT, first, follow
from .closure import closure, LR_1


def create_table(grammar, first_sets=None, follow_sets=None,
                 itemset_type=LR_1, start_production=1):

    first_sets = first_sets if first_sets else first(grammar)

    # Check for states with GOTO links but without SHIFT links.
    # This is invalid as the GOTO link will never be traversed.
    for nt, firsts in first_sets.items():
        if nt.name != 'S\'' and not firsts:
            raise GrammarError(
                'First set empty for grammar symbol "{}". '
                'An infinite recursion on the grammar symbol.'.format(nt))

    follow_sets = follow_sets if follow_sets else follow(grammar, first_sets)

    start_prod_symbol = grammar.productions[start_production].symbol
    grammar.productions[0].rhs = ProductionRHS([start_prod_symbol, STOP])

    # Create a state for the first production (augmented)
    s = LRState(grammar, 0, AUGSYMBOL,
                [LRItem(grammar.productions[0], 0, set())])

    state_queue = [s]
    state_id = 1

    states = []

    while state_queue:
        # For each state calculate its closure first, i.e. starting from a
        # so called "kernel items" expand collection with non-kernel items.
        # We will also calculate GOTO and ACTIONS dicts for each state. These
        # dicts will be keyed by a grammar symbol.
        state = state_queue.pop(0)
        closure(state, itemset_type, first_sets)
        states.append(state)

        # To find out other states we examine following grammar symbols
        # in the current state (symbols following current position/"dot")
        # and group all items by a grammar symbol.
        state._per_next_symbol = OrderedDict()

        # Each production has a priority. But since productions are grouped
        # by grammar symbol that is ahead we take the maximal
        # priority given for all productions for the given grammar symbol.
        state._max_prior_per_symbol = {}

        for i in state.items:
            symbol = i.symbol_at_position
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
                    # LALR: Try to merge states, i.e. update items follow sets.
                    if not merge_states(target_state, maybe_new_state):
                        target_state = maybe_new_state
                        state_queue.append(target_state)
                        state_id += 1

            # Create entries in GOTO and ACTION tables
            if isinstance(symbol, NonTerminal):
                # For each non-terminal symbol we create an entry in GOTO
                # table.
                state.gotos[symbol] = target_state

            else:
                if symbol is STOP:
                    state.actions[symbol] = [Action(ACCEPT,
                                                    state=target_state)]
                else:
                    # For each terminal symbol we create SHIFT action in the
                    # ACTION table.
                    state.actions[symbol] = [Action(SHIFT, state=target_state)]

    # For LR(1) itemsets refresh/propagate item's follows as the LALR
    # merging might change item's follow in previous states
    if itemset_type is LR_1:

        # Propagate updates as long as there were items propagated in the last
        # loop run.
        update = True
        while update:
            update = False

            for state in states:

                # First refresh current state's follows
                closure(state, LR_1, first_sets)

                # Propagate follows to next states. GOTOs/ACTIONs keep
                # information about states created from this state
                inc_items = [i.get_pos_inc() for i in state.items]
                for target_state in chain(
                        state.gotos.values(),
                        [a.state for i in state.actions.values()
                         for a in i if a.action is SHIFT]):
                    for next_item in target_state.kernel_items:
                        this_item = inc_items[inc_items.index(next_item)]
                        if this_item.follow.difference(next_item.follow):
                            update = True
                            next_item.follow.update(this_item.follow)

    # Calculate REDUCTION entries in ACTION tables and resolve possible
    # conflicts.
    for state in states:
        actions = state.actions

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

                prod = i.production
                new_reduce = Action(REDUCE, prod=prod)

                for t in f_set:
                    if t not in actions:
                        actions[t] = [new_reduce]
                    else:
                        # Conflict! Try to resolve
                        t_acts = actions[t]
                        should_reduce = True

                        # Only one SHIFT might exists for single terminal
                        try:
                            t_shift = [x for x in t_acts
                                       if x.action is SHIFT][0]
                        except IndexError:
                            t_shift = None

                        # But many REDUCE might exist
                        t_reduces = [x for x in t_acts if x.action is REDUCE]

                        # We should try to resolve using standard
                        # disambiguation rules between current reduction and
                        # all previous actions.

                        if t_shift:
                            # SHIFT/REDUCE conflict. Use assoc and priority to
                            # resolve
                            sh_prior = state._max_prior_per_symbol[
                                t_shift.state.symbol]
                            if prod.prior == sh_prior:
                                if prod.assoc == ASSOC_LEFT:
                                    # Override SHIFT with this REDUCE
                                    actions[t].remove(t_shift)
                                elif prod.assoc == ASSOC_RIGHT:
                                    # If associativity is right leave SHIFT
                                    # action as "stronger" and don't consider
                                    # this reduction any more. Right
                                    # assiciative reductions can't be in the
                                    # same set of actions together with SHIFTs.
                                    should_reduce = False

                            elif prod.prior > sh_prior:
                                # This item operation priority is higher =>
                                # override with reduce
                                actions[t].remove(t_shift)
                            else:
                                # If priority of existing SHIFT action is
                                # higher then leave it instead
                                should_reduce = False

                        if should_reduce:
                            if not t_reduces:
                                actions[t].append(new_reduce)
                            else:
                                # REDUCE/REDUCE conflicts
                                # Try to resolve using priorities
                                if prod.prior == t_reduces[0].prod.prior:
                                    actions[t].append(new_reduce)
                                elif prod.priod > t_reduces[0].prod.prior:
                                    # If this production priority is higher
                                    # it should override all other reductions.
                                    actions[t][:] = [x for x in actions[t]
                                                     if x.action is not REDUCE]
                                    actions[t].append(new_reduce)

    # Scanning optimization. Preorder actions based on terminal priority and
    # specificity. Set _finish flags.
    def act_order(act_item):
        """Priority is the strongest property. After that honor string recognizer over
        other types of recognizers.
        """
        symbol, act = act_item
        return symbol.prior * 1000000 + (500000 + len(symbol.recognizer.value)
                                         if type(symbol.recognizer)
                                         is StringRecognizer else 0)
    for state in states:
        finish_flags = []
        state.actions = OrderedDict(sorted(state.actions.items(),
                                           key=act_order, reverse=True))
        # Finish flags
        prior = None
        for symbol, act in reversed(list(state.actions.items())):
            finish_flags.append(symbol.finish
                                or (symbol.prior > prior if prior else False)
                                or type(symbol.recognizer) is StringRecognizer)
            prior = symbol.prior

        finish_flags.reverse()
        state.finish_flags = finish_flags

    table = LRTable(states, first_sets, follow_sets, grammar)
    table.calc_conflicts()
    return table


def merge_states(old_state, new_state):
    """Try to merge new_state to old_state if possible. If not possible return
    False.

    If old state has no R/R conflicts additional check is made and merging is
    not done if it would add R/R conflict.
    """

    # If states are not equal (e.g. have the same kernel items)
    # no merge is possible
    if old_state != new_state:
        return False

    item_pairs = []
    for old_item in (s for s in old_state.kernel_items if s.is_at_end):
        new_item = new_state.get_item(old_item)
        item_pairs.append((old_item, new_item))

    # Check if merging would result in additional R/R conflict
    for old, new in item_pairs:
        (new.follow.difference(old.follow))
        for s in (s for s in old_state.kernel_items
                  if s.is_at_end and s is not old):
            if s.follow.intersection(
                    new.follow.difference(old.follow)):
                return False

    # Do the merge
    for old, new in item_pairs:
        old.follow.update(new.follow)
    return True


def check_table(states, all_actions, all_goto, first_sets, follow_sets):
    """
    Return a list of errors for the given table.
    """

    errors = []
    # Check for states with GOTO links but without SHIFT links.
    # This is invalid as the GOTO link will never be traversed.
    for nt, firsts in first_sets.items():
        if nt.name != 'S\'' and not firsts:
            errors.append(
                'First set empty for grammar symbol "{}". '
                'An infinite recursion on the grammar symbol.'.format(nt))

    return errors


class LRTable(object):
    def __init__(self, states, first_sets=None, follow_sets=None,
                 grammar=None):
        self.states = states
        self.first_sets = first_sets
        self.follow_sets = follow_sets
        self.grammar = grammar

    def calc_conflicts(self):
        """
        Determine S/R and R/R conflicts.
        """
        self.sr_conflicts = []
        self.rr_conflicts = []
        for state in self.states:

            for term, actions in state.actions.items():

                # Mark state for dynamic disambiguation
                if term.dynamic:
                    state.dynamic.add(term)

                if len(actions) > 1:
                    if actions[0].action in [SHIFT, ACCEPT]:
                        # Create SR conflicts for each S-R pair of actions
                        # except EMPTY reduction as SHIFT will always be
                        # preferred in LR parsing and GLR has a special
                        # handling of EMPTY reduce in order to avoid infinite
                        # looping.
                        for r_act in actions[1:]:

                            # Mark state for dynamic disambiguation
                            if r_act.prod.dynamic:
                                state.dynamic.add(term)

                            if len(r_act.prod.rhs):
                                self.sr_conflicts.append(
                                    SRConflict(state, term,
                                               [x.prod for x in actions[1:]]))
                    else:
                        prods = [x.prod for x in actions if len(x.prod.rhs)]

                        # Mark state for dynamic disambiguation
                        if any([p.dynamic for p in prods]):
                            state.dynamic.add(term)

                        empty_prods = [x.prod for x in actions
                                       if not len(x.prod.rhs)]
                        if len(empty_prods) > 1 or len(prods) > 1:
                            self.rr_conflicts.append(
                                RRConflict(state, term, prods))

    def print_debug(self):
        print("\n\n*** STATES ***")
        for state in self.states:
            state.print_debug()

            if state.gotos:
                print("\n\n\tGOTO:")
                print("\t", ", ".join(["%s->%d" % (k, v.state_id)
                                       for k, v in state.gotos.items()]))
            print("\n\tACTIONS:")
            print("\t", ", ".join(
                ["%s->%s" % (k, str(v[0])
                             if len(v) == 1 else "[{}]".format(
                                     ",".join([str(x) for x in v])))
                 for k, v in state.actions.items()]))

        if self.sr_conflicts:
            print("\n\n*** S/R conflicts ***")
            print("There are {} S/R conflicts".format(len(self.sr_conflicts)))
            for src in self.sr_conflicts:
                print(src.message)

        if self.rr_conflicts:
            print("\n\n*** R/R conflicts ***\n")
            for rrc in self.rr_conflicts:
                print(rrc.message)
