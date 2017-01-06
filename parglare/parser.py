# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from collections import OrderedDict
from .grammar import Grammar, NonTerminal, NULL, AUGSYMBOL, EOF, \
    ASSOC_RIGHT, ASSOC_NONE
from .exceptions import ParseError, ParserInitError, ShiftReduceConflict

SHIFT = 0
REDUCE = 1
ACCEPT = 2


class Parser(object):
    """Parser works like a DFA driven by a LR tables. For a given grammar LR table
    will be created and cached or loaded from cache if cache is found.
    """
    def __init__(self, grammar, root_symbol=None, actions=None, debug=False,
                 ws='\t\n ', skip_ws=True, default_actions=True):
        self.grammar = grammar

        self.root_symbol = \
            root_symbol if root_symbol else self.grammar.root_symbol
        if isinstance(self.root_symbol, str):
            rs = [x for x in self.grammar.nonterminals
                  if x.name == self.root_symbol]
            if rs:
                self.root_symbol = rs[0]
            else:
                raise ParserInitError("Unexisting root grammar symbol '{}'"
                                      .format(root_symbol))

        self.actions = actions if actions else {}

        self.debug = debug

        self._states = []
        self._actions = []
        self._goto = []

        self.ws = ws
        self.skip_ws = skip_ws
        self.default_actions = default_actions

        self._init_parser()

    def _init_parser(self):
        """Create parser states and tables."""
        self._first_sets = first(self.grammar)
        self._follow_sets = follow(self.grammar, self._first_sets)
        self._create_tables()

    def _create_tables(self):

        # Create a state for the first production (augmented)
        s = LRState(self, 0, AUGSYMBOL,
                    [LRItem(self.grammar.productions[0], 0)])

        state_queue = [s]
        state_id = 1

        while state_queue:
            # For each state calculate its closure first, i.e. starting from a
            # so called "kernel items" expand collection with non-kernel items.
            # We will also calculate GOTO and ACTIONS dict for each state. This
            # dict will be keyed by a grammar symbol.
            state = state_queue.pop(0)
            state.closure()
            self._states.append(state)

            # Each state has its corresponding GOTO and ACTION table
            goto = OrderedDict()
            self._goto.append(goto)
            actions = OrderedDict()
            # State with id of 1 is ending state
            if state.state_id == 1:
                actions[EOF] = Action(ACCEPT)
            self._actions.append(actions)

            # To find out other state we examine following grammar symbols
            # in the current state (symbols following current position/"dot")
            # and group all items by a grammar symbol.
            per_next_symbol = OrderedDict()
            max_prior_per_symbol = {}
            for i in state.items:
                symbol = i.production.rhs[i.position]
                if symbol:
                    per_next_symbol.setdefault(symbol, []).append(i)
                    prod_prior = i.production.prior
                    if symbol in max_prior_per_symbol:
                        old_prior = max_prior_per_symbol[symbol]
                        max_prior_per_symbol[symbol] = max(prod_prior,
                                                           old_prior)
                    else:
                        max_prior_per_symbol[symbol] = prod_prior
                else:
                    # If the position is at the end then this item
                    # would call for reduction but only for terminals
                    # from the FOLLOW set of the production LHS non-terminal.
                    for t in self._follow_sets[i.production.symbol]:
                        if t in actions:
                            # TODO: REDUCE/REDUCE conflict
                            assert False
                        else:
                            actions[t] = Action(REDUCE, prod=i.production)

            # For each group symbol we create new state and form its kernel
            # items from the group items with positions moved one step ahead.
            for symbol, items in per_next_symbol.items():
                inc_items = [i.get_pos_inc() for i in items]
                maybe_new_state = LRState(self, state_id, symbol, inc_items)
                target_state = maybe_new_state
                try:
                    idx = self._states.index(maybe_new_state)
                    target_state = self._states[idx]
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
                                self.print_debug()
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

        if self.debug:
            self.print_debug()

    def print_debug(self):
        self.grammar.print_debug()
        print("\n\n*** STATES ***")
        for s, g, a in zip(self._states, self._goto, self._actions):
            s.print_debug()

            if g:
                print("\n\n\tGOTO:")
                print("\t", ", ".join(["%s->%d" % (k, v.state_id)
                                       for k, v in g.items()]))
            print("\n\tACTIONS:")
            print("\t", ", ".join(["%s->%s" % (k, str(v))
                                   for k, v in a.items()]))

    def parse(self, input_str):
        state_stack = [self._states[0]]
        results_stack = []
        position_stack = [0]
        position = 0
        in_len = len(input_str)

        while True:
            cur_state = state_stack[-1]
            goto = self._goto[cur_state.state_id]
            actions = self._actions[cur_state.state_id]

            # Skip whitespaces
            if self.ws and self.skip_ws:
                while position < in_len and input_str[position] in self.ws:
                    position += 1

            # Find the next token in the input
            if position == in_len:
                ntok_sym = EOF
            else:
                tokens = []
                for symbol in actions:
                    tok = symbol.parse(input_str, position)
                    if tok:
                        tokens.append((symbol, tok))
                if not tokens:
                    raise ParseError(position, actions.keys())
                # Longest-match disambiguation resolution.
                ntok_sym, ntok = max(tokens, key=lambda t: len(t[1]))

            act = actions.get(ntok_sym)

            if not act:
                raise ParseError(position, actions.keys())

            if act.action is SHIFT:
                state = act.state

                res = None
                if state.symbol.name in self.actions:
                    res = self.actions[state.symbol.name](position,
                                                          state.symbol,
                                                          value=ntok)
                elif self.default_actions:
                    res = default_shift_action(position, state.symbol,
                                               value=ntok)

                state_stack.append(state)
                results_stack.append(res)
                position_stack.append(position)
                position += len(ntok)

                if self.debug:
                    print("Shift:", ntok, "at position", position)

            elif act.action is REDUCE:
                production = act.prod
                subresults = results_stack[-len(production.rhs):]
                del state_stack[-len(production.rhs):]
                del results_stack[-len(production.rhs):]
                if len(production.rhs) > 1:
                    del position_stack[-(len(production.rhs)-1):]
                cur_state = state_stack[-1]
                goto = self._goto[cur_state.state_id]

                res = None
                if act.prod.prod_symbol_id in self.actions:
                    res = self.actions[
                        act.prod.prod_symbol_id](position_stack[-1],
                                                 act.prod.symbol,
                                                 nodes=subresults)
                elif act.prod.symbol.name in self.actions:
                    res = self.actions[
                        act.prod.symbol.name](position_stack[-1],
                                              act.prod.symbol,
                                              nodes=subresults)
                elif self.default_actions:
                    res = default_reduce_action(position_stack[-1],
                                                act.prod.symbol,
                                                nodes=subresults)

                state_stack.append(goto[production.symbol])
                results_stack.append(res)

                if self.debug:
                    print("Reducing by prod '%s'." % str(production))

            elif act.action is ACCEPT:
                if self.debug:
                    print("SUCCESS!!!")
                assert len(results_stack) == 1
                return results_stack[0]


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
    __slots__ = ['parser', 'state_id', 'symbol', 'items']

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
            to_add = []
            for item in self.items:
                gs = item.production.rhs[item.position]
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


