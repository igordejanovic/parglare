# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function
import codecs
import sys
from collections import OrderedDict
from .grammar import Grammar, EMPTY, AUGSYMBOL, EOF, STOP
from .exceptions import ParseError, DisambiguationError, \
    disambiguation_error, nomatch_error, SRConflicts, RRConflicts

if sys.version < '3':
    text = unicode  # NOQA
else:
    text = str

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
    def __init__(self, grammar, start_production=1, actions=None, debug=False,
                 layout_debug=False, ws='\n\t ', default_actions=True,
                 tables=LALR, layout=False, position=False,
                 prefer_shifts=False):
        self.grammar = grammar
        self.start_production = start_production
        self.sem_actions = actions if actions else {}

        self.layout_parser = None
        if not layout:
            layout_prod = grammar.get_production_id('LAYOUT')
            if layout_prod:
                self.layout_parser = Parser(grammar,
                                            start_production=layout_prod,
                                            ws=None, layout=True,
                                            position=True,
                                            debug=layout_debug)

        self.layout = layout
        # If user recognizers are registered disable white-space skipping
        self.ws = ws if not grammar.recognizers else None
        self.position = position
        self.debug = debug
        self.layout_debug = layout_debug

        self.default_actions = default_actions

        self.prefer_shifts = prefer_shifts

        from .closure import LR_0, LR_1
        from .tables import create_table
        if tables == SLR:
            itemset_type = LR_0
        else:
            itemset_type = LR_1
        self.table = create_table(grammar, itemset_type=itemset_type,
                                  start_production=start_production)

        self._check_parser()
        if debug:
            self.print_debug()

    def _check_parser(self):
        if self.table.sr_conflicts and not self.prefer_shifts:
            self.print_debug()
            raise SRConflicts(self.table.sr_conflicts)

        # Reduce/Reduce conflicts are fatal for LR parsing
        if self.table.rr_conflicts:
            self.print_debug()
            raise RRConflicts(self.table.rr_conflicts)

    def print_debug(self):
        if self.layout and self.layout_debug:
            print('\n\n*** LAYOUT parser ***\n')
        self.table.print_debug()

    def parse_file(self, file_name):
        """
        Parses content from the given file.
        Args:
            file_name(str): A file name.
        """
        with codecs.open(file_name, 'r', 'utf-8') as f:
            content = f.read()
        return self.parse(content, file_name=file_name)

    def parse(self, input_str, position=0, file_name=None):
        """
        Parses the given input string.
        Args:
            input_str(str): A string to parse.
            position(int): Position to start from.
            file_name(str): File name if applicable. Used in error reporting.
        """

        if self.debug:
            print("*** Parsing started")

        state_stack = [self.table.states[0]]
        results_stack = []
        position_stack = [0]
        position = position

        default_actions = self.default_actions
        sem_actions = self.sem_actions
        next_token = self._next_token
        debug = self.debug

        context = type(str("Context"), (), {})

        new_token = True
        ntok = Token()

        while True:
            cur_state = state_stack[-1]
            if debug:
                print("Current state =", cur_state.state_id)

            actions = cur_state.actions

            if new_token or ntok.symbol not in actions:
                # Try to recognize a new token in the input only after
                # successful SHIFT operation, i.e. when the input position has
                # moved. REDUCE operation doesn't move position. If the current
                # ntok_sym is not in the current actions then try to find new
                # token. This could happen if old token is not available in the
                # actions of the current state but EMPTY is and will match
                # always leading to reduction.
                try:

                    position, layout_content = self._skipws(input_str,
                                                            position)
                    if self.debug:
                        print("\tLayout content: '{}'".format(layout_content))

                    ntok = next_token(cur_state, input_str, position)

                except DisambiguationError as e:
                    raise ParseError(file_name, input_str, position,
                                     disambiguation_error(e.tokens))

            if debug:
                print("\tContext:", position_context(input_str, position))
                print("\tToken ahead: {}".format(ntok))

            acts = actions.get(ntok.symbol)

            if not acts:
                raise ParseError(file_name, input_str, position,
                                 nomatch_error(actions.keys()))

            # Use first action -- SHIFT if exists there are SHIFT available or
            # REDUCE. This parser would raise exception during contstruction if
            # there are R/R conflicts or if there are S/R conflicts and
            # prefer_shifts strategy is not selected. Thus, we are safe to get
            # the first action.
            act = acts[0]

            context.position = position

            if act.action is SHIFT:
                state = act.state
                context.symbol = state.symbol
                symbol = state.symbol

                if debug:
                    print("\tShift:{} \"{}\"".format(state.state_id,
                                                     ntok.value),
                          "at position",
                          pos_to_line_col(input_str, position))

                res = None
                if symbol.name in sem_actions:
                    res = sem_actions[state.symbol.name](context, ntok.value)
                elif default_actions:
                    res = default_shift_action(context, ntok.value)

                if debug:
                    print("\tAction result = type:{} value:{}"
                          .format(type(res), repr(res)))

                state_stack.append(state)
                results_stack.append(res)
                position_stack.append(position)
                position += len(ntok.value)
                new_token = True

            elif act.action is REDUCE:
                production = act.prod
                symbol = production.symbol
                context.symbol = symbol

                if debug:
                    print("\tReducing by prod '%s'." % str(production))

                r_length = len(production.rhs)
                if r_length:
                    subresults = results_stack[-r_length:]
                    del state_stack[-r_length:]
                    del results_stack[-r_length:]
                    if r_length > 1:
                        del position_stack[-(r_length - 1):]

                    cur_state = state_stack[-1]
                    context.position = position_stack[-1]

                else:
                    subresults = []

                # Calling semantic actions
                res = None
                sem_action = sem_actions.get(symbol.name)
                if sem_action:
                    if type(sem_action) is list:
                        res = sem_action[production.prod_symbol_id](context,
                                                                    subresults)
                    else:
                        res = sem_action(context, subresults)
                elif default_actions:
                    res = default_reduce_action(context, nodes=subresults)

                if debug:
                    print("\tAction result = type:{} value:{}"
                          .format(type(res), repr(res)))

                goto = cur_state.gotos
                state_stack.append(goto[production.symbol])
                results_stack.append(res)
                new_token = False

            elif act.action is ACCEPT:
                if debug:
                    print("SUCCESS!!!")
                assert len(results_stack) == 1
                if self.position:
                    return results_stack[0], position
                else:
                    return results_stack[0]

    def _skipws(self, input_str, position):
        in_len = len(input_str)
        layout_content = ''
        if self.layout_parser:
            layout_content, pos = self.layout_parser.parse(
                input_str, position)
            layout_content = input_str[position:pos]
            position = pos
        elif self.ws:
            old_pos = position
            while position < in_len and input_str[position] in self.ws:
                position += 1
            layout_content = input_str[old_pos:position]

        if self.debug:
            print("\tSkipping whitespaces: '{}'".format(
                layout_content.replace("\n", "\\n")))
            print("\tNew position:", pos_to_line_col(input_str, position))

        return position, layout_content

    def _next_token(self, state, input_str, position):
        """
        For the current position in the input stream and actions in the current
        state find next token.
        """

        actions = state.actions
        finish_flags = state.finish_flags

        in_len = len(input_str)

        # Find the next token in the input
        if position == in_len and EMPTY not in actions \
           and STOP not in actions:
            # Execute EOF action at end of input only if EMTPY and
            # STOP terminals are not in actions as this might call
            # for reduction.
            ntok = EOF_token
        else:
            tokens = []
            for idx, symbol in enumerate(actions):
                tok = symbol.recognizer(input_str, position)
                if tok:
                    tokens.append(Token(symbol, tok))
                    if finish_flags[idx]:
                        break
            if not tokens:
                if STOP in actions:
                    ntok = STOP_token
                else:
                    ntok = EMPTY_token
            elif len(tokens) == 1:
                ntok = tokens[0]
            else:
                ntok = self._lexical_disambiguation(tokens)

        return ntok

    def _lexical_disambiguation(self, tokens):
        """
        For the given list of matched tokens apply disambiguation strategy.

        Args:
        tokens (list of Token)
        """

        if self.debug:
            print("\tLexical disambiguation. Tokens:",
                  [x for x in tokens])

        # Longest-match strategy.
        max_len = max((len(x.value) for x in tokens))
        tokens = [x for x in tokens if len(x.value) == max_len]
        if self.debug:
            print("\tDisambiguation by longest-match strategy. Tokens:",
                  [x for x in tokens])
        if len(tokens) == 1:
            return tokens[0]
        else:
            # Finally try to find preferred token.
            pref_tokens = [x for x in tokens if x.symbol.prefer]
            if len(pref_tokens) == 1:
                if self.debug:
                    print("\tPreferring token {}.".format(pref_tokens[0]))
                return pref_tokens[0]
            elif len(pref_tokens) > 1:
                tokens = pref_tokens

        raise DisambiguationError(tokens)


