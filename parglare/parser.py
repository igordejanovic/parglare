# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from collections import OrderedDict
from .grammar import Grammar, NonTerminal, NULL, AUGSYMBOL, EOF
from .exceptions import NotInitialized, ParseError

SHIFT = 0
REDUCE = 1
ACCEPT = 2


class Parser(object):
    """Parser works like a DFA driven by a LR tables. For a given grammar LR table
    will be created and cached or loaded from cache if cache is found.
    """
    def __init__(self, grammar, root_symbol=None, debug=False):
        self.grammar = grammar
        if root_symbol is None:
            root_symbol = self.grammar.productions[0].symbol
        self.grammar.init_grammar(root_symbol)
        self.root_symbol = root_symbol
        self.debug = debug

        self.states = []
        self.actions = []
        self.goto = []

        self._init_parser()

    def _init_parser(self):
        """Create parser states and tables."""
        self.first_sets = first(self.grammar)
        self.follow_sets = follow(self.grammar, self.first_sets)
        self._create_tables()

    def _create_tables(self):

        # Create a state for the first production (augmented)
        s = LRState(self, 0, AUGSYMBOL,
                    [LRItem(self.grammar.productions[0], 0)])

        state_queue = [s]
        state_id = 1

        while state_queue:
            # For each state calculate its closure first, i.e. starting from
            # a so called "kernel items" expand collection with non-kernel
            # items. We will also calculate GOTO dict for each state.
            # This dict will be keyed by a grammar symbol.
            s = state_queue.pop(0)
            s.closure()
            self.states.append(s)

            # Each state has its corresponding GOTO table
            goto = OrderedDict()
            self.goto.append(goto)
            actions = OrderedDict()
            if s.state_id == 1:
                actions[EOF] = Action(ACCEPT)
            self.actions.append(actions)

            # To find out other state we examine following grammar symbols
            # in the current state (symbols following current position/"dot")
            # and group all items by a grammar symbol.
            per_next_symbol = OrderedDict()
            for i in s.items:
                symbol = i.production.rhs[i.position]
                if symbol:
                    per_next_symbol.setdefault(symbol, []).append(i)
                else:
                    # If the position is at the end then this item
                    # would call for reduction but only for terminals
                    # from the FOLLOW set of the production LHS non-terminal.
                    for t in self.follow_sets[i.production.symbol]:
                        if t in actions:
                            # TODO: REDUCE/REDUCE conflict
                            assert False
                        else:
                            actions[t] = Action(REDUCE, prod=i.production)

            # For each group symbol we create new state and form its kernel
            # items from the group items with position moved one step ahead.
            for symbol, items in per_next_symbol.items():
                inc_items = [i.get_pos_inc() for i in items]
                maybe_new_state = LRState(self, state_id, symbol, inc_items)
                target_state = maybe_new_state
                try:
                    idx = self.states.index(maybe_new_state)
                    target_state = self.states[idx]
                except ValueError:
                    try:
                        idx = state_queue.index(maybe_new_state)
                        target_state = state_queue[idx]
                    except ValueError:
                        pass

                # We register a state only if it doesn't exists from before.
                if target_state is maybe_new_state:
                    state_queue.append(target_state)
                    state_id += 1

                if isinstance(symbol, NonTerminal):
                    # For each non-terminal symbol we create an entry in GOTO
                    # table.
                    goto[symbol] = target_state
                else:
                    if symbol in actions:
                        # TODO: SHIFT/REDUCE conflict
                        assert False
                    actions[symbol] = Action(SHIFT, state=target_state)

        if self.debug:
            self.print_debug()

    def print_debug(self):
        self.grammar.print_debug()
        print("\n\n*** STATES ***")
        for s, g, a in zip(self.states, self.goto, self.actions):
            s.print_debug()

            if g:
                print("\n\n\tGOTO:")
                print("\t", ", ".join(["%s->%d" % (k, v.state_id)
                                       for k, v in g.items()]))
            print("\n\tACTIONS:")
            print("\t", ", ".join(["%s->%s" % (k, str(v))
                                   for k, v in a.items()]))

    def parse(self, input_str):
        state_stack = [self.states[0]]
        position = 0

        while True:
            cur_state = state_stack[-1]
            goto = self.goto[cur_state.state_id]
            actions = self.actions[cur_state.state_id]

            # Find next token on the input
            if position == len(input_str):
                ntok_sym = EOF
            else:
                tokens = []
                for symbol in actions:
                    tok = symbol.parse(input_str[position:])
                    if tok:
                        tokens.append((symbol, tok))
                if not tokens:
                    raise ParseError(position, actions)
                ntok_sym, ntok = max(tokens, key=lambda t: len(t[1]))

            if ntok_sym is EOF and EOF in actions and \
                    actions[EOF].action is ACCEPT:
                if self.debug:
                    print("SUCCESS!!!")
                break
            else:
                act = actions[ntok_sym]

                if act.action is SHIFT:
                    state = act.state
                    position += len(ntok)
                    state_stack.append(state)
                    if self.debug:
                        print("Shift: ", ntok)
                elif act.action is REDUCE:
                    production = act.prod
                    del state_stack[-len(production.rhs):]
                    cur_state = state_stack[-1]
                    goto = self.goto[cur_state.state_id]
                    state_stack.append(goto[production.symbol])
                    if self.debug:
                        print("Reducing by prod '%s'." % str(production))


