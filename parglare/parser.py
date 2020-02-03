# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function
import codecs
import logging
import sys
from copy import copy
from .grammar import EMPTY, STOP
from .tables import LALR, SLR, SHIFT, REDUCE, ACCEPT
from .exceptions import ParseError, ParserInitError, DisambiguationError, \
    DynamicDisambiguationConflict, SRConflicts, RRConflicts, \
    expected_symbols_str
from .common import Location, position_context
from .actions import pass_none
from .termui import prints, h_print, a_print
from parglare import termui

if sys.version < '3':
    text = unicode  # NOQA
else:
    text = str


logger = logging.getLogger(__name__)


class Parser(object):
    """Parser works like a DFA driven by LR tables. For a given grammar LR table
    will be created and cached or loaded from cache if cache is found.
    """
    def __init__(self, grammar, in_layout=False, actions=None,
                 layout_actions=None, debug=False, debug_trace=False,
                 debug_colors=False, debug_layout=False, ws='\n\r\t ',
                 consume_input=True, build_tree=False,
                 call_actions_during_tree_build=False, tables=LALR,
                 return_position=False, prefer_shifts=None,
                 prefer_shifts_over_empty=None, error_recovery=False,
                 dynamic_filter=None, custom_token_recognition=None,
                 lexical_disambiguation=True, force_load_table=False,
                 table=None):
        self.grammar = grammar
        self.in_layout = in_layout

        EMPTY.action = pass_none
        if actions:
            self.grammar._resolve_actions(action_overrides=actions,
                                          fail_on_no_resolve=True)

        self.layout_parser = None
        if self.in_layout:
            start_production = grammar.get_production_id('LAYOUT')
        else:
            start_production = 1
            layout_symbol = grammar.get_symbol('LAYOUT')
            if layout_symbol:
                self.layout_parser = Parser(
                    grammar,
                    in_layout=True,
                    consume_input=False,
                    actions=layout_actions,
                    ws=None, return_position=True,
                    prefer_shifts=True,
                    prefer_shifts_over_empty=True,
                    debug=debug_layout)

        self.ws = ws
        self.return_position = return_position
        self.debug = debug
        self.debug_trace = debug_trace
        self.debug_colors = debug_colors
        termui.colors = debug_colors
        self.debug_layout = debug_layout

        self.consume_input = consume_input
        self.build_tree = build_tree
        self.call_actions_during_tree_build = call_actions_during_tree_build

        self.error_recovery = error_recovery
        self.dynamic_filter = dynamic_filter
        self.custom_token_recognition = custom_token_recognition
        self.lexical_disambiguation = lexical_disambiguation

        if table is None:
            from .closure import LR_0, LR_1
            from .tables import create_load_table

            if tables == SLR:
                itemset_type = LR_0
            else:
                itemset_type = LR_1

            if prefer_shifts is None:
                prefer_shifts = True
            if prefer_shifts_over_empty is None:
                prefer_shifts_over_empty = True

            self.table = create_load_table(
                grammar, itemset_type=itemset_type,
                start_production=start_production,
                prefer_shifts=prefer_shifts,
                prefer_shifts_over_empty=prefer_shifts_over_empty,
                lexical_disambiguation=lexical_disambiguation,
                force_load=force_load_table,
                in_layout=self.in_layout)
        else:
            self.table = table

            # warn about overriden parameters
            for name, value, default in [
                ('tables', tables, LALR),
                ('prefer_shifts', prefer_shifts, None),
                ('prefer_shifts_over_empty', prefer_shifts_over_empty, None),
                ('force_load_table', force_load_table, False),
            ]:
                if value is not default:
                    logger.warn("Precomputed table overrides value of "
                                "parameter %s", name)

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
        if self.in_layout and self.debug_layout:
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

        next_token = self._next_token
        debug = self.debug
        self.file_name = file_name
        self.in_error_recovery = False

        context = self._get_init_context(context, input_str, position,
                                         file_name)
        assert isinstance(context, Context)

        self._init_dynamic_disambiguation(context)
        self.state_stack = state_stack = [StackNode(context, None)]

        while True:
            cur_state = state_stack[-1].context.state
            if debug:
                a_print("Current state:", str(cur_state.state_id),
                        new_line=True)

            if context.token_ahead is None:
                if not self.in_layout:
                    self._skipws(context)
                    if self.debug:
                        h_print("Layout content:",
                                "'{}'".format(context.layout_content),
                                level=1)

                context.token_ahead = next_token(context)

            if debug:
                h_print("Context:", position_context(context), level=1)
                h_print("Tokens expected:",
                        expected_symbols_str(cur_state.actions.keys()),
                        level=1)
                h_print("Token ahead:", context.token_ahead, level=1)

            actions = cur_state.actions.get(context.token_ahead.symbol)
            if not actions and not self.consume_input:
                # If we don't have any action for the current token ahead
                # see if we can finish without consuming the whole input.
                actions = cur_state.actions.get(STOP)

            if not actions:

                symbols_expected = list(cur_state.actions.keys())
                tokens_ahead = self._get_all_possible_tokens_ahead(context)
                if not self.in_error_recovery:
                    error = self._create_error(
                        context, symbols_expected,
                        tokens_ahead,
                        symbols_before=[cur_state.symbol])
                else:
                    error = self.errors[-1]

                if self.error_recovery:
                    if self._do_recovery(context, error):
                        self.in_error_recovery = True
                        continue

                raise error

            # Dynamic disambiguation
            if self.dynamic_filter:
                actions = self._dynamic_disambiguation(context, actions)

                # If after dynamic disambiguation we still have at least one
                # shift and non-empty reduction or multiple non-empty
                # reductions raise exception.
                if len([a for a in actions
                        if (a.action is SHIFT)
                        or ((a.action is REDUCE) and len(a.prod.rhs))]) > 1:
                    raise DynamicDisambiguationConflict(context, actions)

            # If dynamic disambiguation is disabled either globaly by not
            # giving disambiguation function or localy by not marking
            # any production dynamic for this state take the first action.
            # First action is either SHIFT while there might be empty
            # reductions, or it is the only reduction.
            # Otherwise, parser construction should raise an error.
            act = actions[0]

            if act.action is SHIFT:
                cur_state = act.state

                if debug:
                    a_print("Shift:",
                            "{} \"{}\""
                            .format(cur_state.state_id,
                                    context.token_ahead.value)
                            + " at position " +
                            str(pos_to_line_col(context.input_str,
                                                context.position)), level=1)

                new_position = context.position \
                    + len(context.token_ahead.value)
                context = Context(
                    state=act.state,
                    start_position=context.position,
                    end_position=new_position,
                    token=context.token_ahead,
                    layout_content=context.layout_content_ahead,
                    position=new_position,
                    context=context)

                result = self._call_shift_action(context)
                state_stack.append(StackNode(context, result))

                self.in_error_recovery = False

            elif act.action is REDUCE:
                # if this is EMPTY reduction try to take another if
                # exists.
                if len(act.prod.rhs) == 0:
                    if len(actions) > 1:
                        act = actions[1]
                context.production = production = act.prod

                if debug:
                    a_print("Reducing", "by prod '{}'.".format(production),
                            level=1)

                r_length = len(production.rhs)
                top_stack_context = state_stack[-1].context
                if r_length:
                    start_reduction_context = state_stack[-r_length].context
                    subresults = [x.result for x in state_stack[-r_length:]]
                    del state_stack[-r_length:]
                    cur_state = state_stack[-1].context.state.gotos[
                        production.symbol]
                    context = Context(
                        state=cur_state,
                        start_position=start_reduction_context.start_position,
                        end_position=top_stack_context.end_position,
                        position=top_stack_context.position,
                        production=production,
                        token_ahead=top_stack_context.token_ahead,
                        layout_content=start_reduction_context.layout_content,
                        layout_content_ahead=top_stack_context.layout_content_ahead,  # noqa
                        context=context)
                else:
                    subresults = []
                    cur_state = cur_state.gotos[production.symbol]
                    context = Context(
                        state=cur_state,
                        start_position=context.end_position,
                        end_position=context.end_position,
                        position=context.position,
                        production=production,
                        token_ahead=top_stack_context.token_ahead,
                        layout_content='',
                        layout_content_ahead=top_stack_context.layout_content_ahead,  # noqa
                        context=context)

                # Calling reduce action
                result = self._call_reduce_action(context, subresults)
                state_stack.append(StackNode(context, result))

            elif act.action is ACCEPT:
                if debug:
                    a_print("SUCCESS!!!")
                assert len(state_stack) == 2
                if self.return_position:
                    return state_stack[1].result, context.position
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
            context.production = None
            context.token = None
            context.layout_content = node.layout_content

        def inner_call_actions(node):
            sem_action = node.symbol.action
            if isinstance(node, NodeTerm):
                if sem_action:
                    set_context(context, node)
                    try:
                        result = sem_action(context, node.value,
                                            *node.additional_data)
                    except TypeError as e:
                        raise TypeError('{}: terminal={} action={} params={}'
                                        .format(
                                            str(e),
                                            node.symbol.name,
                                            repr(sem_action),
                                            (context, node.value,
                                             node.additional_data))) from e
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

    def _get_init_context(self, context, input_str, position, file_name):

        context = Context() if not context else context

        context.state = self.table.states[0]
        context.input_str = input_str
        if not hasattr(context, 'file_name') or context.file_name is None:
            context.file_name = file_name
        context.parser = self
        context.position = context.start_position = \
            context.end_position = position
        context.layout_content = ''

        return context

    def _skipws(self, context):

        in_len = len(context.input_str)
        context.layout_content_ahead = ''

        if self.layout_parser:
            _, pos = self.layout_parser.parse(
                context.input_str, context.position, context=copy(context))
            if pos > context.position:
                context.layout_content_ahead = \
                    context.input_str[context.position:pos]
                context.position = pos
        elif self.ws:
            old_pos = context.position
            try:
                while context.position < in_len \
                      and context.input_str[context.position] in self.ws:
                    context.position += 1
            except TypeError:
                raise ParserInitError(
                    "For parsing non-textual content please "
                    "set `ws` to `None`.")
            context.layout_content_ahead = \
                context.input_str[old_pos:context.position]

        if self.debug:
            content = context.layout_content_ahead
            if type(context.layout_content_ahead) is text:
                content = content.replace("\n", "\\n")
            h_print("Skipping whitespaces:",
                    "'{}'".format(content), level=1)
            h_print("New position:", pos_to_line_col(context.input_str,
                                                     context.position),
                    level=1)

    def _next_token(self, context):
        tokens = self._next_tokens(context)
        if not tokens:
            # We have to return something.
            # Returning EMPTY token is not a lie (EMPTY can always be matched)
            # and will cause proper parse error to be raised.
            return EMPTY_token
        elif len(tokens) == 1:
            return tokens[0]
        else:
            raise DisambiguationError(Location(context), tokens)

    def _next_tokens(self, context):
        """
        For the current position in the input stream and actions in the current
        state find next tokens. This function must return only tokens that
        are relevant to specified context - ie it mustn't return a token
        if it's not expected by any action in given state.
        """
        state = context.state
        input_str = context.input_str
        position = context.position
        actions = state.actions
        in_len = len(input_str)
        tokens = []

        # add special tokens (EMPTY and STOP) if they are applicable
        if EMPTY in actions:
            tokens.append(EMPTY_token)
        if STOP in actions:
            if not self.consume_input \
               or (self.consume_input and position == in_len):
                tokens.append(STOP_token)

        if position < in_len:
            # Get tokens by trying recognizers - but only if we are not at
            # the end, because token cannot be empty
            if self.custom_token_recognition:
                def get_tokens():
                    return self._token_recognition(context)

                custom_tokens = self.custom_token_recognition(
                    context, get_tokens,
                )
                if custom_tokens is not None:
                    tokens.extend(custom_tokens)
            else:
                tokens.extend(self._token_recognition(context))

        # do lexical disambiguation if it is enabled
        if self.lexical_disambiguation:
            tokens = self._lexical_disambiguation(context, tokens)

        return tokens

    def _token_recognition(self, context):
        input_str = context.input_str
        actions = context.state.actions
        position = context.position
        finish_flags = context.state.finish_flags

        tokens = []
        last_prior = -1
        for idx, symbol in enumerate(actions):
            if symbol.prior < last_prior and tokens:
                break
            last_prior = symbol.prior
            try:
                tok = symbol.recognizer(input_str, position)
            except TypeError:
                try:
                    tok = symbol.recognizer(context, input_str, position)
                except TypeError as e:
                    raise TypeError(
                        'In recognizer for "{}": {}'.format(symbol, e)) from e

            additional_data = ()
            if type(tok) is tuple:
                tok, *additional_data = tok
            if tok:
                tokens.append(Token(symbol, tok, additional_data))
                if finish_flags[idx]:
                    break
        return tokens

    def _get_all_possible_tokens_ahead(self, context):
        """
        Check what is ahead no matter the current state.
        Just check with all recognizers available.
        """
        tokens = []
        if context.position < len(context.input_str):
            for terminal in self.grammar.terminals.values():
                try:
                    tok = terminal.recognizer(context.input_str,
                                              context.position)
                except TypeError:
                    tok = terminal.recognizer(context, context.input_str,
                                              context.position)
                additional_data = ()
                if type(tok) is tuple:
                    tok, *additional_data = tok
                if tok:
                    tokens.append(Token(terminal, tok, additional_data))
        return tokens

    def _init_dynamic_disambiguation(self, context):
        if self.dynamic_filter:
            if self.debug:
                prints("\tInitializing dynamic disambiguation.")
            self.dynamic_filter(context, None, None)

    def _dynamic_disambiguation(self, context, actions):

        dyn_actions = []
        for a in actions:
            if a.action is SHIFT:
                if self._call_dynamic_filter(context, SHIFT, None):
                    dyn_actions.append(a)
            elif a.action is REDUCE:
                r_len = len(a.prod.rhs)
                if r_len:
                    subresults = [x.result
                                  for x in self.state_stack[-r_len:]]
                else:
                    subresults = []
                context.production = a.prod
                if self._call_dynamic_filter(context, REDUCE, subresults):
                    dyn_actions.append(a)
            else:
                dyn_actions.append(a)
        return dyn_actions

    def _call_dynamic_filter(self, context, action, subresults):
        if (action is SHIFT and not context.token_ahead.symbol.dynamic)\
           or (action is REDUCE and not context.production.dynamic):
            return True

        if self.debug:
            h_print("Calling filter for action:",
                    " {}, token={}{}{}"
                    .format(
                        "SHIFT" if action is SHIFT else "REDUCE",
                        context.token,
                        ", prod={}".format(context.production)
                        if action is REDUCE else "",
                        ", subresults={}".format(subresults)
                        if action is REDUCE else ""), level=2)

        accepted = self.dynamic_filter(context, action, subresults)
        if self.debug:
            if accepted:
                a_print("Action accepted.", level=2)
            else:
                a_print("Action rejected.", level=2)

        return accepted

    def _call_shift_action(self, context):
        """
        Calls registered shift action for the given grammar symbol.
        """
        debug = self.debug
        token = context.token
        sem_action = token.symbol.action

        if self.build_tree:
            # call action for building tree node if tree building is enabled
            if debug:
                h_print("Building terminal node",
                        "'{}'.".format(token.symbol.name), level=2)

            # If both build_tree and call_actions_during_build are set to
            # True, semantic actions will be call but their result will be
            # discarded. For more info check following issue:
            # https://github.com/igordejanovic/parglare/issues/44
            if self.call_actions_during_tree_build and sem_action:
                sem_action(context, token.value, *token.additional_data)

            return treebuild_shift_action(context)

        if sem_action:
            result = sem_action(context, token.value, *token.additional_data)

        else:
            if debug:
                h_print("No action defined",
                        "for '{}'. "
                        "Result is matched string.".format(token.symbol.name),
                        level=1)
            result = token.value

        if debug:
            h_print("Action result = ",
                    "type:{} value:{}"
                    .format(type(result), repr(result)), level=1)

        return result

    def _call_reduce_action(self, context, subresults):
        """
        Calls registered reduce action for the given grammar symbol.
        """
        debug = self.debug
        result = None
        bt_result = None
        production = context.production

        if self.build_tree:
            # call action for building tree node if enabled.
            if debug:
                h_print("Building non-terminal node",
                        "'{}'.".format(production.symbol.name), level=2)

            bt_result = treebuild_reduce_action(context, nodes=subresults)
            if not self.call_actions_during_tree_build:
                return bt_result

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

        # If build_tree is set to True, discard the result of the semantic
        # action, and return the result of treebuild_reduce_action.
        return bt_result if bt_result is not None else result

    def _lexical_disambiguation(self, context, tokens):
        """
        For the given list of matched tokens apply disambiguation strategy.

        Args:
        tokens (list of Token)
        """

        if self.debug:
            h_print("Lexical disambiguation.",
                    " Tokens: {}".format([x for x in tokens]), level=1)

        if len(tokens) <= 1:
            return tokens

        # prefer STOP over EMPTY
        if STOP_token in tokens:
            tokens = [t for t in tokens if t != EMPTY_token]

        # Longest-match strategy.
        max_len = max((len(x.value) for x in tokens))
        tokens = [x for x in tokens if len(x.value) == max_len]
        if self.debug:
            h_print("Disambiguation by longest-match strategy.",
                    "Tokens: {}".format([x for x in tokens]), level=1)
        if len(tokens) == 1:
            return tokens

        # try to find preferred token.
        pref_tokens = [x for x in tokens if x.symbol.prefer]
        if pref_tokens:
            if self.debug:
                h_print("Preferring tokens {}.".format(pref_tokens),
                        level=1)
            return pref_tokens

        return tokens

    def _do_recovery(self, context, error):

        debug = self.debug
        if debug:
            a_print("**Recovery initiated.**")

        if type(self.error_recovery) is bool:
            # Default recovery
            if debug:
                prints("\tDoing default error recovery.")
            token, position = self.default_error_recovery(context)
        else:
            # Custom recovery provided during parser construction
            if debug:
                prints("\tDoing custom error recovery.")
            token, position = self.error_recovery(context, error)

        # The recovery may either decide to skip erroneous part of
        # the input and resume at the place that can continue or it
        # might decide to fill in missing tokens.
        if position:
            last_error = self.errors[-1]
            last_error.location.end_position = position
            context.position = position
            if debug:
                h_print("Advancing position to ",
                        pos_to_line_col(context.input_str, position),
                        level=1)

        context.token_ahead = token
        if token and debug:
            h_print("Introducing token {}", repr(token), level=1)

        return bool(token or position)

    def default_error_recovery(self, context):
        """The default recovery strategy is to drop char/object at current position
        and try to continue.

        Args:
            context(Context): The parsing context

        Returns:
            (None for new Token, new position)

        """
        return None, context.position + 1 \
            if context.position < len(context.input_str) else None

    def _create_error(self, context, symbols_expected, tokens_ahead=None,
                      symbols_before=None, last_heads=None, store=True):
        context = copy(context)
        context.start_position = context.position
        context.end_position = context.position
        error = ParseError(Location(context=context),
                           symbols_expected,
                           tokens_ahead,
                           symbols_before=symbols_before,
                           last_heads=last_heads,
                           grammar=self.grammar)

        if self.debug:
            a_print("Error: ", error, level=1)

        if store:
            self.errors.append(error)

        return error


