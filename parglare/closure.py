from parglare import NonTerminal
from parglare.parser import LRItem
from parglare.grammar import EMPTY

LR_0 = 0
LR_1 = 1


def closure(state, itemset_type, first_sets=None):
    """
    For the given LRState calculates its LR(0)/LR(1) itemset closure.

    Args:
    state(LRState):
    itemset_type(int): LR_0 or LR_1
    first_sets(dict of sets): Used in LR_1 itemsets calculation.
    """

    while True:
        has_additions = False
        to_add = []
        for item in state.items:
            gs = item.production.rhs[item.position]
            if isinstance(gs, NonTerminal):
                for p in state.parser.grammar.productions:
                    if p.symbol == gs:

                        if itemset_type is LR_1:
                            # Calculate follow set that is possible at
                            # after the non-terminal at the given position
                            follow = new_item_follow(item, first_sets)
                            new_item = LRItem(p, 0, follow)
                        else:
                            new_item = LRItem(p, 0)

                        if new_item not in state.items \
                                and new_item not in to_add:
                            to_add.append(new_item)
                            has_additions = True
                        else:
                            if itemset_type is LR_1:
                                try:
                                    existing_item = state.items[
                                        state.items.index(new_item)]
                                except ValueError:
                                    existing_item = to_add[
                                        to_add.index(new_item)]

                                if not follow.issubset(
                                        existing_item.follow):
                                    existing_item.follow.update(follow)
                                    has_additions = True

        if has_additions:
            state.items.extend(to_add)
        else:
            break


def new_item_follow(item, first_sets):
    """
    Returns follow set of possible terminals after the item current
    non-terminal.

    Args:
    item (LRItem)
    """

    new_follow = set()
    for s in item.production.rhs[item.position + 1:]:
        new_follow.update(first_sets[s])
        if EMPTY not in new_follow:
            break
        else:
            new_follow.remove(EMPTY)
    else:
        # If the rest of production can be EMPTY we shall inherit
        # elements of the parent item follow set.
        new_follow.update(item.follow)

    return new_follow
