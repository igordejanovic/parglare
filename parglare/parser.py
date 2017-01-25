# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function
from .grammar import Grammar, EMPTY, AUGSYMBOL, EOF
from .exceptions import ParseError, ParserInitError

SHIFT = 0
REDUCE = 1
ACCEPT = 2

# Tables construction algorithms
SLR = 0
LALR = 1


class Parser(object):
    """Parser works like a DFA driven by LR tables. For a given grammar LR table
    will be created and cached or loaded from cache if cache is found.
    """
    def __init__(self, grammar, root_symbol=None, actions=None, debug=False,
                 ws='\t\n ', skip_ws=True, default_actions=True, tables=SLR):
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

        from .closure import LR_0, LR_1
        from .tables import create_tables
        if tables == SLR:
            itemset_type = LR_0
        else:
            itemset_type = LR_1
        create_tables(self, itemset_type)

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
        """ LR parsing. """

        if self.debug:
            print("\n\n*** Parsing started")

        state_stack = [self._states[0]]
        results_stack = []
        position_stack = [0]
        position = 0
        in_len = len(input_str)

        context = type(str("Context"), (), {})

        while True:
            cur_state = state_stack[-1]
            if self.debug:
                print("Current state =", cur_state.state_id)
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
                    raise ParseError(input_str, position, actions.keys())
                # Longest-match disambiguation resolution.
                ntok_sym, ntok = max(tokens, key=lambda t: len(t[1]))

            act = actions.get(ntok_sym)

            if not act:
                raise ParseError(input_str, position, actions.keys())

            context.position = position

            if act.action is SHIFT:
                state = act.state
                context.symbol = state.symbol

                if self.debug:
                    print("\tShift:{} \"{}\"".format(state.state_id, ntok),
                          "at position",
                          pos_to_line_col(input_str, position),
                          "=>", position_context(input_str, position))

                res = None
                if state.symbol.name in self.actions:
                    res = self.actions[state.symbol.name](context, ntok)
                elif self.default_actions:
                    res = default_shift_action(context, ntok)

                if self.debug:
                    print("\tAction result =", str(res))

                state_stack.append(state)
                results_stack.append(res)
                position_stack.append(position)
                position += len(ntok)

            elif act.action is REDUCE:
                production = act.prod
                context.symbol = act.prod.symbol

                if self.debug:
                    print("\tReducing by prod '%s'." % str(production))

                subresults = results_stack[-len(production.rhs):]
                del state_stack[-len(production.rhs):]
                del results_stack[-len(production.rhs):]
                if len(production.rhs) > 1:
                    del position_stack[-(len(production.rhs)-1):]
                cur_state = state_stack[-1]
                goto = self._goto[cur_state.state_id]
                context.position = position_stack[-1]

                res = None
                if act.prod.prod_symbol_id in self.actions:
                    res = self.actions[
                        act.prod.prod_symbol_id](context, subresults)
                elif act.prod.symbol.name in self.actions:
                    res = self.actions[
                        act.prod.symbol.name](context, subresults)
                elif self.default_actions:
                    res = default_reduce_action(context, nodes=subresults)

                if self.debug:
                    print("\tAction result =", str(res))

                state_stack.append(goto[production.symbol])
                results_stack.append(res)

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
    __slots__ = ('production', 'position', 'follow')

    def __init__(self, production, position, follow=None):
        self.production = production
        self.position = position
        self.follow = set() if not follow else follow

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

        return "%d: %s = %s   follow=%s" % (self.production.prod_id,
                                            self.production.symbol, s,
                                            self.follow)

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
            return LRItem(self.production, self.position+1, self.follow)


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
        this_kernel = [x for x in self.items if x.is_kernel]
        other_kernel = [x for x in other.items if x.is_kernel]
        if len(this_kernel) != len(other_kernel):
            return False
        for item in this_kernel:
            if item not in other_kernel:
                return False
        return True

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
                    s += '\n' + indent + n.__class__.__name__ \
                         + '(' + str(n) + ')'
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


def default_shift_action(context, value):
    return NodeTerm(context.position, context.symbol, value)


def default_reduce_action(context, nodes):
    return NodeNonTerm(context.position, context.symbol, nodes)


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
            if p.symbol == nt:
                pfs = set()
                for r in p.rhs:
                    if r == nt:
                        pfs.discard(EMPTY)
                        break
                    f = _first(r)
                    pfs.update(f)
                    if EMPTY not in f:
                        pfs.discard(EMPTY)
                        break
                fs.update(pfs)
        return fs

    for nt in grammar.nonterminals:
        first_sets[nt] = _first(nt)

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
                    if s == symbol:
                        prod_follow = set()
                        for rsymbol in p.rhs[idx+1:]:
                            sfollow = first_sets[rsymbol]
                            prod_follow.update(sfollow)
                            if EMPTY not in sfollow:
                                break
                        else:
                            prod_follow.update(follow_sets[p.symbol])
                        prod_follow.discard(EMPTY)
                        if prod_follow.difference(follow_sets[symbol]):
                            has_additions = True
                            follow_sets[symbol].update(prod_follow)
    return follow_sets


def pos_to_line_col(input_str, position):
    """
    Returns position in the (line,column) form.
    """
    line = 1
    old_pos = 0
    try:
        cur_pos = input_str.index("\n")
        while cur_pos < position:
            line += 1
            old_pos = cur_pos + 1
            cur_pos = input_str.index("\n", cur_pos + 1)
    except ValueError:
        pass

    return line, position - old_pos


def position_context(input_str, position):
    """
    Returns position context string.
    """
    start = max(position-10, 0)
    c = input_str[start:position] + "*" \
        + input_str[position:position+10]
    c = c.replace("\n", "\\n")
    return c
