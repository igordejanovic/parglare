# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function
import codecs
import sys
from collections import OrderedDict
from .grammar import Grammar, EMPTY, AUGSYMBOL, EOF, STOP
from .errors import Error, expected_symbols_str
from .exceptions import ParseError, DisambiguationError, \
    DynamicDisambiguationConflict, disambiguation_error, \
    nomatch_error, SRConflicts, RRConflicts

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
    def __init__(self, grammar, start_production=1, actions=None,
                 layout_actions=None, debug=False, debug_trace=False,
                 debug_layout=False, ws='\n\t ', build_tree=False,
                 tables=LALR, layout=False, position=False,
                 prefer_shifts=False, error_recovery=False,
                 dynamic_filter=None):
        self.grammar = grammar
        self.start_production = start_production
        self.sem_actions = actions if actions else {}

        self.layout_parser = None
        if not layout:
            layout_prod = grammar.get_production_id('LAYOUT')
            if layout_prod:
                self.layout_parser = Parser(grammar,
                                            start_production=layout_prod,
                                            actions=layout_actions,
                                            ws=None, layout=True,
                                            position=True,
                                            debug=debug_layout)

        self.layout = layout
        # If user recognizers are registered disable white-space skipping
        self.ws = ws if not grammar.recognizers else None
        self.position = position
        self.debug = debug
        self.debug_trace = debug_trace
        self.debug_layout = debug_layout

        self.build_tree = build_tree

        self.prefer_shifts = prefer_shifts

        self.error_recovery = error_recovery
        self.dynamic_filter = dynamic_filter

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
            if self.dynamic_filter:
                unhandled_conflicts = []
                for src in self.table.sr_conflicts:
                    if not src.dynamic:
                        unhandled_conflicts.append(src)
            else:
                unhandled_conflicts = self.table.sr_conflicts

            if unhandled_conflicts:
                raise SRConflicts(unhandled_conflicts)

        # Reduce/Reduce conflicts are fatal for LR parsing
        if self.table.rr_conflicts:
            self.print_debug()
            if self.dynamic_filter:
                unhandled_conflicts = []
                for rrc in self.table.rr_conflicts:
                    if not rrc.dynamic:
                        unhandled_conflicts.append(rrc)
            else:
                unhandled_conflicts = self.table.rr_conflicts

            if unhandled_conflicts:
                raise RRConflicts(unhandled_conflicts)

    def print_debug(self):
        if self.layout and self.debug_layout:
            print('\n\n*** LAYOUT parser ***\n')
        self.table.print_debug()

    def parse_file(self, file_name, **kwargs):
        """
        Parses content from the given file.
        Args:
            file_name(str): A file name.
        """
        with codecs.open(file_name, 'r', 'utf-8') as f:
            content = f.read()
        return self.parse(content, file_name=file_name, **kwargs)

    def parse(self, input_str, position=0, file_name=None, context=None):
        """
        Parses the given input string.
        Args:
            input_str(str): A string to parse.
            position(int): Position to start from.
            file_name(str): File name if applicable. Used in error reporting.
            context(Context): An object used to keep parser context info.
        """

        if self.debug:
            print("*** Parsing started")

        self.errors = []
        self.current_error = None

        if self.dynamic_filter:
            if self.debug:
                print("\tInitializing dynamic disambiguation.")
            self.dynamic_filter(None, None, None, None, None)

        state_stack = [StackNode(self.table.states[0], position, 0, None,
                                 None)]
        context = Context() if not context else context

        next_token = self._next_token
        debug = self.debug

        new_token = True
        ntok = Token()

        while True:
            cur_state = state_stack[-1].state
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

                    position, layout_content = self._skipws(context, input_str,
                                                            position)
                    if self.debug:
                        print("\tLayout content: '{}'".format(layout_content))

                    ntok = next_token(cur_state, input_str, position)
                    context.layout_content = layout_content

                except DisambiguationError as e:
                    raise ParseError(file_name, input_str, position,
                                     disambiguation_error(e.tokens))

            context.parser = self
            context.start_position = position
            context.end_position = position + len(ntok.value)
            context.layout_content = layout_content

            if debug:
                print("\tContext:", position_context(input_str, position))
                print("\tTokens expected: {}"
                      .format(expected_symbols_str(actions.keys())))
                print("\tToken ahead: {}".format(ntok))

            acts = actions.get(ntok.symbol)

            if not acts:

                if self.error_recovery:
                    # If we are past end of input error recovery can't be
                    # successful and the only thing we can do is to throw
                    # ParserError
                    if position > len(input_str):
                        e = self.current_error
                        raise ParseError(file_name, input_str, e.position,
                                         nomatch_error(actions.keys()))
                    if debug:
                        print("**Error found. Recovery initiated.**")
                    # No actions to execute. Try error recovery.
                    if type(self.error_recovery) is bool:
                        # Default recovery
                        error, position, ntok = self.default_error_recovery(
                            input_str, position, set(actions.keys()))
                    else:
                        # Custom recovery provided during parser construction
                        ntok, error, position = self.error_recovery(
                            self, input_str, position, set(actions.keys()))

                    # The recovery may either decide to skip erroneous part
                    # of the input and resume at the place that can
                    # continue or it might decide to fill in/replace
                    # missing/invalid tokens.
                    if error:
                        if debug:
                            print("\tError: {}".format(str(error)))
                        self.errors.append(error)

                    if not ntok:
                        # If token is not created we are just droping current
                        # input and advancing position. Thus, stay in the same
                        # state and try to continue.
                        if debug:
                            print("\tContinuing at position {}.".format(
                                pos_to_line_col(input_str, position)))

                        new_token = True
                        continue

                    else:
                        acts = actions.get(ntok.symbol)

            if not acts:
                raise ParseError(file_name, input_str, position,
                                 nomatch_error(actions.keys()))

            # Dynamic disambiguation
            if self.dynamic_filter:
                dacts = []
                for a in acts:
                    if a.action is SHIFT:
                        if self._call_dynamic_filter(
                                SHIFT, ntok, None, None, cur_state):
                            dacts.append(a)
                    elif a.action is REDUCE:
                        r_len = len(a.prod.rhs)
                        if r_len:
                            subresults = [x.result
                                          for x in state_stack[-r_len:]]
                        else:
                            subresults = []
                        if self._call_dynamic_filter(
                                REDUCE, ntok, a.prod, subresults, cur_state):
                            dacts.append(a)
                    else:
                        dacts.append(a)

                acts = dacts

                # If after dynamic disambiguation we still have at least one
                # shift and non-empty reduction or multiple non-empty
                # reductions raise exception.
                if len([a for a in acts
                        if (a.action is SHIFT)
                        or ((a.action is REDUCE) and len(a.prod.rhs))]) > 1:
                    raise DynamicDisambiguationConflict(cur_state, ntok, acts)

            # If dynamic disambiguation is disabled either globaly by not
            # giving disambiguation function or localy by not marking
            # any poduction dynamic for this state take the first action.
            # First action is either SHIFT while there might be empty
            # reductions, or it is the only reduction.
            # Otherwise, parser construction should raise an error.
            act = acts[0]

            if act.action is SHIFT:
                state = act.state
                symbol = state.symbol
                context.symbol = symbol

                if debug:
                    print("\tShift:{} \"{}\"".format(state.state_id,
                                                     ntok.value),
                          "at position",
                          pos_to_line_col(input_str, position))

                result = self._call_shift_action(symbol, ntok.value, context)

                # If in error recovery mode, get out.
                self.current_error = None

                state_stack.append(StackNode(state,
                                             context.start_position,
                                             context.end_position,
                                             context.layout_content,
                                             result))
                position = context.end_position
                new_token = True

            elif act.action is REDUCE:
                # if this is EMPTY reduction try to take another if
                # exists.
                if len(act.prod.rhs) == 0:
                    if len(acts) > 1:
                        act = acts[1]
                production = act.prod
                symbol = production.symbol
                context.symbol = symbol
                context.production = production

                if debug:
                    print("\tReducing by prod '%s'." % str(production))

                r_length = len(production.rhs)
                if r_length:
                    context.end_position = state_stack[-1].end_position
                    context.start_position = \
                        state_stack[-r_length].start_position
                    context.layout_content = \
                        state_stack[-r_length].layout_content
                    subresults = [x.result for x in state_stack[-r_length:]]
                    del state_stack[-r_length:]
                    cur_state = state_stack[-1].state
                else:
                    subresults = []
                    context.end_position = position
                    context.start_position = position
                    context.layout_content = ''

                # Calling reduce action
                result = self._call_reduce_action(production, subresults,
                                                  context)

                cur_state = cur_state.gotos[production.symbol]
                state_stack.append(StackNode(cur_state,
                                             context.start_position,
                                             context.end_position,
                                             context.layout_content,
                                             result))
                new_token = False

            elif act.action is ACCEPT:
                if debug:
                    print("SUCCESS!!!")
                assert len(state_stack) == 2
                if self.position:
                    return state_stack[1].result, position
                else:
                    return state_stack[1].result

    def call_actions(self, node, actions, context=None):
        """
        Calls semantic actions for the given tree node.
        """
        self.context = context = context if context else Context()
        context.parser = self

        def set_context(context, node):
            context.start_position = node.start_position
            context.end_position = node.end_position
            context.node = node
            context.symbol = node.symbol
            context.layout_content = node.layout_content

        def inner_call_actions(node):
            sem_action = node.symbol.action
            if not sem_action:
                sem_action = actions.get(node.symbol.name)
            if sem_action:
                if isinstance(node, NodeTerm):
                    set_context(context, node)
                    return sem_action(context, node.value)
                else:
                    results = []
                    # Recursive right to left, bottom up. Simulate LR
                    # reductions.
                    for n in reversed(node):
                        results.append(inner_call_actions(n))
                    results.reverse()

                    set_context(context, node)
                    context.production = node.production
                    if type(sem_action) is list:
                        result = \
                            sem_action[
                                node.production.prod_symbol_id](context,
                                                                results)
                    else:
                        result = sem_action(context, results)
            else:
                result = node
            return result

        return inner_call_actions(node)

    def _skipws(self, context, input_str, position):
        in_len = len(input_str)
        layout_content = ''
        if self.layout_parser:
            layout_content, pos = self.layout_parser.parse(
                input_str, position, context=context)
            if not layout_content:
                layout_content = input_str[position:pos]
            position = pos
        elif self.ws:
            old_pos = position
            while position < in_len and input_str[position] in self.ws:
                position += 1
            layout_content = input_str[old_pos:position]

        if self.debug:
            content = layout_content.replace("\n", "\\n") \
                      if type(layout_content) is text else layout_content
            print("\tSkipping whitespaces: '{}'".format(content))
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
            if position < in_len:
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

    def _call_shift_action(self, symbol, matched_str, context):
        """
        Calls registered shift action for the given grammar symbol.
        """
        debug = self.debug

        if self.build_tree:
            # call action for building tree node if tree building is enabled
            if debug:
                print("\tBuilding terminal node for '{}'. "
                      .format(symbol.name))
            return treebuild_shift_action(context, matched_str)

        # Get action defined by the grammar
        sem_action = symbol.action
        if not sem_action:
            # Override grammar action if given explicitely in the actions dict
            sem_action = self.sem_actions.get(symbol.name)

        if sem_action:
            result = sem_action(context, matched_str)

        else:
            if debug:
                print("\tNo action defined for '{}'. "
                      "Result is matched string.".format(symbol.name))
            result = matched_str

        if debug:
            print("\tAction result = type:{} value:{}"
                  .format(type(result), repr(result)))

        return result

    def _call_reduce_action(self, production, subresults, context):
        """
        Calls registered reduce action for the given grammar symbol.
        """
        debug = self.debug
        result = None

        if self.build_tree:
            # call action for building tree node if enabled.
            if debug:
                print("\tBuilding non-terminal node '{}'."
                      .format(production.symbol.name))
            return treebuild_reduce_action(context, nodes=subresults)

        # Get action defined by the grammar
        sem_action = production.symbol.action

        if not sem_action:
            # Override grammar action if given explicitely in the actions dict
            sem_action = self.sem_actions.get(production.symbol.name)

        if sem_action:
            if type(sem_action) is list:
                result = sem_action[production.prod_symbol_id](context,
                                                               subresults)
            else:
                result = sem_action(context, subresults)

        else:
            if debug:
                print("\tNo action defined for '{}'. "
                      "Result is a list of subresults."
                      .format(production.symbol.name))
            result = subresults

        if debug:
            print("\tAction result = type:{} value:{}"
                  .format(type(result), repr(result)))

        return result

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

    def default_error_recovery(self, input, position, expected_symbols):
        """The default recovery strategy is to drop char/object at current position
        and try to continue.

        Args:
            input (sequence): Input string/stream of objects.
            position (int): The current position in the input string.
            expected_symbols (list of GrammarSymbol): The symbol that are
                expected at the current location in the current state.

        Returns:
            (Error, new position, new Token or None)

        """
        if self.current_error:
            self.current_error.length = position + 1 \
                                         - self.current_error.position
            return None, position + 1, None
        else:
            error = Error(position, 1,
                          input_str=input,
                          expected_symbols=expected_symbols)
            self.current_error = error
            return error, position + 1, None

    def _call_dynamic_filter(self, action, token, production, subresults,
                             state):
        if (action is SHIFT and not token.symbol.dynamic)\
           or (action is REDUCE and not production.dynamic):
            return True

        if self.debug:
            print("\tCalling filter for action: {}, token={}{}{}".format(
                "SHIFT" if action is SHIFT else "REDUCE", token,
                ", prod={}".format(production) if action is REDUCE else "",
                ", subresults={}".format(subresults)
                if action is REDUCE else ""))

        accepted = self.dynamic_filter(action, token, production, subresults,
                                       state)
        if self.debug:
            if accepted:
                print("\tAction accepted.")
            else:
                print("\tAction rejected.")

        return accepted


