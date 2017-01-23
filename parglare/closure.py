from parglare import NonTerminal
from parglare.parser import LRItem


def closure_lr0(state):
    """
    For the given LRState calculates its LR(0) itemset closure.
    """

    while True:
        has_additions = False
        to_add = []
        for item in state.items:
            gs = item.production.rhs[item.position]
            if isinstance(gs, NonTerminal):
                for p in state.parser.grammar.productions:
                    if p.symbol == gs:
                        new_item = LRItem(p, 0)
                        if new_item not in state.items \
                                and new_item not in to_add:
                            to_add.append(new_item)
                            has_additions = True

        if has_additions:
            state.items.extend(to_add)
        else:
            break