class Context:
    """
    Args:
        state(LRState):
        file_name(str):
        position(int):
        start_position, end_position(int):
        layout_content(str): Layout content preceeding current token.
        layout_content_ahead(str): Layout content preceeding token_ahead.
        token(Token): Token for shift operation.
        token_ahead(Token): Token recognized ahead at position in given
             state.
        extra(anything): Used for additional state maintained by the user.
             If not given empty dict is used.
    """

    __local = ['state',
               'position',
               'start_position',
               'end_position',
               'token',
               'token_ahead',
               'production',
               'layout_content',
               'layout_content_ahead',
               'node']
    __t = ['file_name',
           'input_str',
           'parser',
           'extra']

    __slots__ = __local + __t

    def __init__(self, state=None, position=None, start_position=None,
                 end_position=None, token=None, token_ahead=None,
                 production=None, layout_content=None,
                 layout_content_ahead=None, node=None, file_name=None,
                 input_str=None, parser=None, extra=None, context=None):
        self.state = state
        self.position = position
        self.start_position = start_position
        self.end_position = end_position
        self.token = token
        self.token_ahead = token_ahead
        self.production = production
        self.layout_content = layout_content
        self.layout_content_ahead = layout_content_ahead
        self.node = node
        if context:
            self.extra = context.extra
            self.file_name = context.file_name
            self.input_str = context.input_str
            self.parser = context.parser
        else:
            self.extra = extra if extra is not None else {}
            self.file_name = file_name
            self.input_str = input_str
            self.parser = parser

    @property
    def symbol(self):
        if self.token is not None:
            return self.token.symbol
        elif self.production is not None:
            return self.production.symbol
        elif self.node is not None:
            return self.node.symbol

    def __str__(self):
        if self.symbol:
            return str(self.symbol)
        elif self.token:
            return str(self.token)
        else:
            return str(self.production)