class Action(object):
    __slots__ = ['action', 'state', 'prod']

    def __init__(self, action, state=None, prod=None):
        self.action = action
        self.state = state
        self.prod = prod

    def __str__(self):
        ac = {0: 'SHIFT', 1: 'REDUCE', 2: 'ACCEPT'}.get(self.action)
        if self.action == 0:
            p = self.state.state_id
        elif self.action == 1:
            p = self.prod.prod_id
        else:
            p = ''
        return '%s%s' % (ac, ':%d' % p if p else '')


class LRItem(object):
    __slots__ = ('production', 'position')

    def __init__(self, production, position):
        self.production = production
        self.position = position

    def __eq__(self, other):
        return other and self.production == other.production and \
            self.position == other.position

    def __repr__(self):
        return str(self)

    def __str__(self):
        s = ""
        for idx, r in enumerate(self.production.rhs):
            if idx == self.position:
                s += " ."
            s += " " + str(r)
        if len(self.production.rhs) == self.position:
            s += " ."

        return "%s -> %s" % (self.production.symbol, s)

    @property
    def is_kernel(self):
        """
        Kernel items are items whose position is not at the beginning.
        The only exception to this rule is start symbol of the augmented
        grammar.
        """
        return self.position > 0 or self.production.symbol is AUGSYMBOL

    def get_pos_inc(self):
        """
        Returns new LRItem with incremented position or None if position
        cannot be incremented (e.g. it is already at the end of the production)
        """

        if self.position < len(self.production.rhs):
            return LRItem(self.production, self.position+1)


class LRState(object):
    """LR State is a set of LR items."""

    def __init__(self, parser, state_id, symbol, items):
        self.parser = parser
        self.state_id = state_id
        self.symbol = symbol
        self.items = items if items else []

    def __eq__(self, other):
        """Two states are equal if their kernel items are equal."""
        for item in self.items:
            if item.is_kernel:
                if item not in other.items:
                    return False
        return True

    def closure(self):
        """Forms a closure of the state. Adds all missing items."""

        while True:
            has_additions = False
            for item in self.items:
                gs = item.production.rhs[item.position]
                to_add = []
                if isinstance(gs, NonTerminal):
                    for p in self.parser.grammar.productions:
                        if p.symbol is gs:
                            new_item = LRItem(p, 0)
                            if new_item not in self.items:
                                to_add.append(new_item)
                                has_additions = True

            if has_additions:
                self.items.extend(to_add)
            else:
                break

    def print_debug(self):
        print("\nState %d" % self.state_id)
        for i in self.items:
            print("\t", i)


def first(grammar):
    """Calculates the sets of terminals that can start the sentence derived from
    all grammar symbols.
    """
    assert isinstance(grammar, Grammar), \
        "grammar parameter should be Grammar instance."
    first_sets = {}
    try:
        for t in grammar.terminals:
            first_sets[t] = set([t])
    except AttributeError:
        raise NotInitialized()

    def _first(nt):
        if nt in first_sets:
            return first_sets[nt]
        fs = set()
        first_sets[nt] = fs
        for p in grammar.productions:
            if p.symbol is nt:
                pfs = set()
                for r in p.rhs:
                    f = _first(r)
                    pfs.update(f)
                    if NULL not in f:
                        pfs.discard(NULL)
                        break
                fs.update(pfs)
        return fs

    for p in grammar.nonterminals:
        first_sets[p] = _first(p)

    return first_sets


def follow(grammar, first_sets=None):
    """Calculates the sets of terminals that can follow some non-terminal for the
    given grammar.

    Args:
    grammar (Grammar): An initialized grammar.
    first_sets (dict): A sets of FIRST terminals keyed by a grammar symbol.
    """

    if not hasattr(grammar, 'nonterminals'):
        raise NotInitialized()

    if first_sets is None:
        first_sets = first(grammar)

    follow_sets = {}
    for symbol in grammar.nonterminals:
        follow_sets[symbol] = set()
    follow_sets[grammar.root_symbol].add(EOF)

    has_additions = True
    while has_additions:
        has_additions = False
        for symbol in grammar.nonterminals:
            for p in grammar.productions:
                for idx, s in enumerate(p.rhs):
                    if s is symbol:
                        prod_follow = set()
                        for rsymbol in p.rhs[idx+1:]:
                            sfollow = first_sets[rsymbol]
                            prod_follow.update(sfollow)
                            if NULL not in sfollow:
                                break
                        else:
                            prod_follow.update(follow_sets[p.symbol])
                        prod_follow.discard(NULL)
                        if prod_follow.difference(follow_sets[symbol]):
                            has_additions = True
                            follow_sets[symbol].update(prod_follow)
    return follow_sets
