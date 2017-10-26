from parglare.grammar import EMPTY, NonTerminal

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
    from parglare.tables import LRItem

    while True:

        has_additions = False
        to_add = []
        for item in state.items:
            gs = item.symbol_at_position
            if isinstance(gs, NonTerminal):
                for p in state.grammar.productions:

                    if p.symbol == gs:

                        if itemset_type is LR_1:
                            # Calculate follow set that is possible after the
                            # non-terminal at the given position of the current
                            # item.
                            follow = _new_item_follow(item, first_sets)
                            new_item = LRItem(p, 0, follow)
                        else:
                            new_item = LRItem(p, 0)

                        if new_item not in state.items \
                                and new_item not in to_add:

                            # If the item doesn't exists yet add it.
                            to_add.append(new_item)
                            has_additions = True

                        else:
                            # If the item already exists, this newly created
                            # item might still have a wider follows set. If so,
                            # update with the current new item follows set if
                            # we are building LR_1 items set.
                            if itemset_type is LR_1:
                                try:
                                    existing_item = state.items[
                                        state.items.index(new_item)]
                                except ValueError:
                                    existing_item = to_add[
                                        to_add.index(new_item)]

                                if not follow.issubset(existing_item.follow):
                                    existing_item.follow.update(follow)
                                    has_additions = True

        if has_additions:
            state.items.extend(to_add)
        else:
            break


def _new_item_follow(item, first_sets):
    """
    Returns follow set of possible terminals after the item's current
    non-terminal.

    Args:
    item (LRItem): The source item which is causing the creation of the
        new item.
    first_sets(dict of sets): The dict of set of first items keyed by
        a grammar symbol.
    """

    new_follow = set()
    for s in item.production.rhs[item.position + 1:]:
        new_follow.update(first_sets[s])
        if EMPTY not in new_follow:
            # If EMPTY can't be derived at current position than we have found
            # the whole follow set.
            break
        else:
            # If the EMPTY is possible at current position in this loop we must
            # continue to include firsts of the next grammar symbol.
            # EMTPY can't be a member of the follow set.
            new_follow.remove(EMPTY)
    else:
        # If the rest of production can be EMPTY we shall inherit
        # all elements of the source item follow set.
        new_follow.update(item.follow)

    return new_follow