class StackNode:
    __slots__ = ['context', 'result']

    def __init__(self, context, result):
        self.context = context
        self.result = result

    def __repr__(self):
        return "<StackNode({}, pos=({}-{}))>"\
            .format(repr(self.context.state),
                    self.context.start_position, self.context.end_position)


class Node(object):
    """A node of the parse tree."""

    __slots__ = ['start_position', 'end_position', 'layout_content']

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
    __slots__ = ['production', 'children']

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
    __slots__ = ['token']

    def __init__(self, start_position, end_position, token,
                 layout_content=None):
        super(NodeTerm, self).__init__(start_position,
                                       end_position,
                                       layout_content=layout_content)
        self.token = token

    @property
    def symbol(self):
        return self.token.symbol

    @property
    def value(self):
        return self.token.value

    @property
    def additional_data(self):
        return self.token.additional_data

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
    __slots__ = ['symbol', 'value', 'additional_data', 'length']

    def __init__(self, symbol=None, value='', additional_data=(), length=None):
        self.symbol = symbol
        self.value = value
        self.additional_data = additional_data
        self.length = length if length is not None else len(value)

    def __repr__(self):
        return "<{}({})>".format(text(self.symbol), text(self.value))

    def __len__(self):
        return self.length

    def __bool__(self):
        return True


STOP_token = Token(STOP)
EMPTY_token = Token(EMPTY)


def treebuild_shift_action(context):
    return NodeTerm(context.start_position, context.end_position,
                    context.token, context.layout_content)


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

    if position is None:
        return None, None

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