class Node(object):
    """A node of the parse tree.
    """
    __slots__ = ['position', 'symbol']

    def __init__(self, position, symbol):
        self.position = position
        self.symbol = symbol


class NodeNonTerm(Node):
    __slots__ = ['nodes']

    def __init__(self, position, symbol, nodes):
        super(NodeNonTerm, self).__init__(position, symbol)
        self.nodes = nodes

    def tree_str(self, depth=0):
        indent = '  ' * depth
        s = '{}[{}]'.format(self.symbol, self.position)
        if self.nodes:
            for n in self.nodes:
                if hasattr(n, 'tree_str'):
                    s += '\n' + indent + n.tree_str(depth+1)
                else:
                    s += '\n' + indent + str(n)
        return s

    def __str__(self):
        return '<Node({}, {})>'.format(self.position, self.symbol)


class NodeTerm(Node):
    __slots__ = ['value']

    def __init__(self, position, symbol, value):
        super(NodeTerm, self).__init__(position, symbol)
        self.value = value

    def tree_str(self, depth=0):
        return '{}[{}, {}]'.format(self.symbol, self.position,
                                   self.value)

    def __str__(self):
        return '<Node({}, {}, {})>'.format(self.position,
                                           self.symbol, self.value)


def default_shift_action(position, symbol, value):
    return NodeTerm(position, symbol, value)


def default_reduce_action(position, symbol, nodes):
    return NodeNonTerm(position, symbol, nodes)


def first(grammar):
    """Calculates the sets of terminals that can start the sentence derived from
    all grammar symbols.
    """
    assert isinstance(grammar, Grammar), \
        "grammar parameter should be Grammar instance."

    first_sets = {}
    for t in grammar.terminals:
        first_sets[t] = set([t])

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

    if first_sets is None:
        first_sets = first(grammar)

    follow_sets = {}
    for symbol in grammar.nonterminals:
        follow_sets[symbol] = set()
    follow_sets[AUGSYMBOL].add(EOF)

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