class Action(object):
    __slots__ = ['action', 'state', 'prod']

    def __init__(self, action, state=None, prod=None):
        self.action = action
        self.state = state
        self.prod = prod

    def __str__(self):
        ac = {SHIFT: 'SHIFT',
              REDUCE: 'REDUCE',
              ACCEPT: 'ACCEPT'}.get(self.action)
        if self.action == SHIFT:
            p = self.state.state_id
        elif self.action == REDUCE:
            p = self.prod.prod_id
        else:
            p = ''
        return '%s%s' % (ac, ':%d' % p if p else '')


class LRItem(object):
    """
    Represents an item in the items set. Item is defined by a production and a
    position inside production (the dot). If the item is of LR_1 type follow
    set is also defined. Follow set is a set of terminals that can follow
    non-terminal at given position in the given production.
    """
    __slots__ = ('production', 'position', 'follow')

    def __init__(self, production, position, follow=None):
        self.production = production
        self.position = position
        self.follow = set() if not follow else follow

    def __eq__(self, other):
        return other and self.production == other.production and \
            self.position == other.position

    def __ne__(self, other):
        return not self == other

    def __repr__(self):
        return str(self)

    def __str__(self):
        s = []
        for idx, r in enumerate(self.production.rhs):
            if idx == self.position:
                s.append(".")
            s.append(str(r))
        if len(self.production.rhs) == self.position:
            s.append(".")
        s = " ".join(s)

        follow = "{{{}}}".format(", ".join([str(t) for t in self.follow])) \
                 if self.follow else "{}"

        return "%d: %s = %s   %s" % (self.production.prod_id,
                                     self.production.symbol, s,
                                     follow)

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

    @property
    def symbol_at_position(self):
        """
        Returns symbol from production RHS at the position of this item.
        """
        return self.production.rhs[self.position]

    @property
    def is_at_end(self):
        """
        Is the position at the end? If so, it is a candidate for reduction.
        """
        return self.position == len(self.production.rhs)