class Context:
    pass


class StackNode:
    __slots__ = ['state',
                 'start_position',
                 'end_position',
                 'layout_content',
                 'result']

    def __init__(self, state, start_position, end_position, layout_content,
                 result):
        self.state = state
        self.start_position = start_position
        self.end_position = end_position
        self.layout_content = layout_content
        self.result = result


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

    def __repr__(self):
        return str(self)

    @property
    def dynamic(self):
        if self.action is SHIFT:
            return self.state.symbol.dynamic
        elif self.action is REDUCE:
            return self.prod.dynamic
        else:
            return False


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

    Attributes:
    grammar(Grammar):
    state_id(int):
    symbol(GrammarSymbol):
    items(list of LRItem):
    actions(OrderedDict): Keys are grammar terminal symbols, values are
        lists of Action instances.
    goto(OrderedDict): Keys are grammar non-terminal symbols, values are
        instances of LRState.
    dynamic(set of terminal symbols): If terminal symbol is in set dynamic
        ambiguity strategy callable is called for the terminal symbol
        lookahead.
    finish_flags:

    """
    __slots__ = ['grammar', 'state_id', 'symbol', 'items',
                 'actions', 'gotos', 'dynamic', 'finish_flags',
                 '_per_next_symbol', '_max_prior_per_symbol']

    def __init__(self, grammar, state_id, symbol, items):
        self.grammar = grammar
        self.state_id = state_id
        self.symbol = symbol
        self.items = items if items else []

        self.actions = OrderedDict()
        self.gotos = OrderedDict()
        self.dynamic = set()

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
        s = "\nState %d:%s\n" % (self.state_id, self.symbol)
        for i in self.items:
            s += "\t{}\n".format(i)
        return s

    def __unicode__(self):
        return str(self)

    def print_debug(self):
        print(text(self))


class Node(object):
    """A node of the parse tree."""
    def __init__(self, start_position, end_position, layout_content=None):
        self.start_position = start_position
        self.end_position = end_position
        self.layout_content = layout_content

    def __repr__(self):
        return str(self)

    def __iter__(self):
        return iter([])

    def __reversed__(self):
        return iter([])


class NodeNonTerm(Node):
    __slots__ = ['start_position', 'end_position', 'production', 'children']

    def __init__(self, start_position, end_position, production, children,
                 layout_content=None):
        super(NodeNonTerm, self).__init__(start_position,
                                          end_position,
                                          layout_content=layout_content)
        self.production = production
        self.children = children

    def tree_str(self, depth=0):
        indent = '  ' * depth
        s = '{}[{}]'.format(self.production.symbol, self.start_position)
        if self.children:
            for n in self.children:
                if hasattr(n, 'tree_str'):
                    s += '\n' + indent + n.tree_str(depth+1)
                else:
                    s += '\n' + indent + n.__class__.__name__ \
                         + '(' + str(n) + ')'
        return s

    @property
    def symbol(self):
        return self.production.symbol

    def __str__(self):
        return '<NonTerm(start={}, end={}, sym={})>'\
            .format(self.start_position, self.end_position,
                    self.production.symbol)

    def __iter__(self):
        return iter(self.children)

    def __reversed__(self):
        return reversed(self.children)


class NodeTerm(Node):
    __slots__ = ['start_position', 'end_position', 'symbol', 'value']

    def __init__(self, start_position, end_position, symbol, value,
                 layout_content=None):
        super(NodeTerm, self).__init__(start_position,
                                       end_position,
                                       layout_content=layout_content)
        self.value = value
        self.symbol = symbol

    def tree_str(self, depth=0):
        return '{}[{}, {}]'.format(self.symbol, self.start_position,
                                   self.value)

    def __str__(self):
        return '<Term(start={}, end={}, sym={}, val="{}")>'\
            .format(self.start_position, self.end_position, self.symbol,
                    self.value[:20])

    def __iter__(self):
        return iter([])

    def __reversed__(self):
        return iter([])


class Token(object):
    """
    Token or lexeme matched from the input.
    """
    __slots__ = ['symbol', 'value', 'length']

    def __init__(self, symbol=None, value='', length=None):
        self.symbol = symbol
        self.value = value
        self.length = length if length is not None else len(value)

    def __repr__(self):
        return "<{}({})>".format(text(self.symbol), text(self.value))

    def __len__(self):
        return self.length

    def __bool__(self):
        return True


STOP_token = Token(STOP)
EMPTY_token = Token(EMPTY)
EOF_token = Token(EOF)


def treebuild_shift_action(context, value):
    return NodeTerm(context.start_position, context.end_position,
                    context.symbol, value, context.layout_content)


def treebuild_reduce_action(context, nodes):
    return NodeNonTerm(context.start_position, context.end_position,
                       context.production, nodes, context.layout_content)


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

    if type(input_str) is not str:
        # If we are not parsing string
        return 1, position

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
