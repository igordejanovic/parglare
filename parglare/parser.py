# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function
import codecs
import sys
from .grammar import EMPTY, EOF, STOP
from .tables import LALR, SLR, SHIFT, REDUCE, ACCEPT
from .errors import Error, expected_symbols_str
from .exceptions import ParseError, ParserInitError, DisambiguationError, \
    DynamicDisambiguationConflict, disambiguation_error, expected_message, \
    SRConflicts, RRConflicts
from .common import Location, position_context
from .actions import pass_none
from .termui import prints, h_print, a_print
from parglare import termui

if sys.version < '3':
    text = unicode  # NOQA
else:
    text = str


class Parser(object):
    """Parser works like a DFA driven by LR tables. For a given grammar LR table
    will be created and cached or loaded from cache if cache is found.
    """
    def __init__(self, grammar, start_production=1, actions=None,
                 layout_actions=None, debug=False, debug_trace=False,
                 debug_colors=False, debug_layout=False, ws='\n\r\t ',
                 build_tree=False, tables=LALR, layout=False, position=False,
                 prefer_shifts=True, prefer_shifts_over_empty=True,
                 error_recovery=False, dynamic_filter=None,
                 custom_lexical_disambiguation=None):
        self.grammar = grammar
        self.start_production = start_production
        EMPTY.action = pass_none
        EOF.action = pass_none
        if actions:
            self.grammar._resolve_actions(action_overrides=actions,
                                          fail_on_no_resolve=True)

        self.layout_parser = None
        if not layout:
            layout_prod = grammar.get_production_id('LAYOUT')
            if layout_prod:
                self.layout_parser = Parser(
                    grammar,
                    start_production=layout_prod,
                    actions=layout_actions,
                    ws=None, layout=True,
                    position=True,
                    prefer_shifts=True,
                    prefer_shifts_over_empty=True,
                    debug=debug_layout)

        self.layout = layout
        self.ws = ws
        self.position = position
        self.debug = debug
        self.debug_trace = debug_trace
        self.debug_colors = debug_colors
        termui.colors = debug_colors
        self.debug_layout = debug_layout

        self.build_tree = build_tree

        self.error_recovery = error_recovery
        self.dynamic_filter = dynamic_filter
        self.custom_lexical_disambiguation = custom_lexical_disambiguation

        from .closure import LR_0, LR_1
        from .tables import create_table
        if tables == SLR:
            itemset_type = LR_0
        else:
            itemset_type = LR_1
        self.table = create_table(
            grammar, itemset_type=itemset_type,
            start_production=start_production, prefer_shifts=prefer_shifts,
            prefer_shifts_over_empty=prefer_shifts_over_empty)

        self._check_parser()
        if debug:
            self.print_debug()

    def _check_parser(self):
        if self.table.sr_conflicts:
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
            a_print('*** LAYOUT parser ***', new_line=True)
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
            a_print("*** PARSING STARTED", new_line=True)

        self.errors = []
        self.current_error = None

        if self.dynamic_filter:
            if self.debug:
                prints("\tInitializing dynamic disambiguation.")
            self.dynamic_filter(None, None, None, None, None)

        state_stack = [StackNode(self.table.states[0], position, 0, None,
                                 None)]
        context = Context() if not context else context
        context.input_str = input_str
        if not hasattr(context, 'file_name') or context.file_name is None:
            context.file_name = file_name

        next_token = self._next_token
        debug = self.debug
        layout_content = ''

        new_token = True
        ntok = Token()

        while True:
            cur_state = state_stack[-1].state
            if debug:
                a_print("Current state:", str(cur_state.state_id),
                        new_line=True)

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

                    if not self.layout:
                        position, layout_content = self._skipws(context,
                                                                input_str,
                                                                position)
                        if self.debug:
                            h_print("Layout content:",
                                    "'{}'".format(layout_content), level=1)

                    ntok = next_token(cur_state, input_str, position)

                except DisambiguationError as e:
                    raise ParseError(
                        location=Location(file_name=file_name,
                                          input_str=input_str,
                                          start_position=position),
                        message=disambiguation_error(e.tokens))

            context.parser = self
            context.start_position = position
            context.end_position = position + len(ntok.value)
            context.layout_content = layout_content

            if debug:
                h_print("Context:",
                        position_context(input_str, position), level=1)
                h_print("Tokens expected:",
                        expected_symbols_str(actions.keys()), level=1)
                h_print("Token ahead:", ntok, level=1)

            acts = actions.get(ntok.symbol)

            if not acts:

                if self.error_recovery:
                    # If we are past end of input error recovery can't be
                    # successful and the only thing we can do is to throw
                    # ParserError
                    if position > len(input_str):
                        e = self.current_error
                        raise ParseError(Location(file_name=file_name,
                                                  input_str=input_str,
                                                  start_position=e.position),
                                         expected_message(actions.keys()))
                    if debug:
                        a_print("**Error found. Recovery initiated.**")

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
                            a_print("Error: ", error, level=1)
                        self.errors.append(error)

                    if not ntok:
                        # If token is not created we are just droping current
                        # input and advancing position. Thus, stay in the same
                        # state and try to continue.
                        if debug:
                            h_print("Continuing at position ",
                                    pos_to_line_col(input_str, position),
                                    level=1)

                        new_token = True
                        continue

                    else:
                        acts = actions.get(ntok.symbol)

            if not acts:
                raise ParseError(Location(file_name=file_name,
                                          input_str=input_str,
                                          start_position=position),
                                 expected_message(actions.keys()))

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
                    a_print("Shift:",
                            "{} \"{}\"" .format(state.state_id,
                                                ntok.value) + " at position " +
                            str(pos_to_line_col(input_str,
                                                position)), level=1)

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
                    a_print("Reducing", "by prod '{}'.".format(production),
                            level=1)

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
                    a_print("SUCCESS!!!")
                assert len(state_stack) == 2
                if self.position:
                    return state_stack[1].result, position
                else:
                    return state_stack[1].result

    def call_actions(self, node, context=None):
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
            if isinstance(node, NodeTerm):
                if sem_action:
                    set_context(context, node)
                    result = sem_action(context, node.value)
                else:
                    result = node.value
            else:
                subresults = []
                # Recursive right to left, bottom up. Simulate LR
                # reductions.
                for n in reversed(node):
                    subresults.append(inner_call_actions(n))
                subresults.reverse()

                if sem_action:
                    set_context(context, node)
                    context.production = node.production
                    assignments = node.production.assignments
                    if assignments:
                        assgn_results = {}
                        for a in assignments.values():
                            if a.op == '=':
                                assgn_results[a.name] = subresults[a.index]
                            else:
                                assgn_results[a.name] = \
                                    bool(subresults[a.index])
                    if type(sem_action) is list:
                        if assignments:
                            result = \
                                sem_action[
                                    node.production.prod_symbol_id](
                                        context, subresults, **assgn_results)
                        else:
                            result = \
                                sem_action[
                                    node.production.prod_symbol_id](context,
                                                                    subresults)
                    else:
                        if assignments:
                            result = sem_action(context, subresults,
                                                **assgn_results)
                        else:
                            result = sem_action(context, subresults)
                else:
                    if len(subresults) == 1:
                        # Unpack if single subresult
                        result = subresults[0]
                    else:
                        result = subresults

            return result

        return inner_call_actions(node)

    def _skipws(self, context, input_str, position):
        in_len = len(input_str)
        layout_content = ''
        if self.layout_parser:
            _, pos = self.layout_parser.parse(
                input_str, position, context=context)
            if pos > position:
                layout_content = input_str[position:pos]
            position = pos
        elif self.ws:
            old_pos = position
            try:
                while position < in_len and input_str[position] in self.ws:
                    position += 1
            except TypeError:
                raise ParserInitError(
                    "For parsing non-textual content please "
                    "set `ws` to `None`.")
            layout_content = input_str[old_pos:position]

        if self.debug:
            content = layout_content.replace("\n", "\\n") \
                      if type(layout_content) is text else layout_content
            h_print("Skipping whitespaces:",
                    "'{}'".format(content), level=1)
            h_print("New position:",
                    pos_to_line_col(input_str, position), level=1)

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
            # Execute EOF action at end of input only if EMPTY and
            # STOP terminals are not in actions as this might call
            # for reduction.
            ntok = EOF_token
        else:
            tokens = []
            if position < in_len:
                if self.custom_lexical_disambiguation:
                    symbols = actions.keys()

                    def get_tokens():
                        return self._token_recognition(input_str,
                                                       position, actions,
                                                       finish_flags)

                    tokens = self.custom_lexical_disambiguation(
                        symbols, input_str, position, get_tokens)
                else:
                    tokens = self._token_recognition(input_str, position,
                                                     actions, finish_flags)
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

    def _token_recognition(self, input_str, position, actions, finish_flags):
        tokens = []
        last_prior = -1
        for idx, symbol in enumerate(actions):
            if symbol.prior < last_prior and tokens:
                break
            last_prior = symbol.prior
            tok = symbol.recognizer(input_str, position)
            if tok:
                tokens.append(Token(symbol, tok))
                if finish_flags[idx]:
                    break
        return tokens

    def _call_shift_action(self, symbol, matched_str, context):
        """
        Calls registered shift action for the given grammar symbol.
        """
        debug = self.debug

        if self.build_tree:
            # call action for building tree node if tree building is enabled
            if debug:
                h_print("Building terminal node",
                        "'{}'.".format(symbol.name), level=2)
            return treebuild_shift_action(context, matched_str)

        sem_action = symbol.action
        if sem_action:
            result = sem_action(context, matched_str)

        else:
            if debug:
                h_print("No action defined",
                        "for '{}'. "
                        "Result is matched string.".format(symbol.name),
                        level=1)
            result = matched_str

        if debug:
            h_print("Action result = ",
                    "type:{} value:{}"
                    .format(type(result), repr(result)), level=1)

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
                h_print("Building non-terminal node",
                        "'{}'.".format(production.symbol.name), level=2)
            return treebuild_reduce_action(context, nodes=subresults)

        sem_action = production.symbol.action
        if sem_action:
            assignments = production.assignments
            if assignments:
                assgn_results = {}
                for a in assignments.values():
                    if a.op == '=':
                        assgn_results[a.name] = subresults[a.index]
                    else:
                        assgn_results[a.name] = bool(subresults[a.index])

            if type(sem_action) is list:
                if assignments:
                    result = sem_action[production.prod_symbol_id](
                        context, subresults, **assgn_results)
                else:
                    result = sem_action[production.prod_symbol_id](context,
                                                                   subresults)
            else:
                if assignments:
                    result = sem_action(context, subresults, **assgn_results)
                else:
                    result = sem_action(context, subresults)

        else:
            if debug:
                h_print("No action defined",
                        " for '{}'.".format(production.symbol.name), level=1)
            if len(subresults) == 1:
                if debug:
                    h_print("Unpacking a single subresult.", level=1)
                result = subresults[0]
            else:
                if debug:
                    h_print("Result is a list of subresults.", level=1)
                result = subresults

        if debug:
            h_print("Action result =",
                    "type:{} value:{}"
                    .format(type(result), repr(result)), level=1)

        return result

    def _lexical_disambiguation(self, tokens):
        """
        For the given list of matched tokens apply disambiguation strategy.

        Args:
        tokens (list of Token)
        """

        if self.debug:
            h_print("Lexical disambiguation.",
                    " Tokens: {}".format([x for x in tokens]), level=1)

        # Longest-match strategy.
        max_len = max((len(x.value) for x in tokens))
        tokens = [x for x in tokens if len(x.value) == max_len]
        if self.debug:
            h_print("Disambiguation by longest-match strategy.",
                    "Tokens: {}".format([x for x in tokens]), level=1)
        if len(tokens) == 1:
            return tokens[0]
        else:
            # Finally try to find preferred token.
            pref_tokens = [x for x in tokens if x.symbol.prefer]
            if len(pref_tokens) == 1:
                if self.debug:
                    h_print("Preferring token {}.".format(pref_tokens[0]),
                            level=1)
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
            h_print("Calling filter for action:",
                    " {}, token={}{}{}"
                    .format(
                        "SHIFT" if action is SHIFT else "REDUCE", token,
                        ", prod={}".format(production)
                        if action is REDUCE else "",
                        ", subresults={}".format(subresults)
                        if action is REDUCE else ""), level=2)

        accepted = self.dynamic_filter(action, token, production, subresults,
                                       state)
        if self.debug:
            if accepted:
                a_print("Action accepted.", level=2)
            else:
                a_print("Action rejected.", level=2)

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
        s = '{}[{}->{}]'.format(self.production.symbol,
                                self.start_position,
                                self.end_position)
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
        return '{}[{}->{}, "{}"]'.format(self.symbol,
                                         self.start_position,
                                         self.end_position,
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
    if nodes:
        return NodeNonTerm(nodes[0].start_position, nodes[-1].end_position,
                           context.production, nodes, context.layout_content)
    else:
        return NodeNonTerm(context.start_position, context.end_position,
                           context.production, nodes, context.layout_content)


def pos_to_line_col(input_str, position):
    """
    Returns position in the (line,column) form.
    """

    if type(input_str) is not text:
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