class LRState(object):
    """LR State is a set of LR items and a dict of LR automata actions and
    gotos.

    """
    __slots__ = ['grammar', 'state_id', 'symbol', 'items',
                 'actions', 'gotos', 'finish_flags',
                 '_per_next_symbol', '_max_prior_per_symbol']

    def __init__(self, grammar, state_id, symbol, items):
        self.grammar = grammar
        self.state_id = state_id
        self.symbol = symbol
        self.items = items if items else []

        self.actions = OrderedDict()
        self.gotos = OrderedDict()

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

    def __ne__(self, other):
        return not self == other

    @property
    def kernel_items(self):
        """
        Returns kernel items of this state.
        """
        return [i for i in self.items if i.is_kernel]

    @property
    def nonkernel_items(self):
        """
        Returns nonkernel items of this state.
        """
        return [i for i in self.items if not i.is_kernel]

    def get_item(self, other_item):
        """
        Get this state item that is equal to the given other_item.
        """
        return self.items[self.items.index(other_item)]

    def __str__(self):
        s = "\nState %d" % self.state_id
        for i in self.items:
            s += "\t{}\n".format(i)
        return s

    def __unicode__(self):
        return str(self)

    def print_debug(self):
        print(text(self))


class Node(object):
    """A node of the parse tree."""
    def __init__(self, position, symbol):
        self.position = position
        self.symbol = symbol


class NodeNonTerm(Node):
    __slots__ = ['position', 'symbol', 'nodes']

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
    __slots__ = ['position', 'symbol', 'value']

    def __init__(self, position, symbol, value):
        super(NodeTerm, self).__init__(position, symbol)
        self.value = value

    def tree_str(self, depth=0):
        return '{}[{}, {}]'.format(self.symbol, self.position,
                                   self.value)

    def __str__(self):
        return '<NodeTerm({}, {}, {})>'.format(self.position,
                                               self.symbol, self.value)

    def __repr__(self):
        return str(self)


class Token(object):
    """
    Token or lexeme matched from the input.
    """
    __slots__ = ['symbol', 'value']

    def __init__(self, symbol=None, value=''):
        self.symbol = symbol
        self.value = value

    def __repr__(self):
        return "<{}({})>".format(text(self.symbol), text(self.value))


STOP_token = Token(STOP)
EMPTY_token = Token(EMPTY)
EOF_token = Token(EOF)


def default_shift_action(context, value):
    return NodeTerm(context.position, context.symbol, value)


def default_reduce_action(context, nodes):
    return NodeNonTerm(context.position, context.symbol, nodes)


def first(grammar):
    """Calculates the sets of terminals that can start the sentence derived from
    all grammar symbols.

    The Dragon book p. 221.
    """
    assert isinstance(grammar, Grammar), \
        "grammar parameter should be Grammar instance."

    first_sets = {}
    for t in grammar.terminals:
        first_sets[t] = set([t])
    for nt in grammar.nonterminals:
        first_sets[nt] = set()

    additions = True
    while additions:
        additions = False

        for p in grammar.productions:
            nonterm = p.symbol
            for rhs_symbol in p.rhs:
                rhs_symbol_first = set(first_sets[rhs_symbol])
                rhs_symbol_first.discard(EMPTY)
                if rhs_symbol_first.difference(first_sets[nonterm]):
                    first_sets[nonterm].update(first_sets[rhs_symbol])
                    additions = True
                # If current RHS symbol can't derive EMPTY
                # this production can't add any more members of
                # the first set for LHS nonterminal.
                if EMPTY not in first_sets[rhs_symbol]:
                    break
            else:
                # If we reached the end of the RHS and each
                # symbol along the way could derive EMPTY than
                # we must add EMPTY to the first set of LHS symbol.
                first_sets[nonterm].add(EMPTY)

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

    additions = True
    while additions:
        additions = False
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
                            additions = True
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
    c = text(input_str[start:position]) + "*" \
        + text(input_str[position:position+10])
    c = c.replace("\n", "\\n")
    return c
