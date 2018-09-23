# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
import codecs
from itertools import chain, takewhile
from copy import copy
from parglare import Parser
from parglare import termui as t
from .exceptions import DisambiguationError, ParseError
from .parser import SHIFT, REDUCE, ACCEPT, pos_to_line_col, STOP, Context, \
    Token
from .common import Location, position_context
from .common import replace_newlines as _
from .tables import LALR
from .export import dot_escape
from .termui import prints, h_print, a_print


def no_colors(f):
    """
    Decorator for trace methods to prevent ANSI COLOR codes apearing in
    the trace dot output.
    """
    def nc_f(*args, **kwargs):
        self = args[0]
        t.colors = False
        r = f(*args, **kwargs)
        t.colors = self.debug_colors
        return r
    return nc_f


class GLRParser(Parser):
    """
    A Tomita-style GLR parser.
    """
    def __init__(self, grammar, start_production=None, actions=None,
                 layout_actions=None, debug=False, debug_trace=False,
                 debug_colors=False, debug_layout=False, ws='\n\r\t ',
                 build_tree=False, call_actions_during_tree_build=False,
                 tables=LALR, return_position=False,
                 prefer_shifts=None, prefer_shifts_over_empty=None,
                 error_recovery=False, dynamic_filter=None,
                 custom_token_recognition=None, force_load_table=False):

        # The default for GLR is not to use any strategy preferring shifts
        # over reduce thus investigating all possibilitites.
        prefer_shifts = False \
            if prefer_shifts is None else prefer_shifts
        prefer_shifts_over_empty = False \
            if prefer_shifts_over_empty is None else prefer_shifts_over_empty

        super(GLRParser, self).__init__(
            grammar=grammar, start_production=start_production,
            actions=actions, layout_actions=layout_actions,
            debug=debug, debug_trace=debug_trace,
            debug_colors=debug_colors, debug_layout=debug_layout, ws=ws,
            build_tree=build_tree,
            call_actions_during_tree_build=call_actions_during_tree_build,
            tables=tables, return_position=return_position,
            prefer_shifts=prefer_shifts,
            prefer_shifts_over_empty=prefer_shifts_over_empty,
            error_recovery=error_recovery, dynamic_filter=dynamic_filter,
            custom_token_recognition=custom_token_recognition,
            force_load_table=force_load_table)

    def _check_parser(self):
        """
        Conflicts in table are allowed with GLR.
        """
        pass

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
            a_print("*** PARSING STARTED\n")
            self.debug_step = 0
            if self.debug_trace:
                self.dot_trace = ""

        self.errors = []
        self.in_error_recovery = None
        self.in_error_reporting = False
        self.last_position = 0
        self.expected = set()
        self.empty_reductions_results = {}
        self.file_name = file_name

        self.context = context = self._get_init_context(context, input_str,
                                                        position, file_name)
        assert isinstance(context, Context)

        self._init_dynamic_disambiguation(context)
        self._skipws(context)

        # We start with a single parser head in state 0.
        start_head = GSSNode(context, number_of_trees=1)
        self.heads_for_reduce = [start_head]
        self.heads_for_shift = []
        self.finish_head = None

        if self.debug and self.debug_trace:
            self._trace_head(start_head,
                             str(start_head.context.state.state_id))

        # The main loop
        while self.heads_for_reduce:

            self.last_heads_for_reduce = list(self.heads_for_reduce)

            self._do_reductions()
            if self.heads_for_shift:
                self._do_shifts()

            # If after shifting we don't have any heads for reduce and we
            # haven't found any final parse do error reporting.
            if not self.heads_for_reduce and not self.finish_head:
                self.in_error_reporting = True
                try:
                    if self.debug:
                        a_print("*** ENTERING ERROR REPORTING MODE.",
                                new_line=True)

                    self._setup_error_reporting()
                    self._do_reductions()
                finally:
                    self.in_error_reporting = False
                    if self.debug:
                        a_print("*** LEAVING ERROR REPORTING MODE.",
                                new_line=True)
                        h_print("Tokens expected:", self.expected, level=1)
                        h_print("Tokens found:", self.tokens_ahead, level=1)

            # After error reporing do error recovery if enabled.
            if self.error_recovery:
                if not self.heads_for_reduce and not self.finish_head:
                    if self.heads_for_recovery:
                        if not self.in_error_recovery:
                            context = self.heads_for_recovery[0].context
                            error = self._create_error(
                                context, self.expected,
                                self.tokens_ahead,
                                list({h.context.state.symbol
                                      for h in self.last_heads_for_reduce}))
                        else:
                            error = self.errors[-1]
                        if self._do_recovery(error):
                            self.in_error_recovery = True
                            continue
                else:
                    # Get out from error recovery mode.
                    self.in_error_recovery = False
                    # Report dying heads
                    if self.debug:
                        for h in self.heads_for_recovery:
                            a_print("{}. Killing head:"
                                    .format(self.debug_step), h,
                                    level=1)
                            if self.debug_trace:
                                self._trace_step_kill(h)
                                self.debug_step += 1

        if not self.finish_head:
            if self.debug and self.debug_trace:
                self._export_dot_trace()
            context = self.context
            context.start_position = context.end_position = context.position
            raise ParseError(Location(context=context),
                             self.expected, self.tokens_ahead,
                             list({h.context.state.symbol
                                   for h in self.last_heads_for_reduce}))

        results = [x[1] for x in self.finish_head.parents]
        if self.debug:
            a_print("*** {} sucessful parse(s).".format(len(results)))
            if self.debug_trace:
                self._export_dot_trace()

        return results

    def _do_reductions(self):
        """
        Reduces active heads until no more heads can be reduced.
        """
        debug = self.debug
        if debug:
            a_print("**REDUCING HEADS", new_line=True)
            self._debug_active_heads(self.heads_for_reduce)

        next_tokens = self._next_tokens
        reduce = self._reduce

        # Reductions
        heads_for_reduce = self.heads_for_reduce
        self.heads_for_shift = []

        # For automata loop detection
        self.reducing_heads = []

        if self.error_recovery and not self.in_error_reporting:
            self.heads_for_recovery = []

        while heads_for_reduce:
            head = heads_for_reduce.pop()
            self.reducing_heads.append(head)
            if debug:
                a_print("Reducing head: ", str(head), new_line=True)

            self.context = context = head.context
            position = context.position
            actions = context.state.actions
            token = context.token_ahead

            if token is None:
                if debug:
                    h_print("Finding lookaheads.", level=1)

                self._skipws(context)
                if position > self.last_position:
                    self.last_position = position
                    self.expected = set()

                if debug:
                    self._debug_context(context, token,
                                        expected_symbols=actions.keys())

                tokens = next_tokens(context)

                if debug:
                    h_print("Token(s) ahead: ", _(str(tokens)), level=1)

                if not tokens:
                    if debug:
                        # This head is dying
                        a_print("***Killing this head.", level=1)
                        if self.debug_trace:
                            self._trace_step_kill(head)
                else:
                    for idx, token in enumerate(tokens):
                        reduce_head = head.for_token(token)
                        self.heads_for_reduce.insert(0, reduce_head)
                    continue
            else:
                # If this head is reduced it can only continue to be reduced by
                # the same token ahead. Check if the head is final.
                if token.symbol is STOP:
                    symbol_action = actions.get(token.symbol, None)
                    if symbol_action and symbol_action[0].action is ACCEPT:
                        if self.in_error_reporting:
                            self.expected.add(token.symbol)
                        else:
                            if debug:
                                a_print("*** {}. SUCCESS!!!!", self.debug_step)
                                self.debug_step += 1
                                if self.debug_trace:
                                    self._trace_step_finish(head)
                            if self.finish_head:
                                self.finish_head.merge_head(head, self)
                            else:
                                self.finish_head = head
                        continue

                # Do all reductions for this head
                symbol_actions = actions.get(token.symbol, [])
                reduce_actions = [a for a in symbol_actions
                                  if a.action is REDUCE]
                for action in reduce_actions:
                    reduce(head, action.prod)

                symbol_act = symbol_actions[0] if symbol_actions else None
                if symbol_act and symbol_act.action is SHIFT:
                    if self.in_error_reporting:
                        self.expected.add(token.symbol)
                    else:
                        self._add_to_heads_for_shift(head)
                elif not reduce_actions and not self.in_error_reporting:
                    if self.error_recovery:
                        # If this head is not reduced and no shift is possible
                        # collect it for possible recovery.
                        self.heads_for_recovery.append(head)
                    elif debug:
                        a_print("** Killing head: ", head, level=1)
                        if self.debug_trace:
                            self._trace_step_kill(head)

                if debug:
                    h_print("No more reductions for this head and lookahead"
                            " token:", _(str(token)), level=1, new_line=True)

    def _do_shifts(self):
        """Perform all shifts.

        Heads that are shifted successfully will be new candidates for
        reducing. If head is not shifted we have a dying head. They will be
        collected for error recovery if enabled.

        """
        debug = self.debug
        if self.debug:
            a_print("**SHIFTING HEADS", new_line=True)

        heads_for_shift = self.heads_for_shift
        self.last_shifts = {}

        if self.debug:
            self._debug_active_heads(heads_for_shift)

        for head in heads_for_shift:
            if debug:
                a_print("Shifting head: ", head, new_line=True)

            self.context = context = head.context

            if debug:
                self._debug_context(context, context.token_ahead,
                                    expected_symbols=None)

            # First action should be SHIFT if it is possible to shift by this
            # token.
            action = context.state.actions.get(context.token_ahead.symbol,
                                               [None])[0]
            if action and action.action is SHIFT:
                if self.dynamic_filter and \
                   not self._call_dynamic_filter(context, SHIFT, None):
                        pass
                else:
                    self._shift(head, action.state, context)
            else:
                # This should never happen as the shift possibility is checked
                # during reducing and only those heads that can be shifted are
                # appended to heads_for_shift
                assert False, "No shift operation possible."

    def _reduce(self, head, production):
        """Executes reduce operation for the given head and production.
        """
        debug = self.debug
        self.context = context = head.context

        if debug:
            a_print("{}. REDUCING by prod ".format(self.debug_step),
                    production, level=1, new_line=True)
            self.debug_step += 1

        prod_len = len(production.rhs)
        roots = []
        if not prod_len:
            context = Context(
                state=context.state.gotos[production.symbol],
                production=production,
                start_position=context.start_position,
                end_position=context.start_position,
                position=context.position,
                layout_content=context.layout_content,
                token_ahead=context.token_ahead,
                layout_content_ahead=context.layout_content_ahead,
                context=context)

            if self.dynamic_filter and \
               not self._call_dynamic_filter(context, REDUCE, []):
                    pass
            else:
                new_head = GSSNode(context)
                self._merge_create_head(new_head, head, head, [], True, True)
        else:
            # Find roots of new heads by going backwards for prod_len steps
            # following all possible paths.
            # Collect subresults along the way to be used with semantic actions
            to_process = [(head, context, [], prod_len, False, True)]
            if debug:
                h_print("Calculate reduction paths of length {}, "
                        "choose only non-empty if possible:"
                        .format(prod_len), level=1)
                h_print("start node=",
                        "[{}], symbol={}, empty=[{},{}], "
                        "length={}".format(head, context.state.symbol,
                                           head.any_empty,
                                           head.all_empty, prod_len), level=2)
            roots = []
            while to_process:
                node, first_head_context, subresults, length, path_has_empty,\
                    path_all_empty = to_process.pop()
                length = length - 1
                if debug:
                    h_print("node = {}".format(node), level=2, new_line=True)
                    h_print("backpath length = {}{}"
                            .format(prod_len - length,
                                    " - ROOT" if not length else ""),
                            level=2)
                for parent, res, any_empty, all_empty in node.parents:
                    path_has_empty = path_has_empty or any_empty
                    path_all_empty = path_all_empty and all_empty
                    if debug:
                        h_print("", "parent=[{}]: path_any_empty={}, "
                                "path_all_empty={}"
                                .format(parent,
                                        path_has_empty, path_all_empty),
                                level=3)
                    parent_subres = [res] + subresults
                    if length:
                        to_process.append(
                            (parent, node.context, parent_subres, length,
                             path_has_empty, path_all_empty))
                    else:
                        roots.append((parent, node.context,
                                      parent_subres, path_has_empty,
                                      path_all_empty))

            # Favour non-empty paths if exists or partialy empty.
            # In none of those exist use empty paths.
            non_empty = [r for r in roots if not r[3] and not r[4]]
            if non_empty:
                roots = non_empty
            else:
                non_empty = [r for r in roots if not r[4]]
                if non_empty:
                    roots = non_empty

            if debug:
                h_print("Reduction paths = ", len(roots),
                        level=1, new_line=True)
                h_print("Roots:", level=1)
                for idx, r in enumerate(roots):
                    h_print("{}.".format(idx+1), r[0], level=2)

            # Create new heads.
            for idx, (root, first_head_context, subresults,
                      any_empty, all_empty) in enumerate(roots):
                if debug:
                    h_print("Reducing path {}:".format(idx + 1),
                            level=1, new_line=True)

                context = Context(
                    state=root.context.state.gotos[production.symbol],
                    production=production,
                    start_position=first_head_context.start_position,
                    end_position=context.end_position,
                    position=context.position,
                    layout_content=first_head_context.layout_content,
                    token_ahead=context.token_ahead,
                    layout_content_ahead=context.layout_content_ahead,
                    context=context)

                if self.dynamic_filter and \
                   not self._call_dynamic_filter(context, REDUCE,
                                                 subresults):
                        pass
                else:
                    new_head = GSSNode(context)
                    self._merge_create_head(new_head, head, root, subresults,
                                            any_empty, all_empty)
                if debug:
                    print()

    def _shift(self, head, state, context):
        """Execute shift operation at the given position to the given state.

        Shift token determined by the given state from input at given position
        and create the new head. Parents will be all nodes that had shift
        action with the given state at the given position.
        """

        last_shifts = self.last_shifts
        debug = self.debug
        token = context.token_ahead

        shifted_head = last_shifts.get((state.state_id,
                                        context.position, token.symbol),
                                       None)
        if shifted_head:
            # If this token has already been shifted connect
            # shifted head to this head.
            result = shifted_head.parents[0][1]
            shifted_head.create_link(head, result, False, False, self)
            if debug and self.debug_trace:
                self._trace_step(head, shifted_head, head,
                                 "S:{}({})".format(
                                     dot_escape(token.symbol.name),
                                     dot_escape(token.value)))
        else:

            if self.debug:
                a_print("{}. SHIFTING".format(self.debug_step),
                        _("\"{}\" to state {} "
                          .format(token.value, context.state.state_id) +
                          "at position " +
                          str(pos_to_line_col(context.input_str,
                                              context.start_position))),
                        level=1, new_line=True)
                self.debug_step += 1

            position = context.position + len(token)
            context = Context(state=state,
                              token=token,
                              start_position=context.position,
                              end_position=position,
                              layout_content=context.layout_content_ahead,
                              position=position,
                              context=context)

            result = self._call_shift_action(context)

            new_head = GSSNode(context)

            # Cache this shift for further shift of the same symbol on the same
            # position.
            last_shifts[(state.state_id, context.start_position,
                         token.symbol)] = new_head

            self.heads_for_reduce.append(new_head)
            if debug:
                a_print("New shifted head ", new_head, level=1)
                if self.debug_trace:
                    self._trace_head(new_head,
                                     "{}:{}".format(
                                         state.state_id,
                                         dot_escape(state.symbol.name)))
                    self._trace_step(head, new_head, head,
                                     "S:{}({})".format(
                                         dot_escape(token.symbol.name),
                                         dot_escape(token.value)))

            new_head.create_link(head, result, False, False, self)

    def _add_to_heads_for_shift(self, new_head):
        """Adds new head for shift or merges if already added."""
        for head in self.heads_for_shift:
            if head == new_head:
                if self.debug:
                    h_print("Merging head for shifting.", level=1)
                head.merge_head(new_head, self)
                break
        else:
            if self.debug:
                h_print("New head for shifting: ", new_head,
                        level=1, new_line=True)
            self.heads_for_shift.append(new_head)

    def _merge_create_head(self, new_head, old_head, root_head, subresults,
                           any_empty, all_empty):
        """Adds new head or merges if already exist on the stack. Executes semantic
        actions. Detects automata looping.
        """

        debug = self.debug
        context = new_head.context

        if new_head == old_head:
            # Special case is reduction of empty production. For automata state
            # self-reference create stack node loop.
            if debug:
                a_print("Looping automata transition.", level=1)
            result = self._call_reduce_action(context, subresults)
            old_head.parents.append((old_head, result, True, True))

        if all_empty and new_head in self.reducing_heads:
            # Detect automata loop. If we are reducing to the head we already
            # had and the new head is empty we have a loop due to EMPTY
            # reductions.
            if debug:
                a_print("Automata loop detected. ",
                        "Rejecting the new head: {}".format(str(new_head)),
                        level=1)
                if self.debug_trace:
                    self._trace_step_kill(old_head)
            return

        result = self._call_reduce_action(context, subresults)

        for head in chain(self.heads_for_reduce,
                          [self.finish_head] if self.finish_head else []):
            if head == new_head:
                new_head.create_link(root_head, result, any_empty, all_empty,
                                     self)
                if head.merge_head(new_head, self):
                    if self.debug and self.debug_trace:
                        self._trace_step(
                            old_head, head, root_head,
                            "R:{}".format(dot_escape(context.production)))
                break
        else:
            self.heads_for_reduce.append(new_head)
            if self.debug:
                a_print("New reduced head ", new_head, level=2, new_line=True)
                if self.debug_trace:
                    self._trace_head(new_head, "{}:{}".format(
                        new_head.context.state.state_id,
                        dot_escape(new_head.context.state.symbol.name)))
            new_head.create_link(root_head, result, any_empty, all_empty, self)

            if self.debug and self.debug_trace:
                self._trace_step(old_head, new_head, root_head,
                                 "R:{}".format(dot_escape(context.production)))

    def _next_tokens(self, context):
        try:
            tok = super(GLRParser, self)._next_token(context)
            tokens = [tok]
        except DisambiguationError as e:
            # Lexical ambiguity will be handled by GLR
            tokens = e.tokens

        return tokens

    def _setup_error_reporting(self):
        """
        To correctly report what is found ahead and what is expected we shall:
        - execute all grammar recognizers at the farther position reached in
          the input by the last shifted heads. This will be part of the error
          report (what is found ahead if anything can be recognized).
        - for all last shifted heads, simulate parsing for each of possible
          lookaheads in the head's state until either SHIFT or ACCEPT is
          successfuly executed. Collect each possible lookahead where this is
          achieved for reporting. This will be another part of the error
          report (what is expected).
        """
        # Start with the last shifted heads sorted by position.
        self.last_heads_for_reduce.sort(key=lambda h: h.context.position,
                                        reverse=True)
        context = self.last_heads_for_reduce[0].context
        farthest_heads = takewhile(
            lambda h: h.context.position == context.position,
            self.last_heads_for_reduce)

        self.tokens_ahead = self._get_all_possible_tokens_ahead(context)

        for head in farthest_heads:
            for possible_lookahead in head.context.state.actions.keys():
                self.heads_for_reduce.append(
                    head.for_token(Token(possible_lookahead, [])))

    def _do_recovery(self, error):
        """If recovery is enabled, does error recovery for the heads in
        heads_for_recovery.

        """
        debug = self.debug
        for head in self.heads_for_recovery:
            context = head.context
            input_str = context.input_str
            symbols = context.state.actions.keys()
            if debug:
                a_print("**Error found. ",
                        "Recovery initiated for head {}.".format(head),
                        level=1, new_line=True)
                h_print("Symbols expected: ", symbols, level=1)
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

            if position is not None or token is not None:
                if position:
                    last_error = self.errors[-1]
                    last_error.location.end_position = position
                    head.context.position = position
                    if debug:
                        h_print("Advancing position to ",
                                pos_to_line_col(input_str, position),
                                level=1)
                head.context.token_ahead = token

                if token and debug:
                    h_print("Introducing token {}", repr(token), level=1)

                self.heads_for_reduce.append(head)

            else:
                if debug:
                    a_print("Killing head: ", head, level=1)
                    if self.debug_trace:
                        self._trace_step_kill(head)

        return bool(token or position)

    def _debug_active_heads(self, heads):
        h_print("Active heads = ", len(heads))
        for head in heads:
            prints("\t{}".format(head))
        h_print("Number of trees = ", sum([h.number_of_trees for h in heads]))

    def _debug_context(self, context, lookahead_tokens,
                       expected_symbols=None):
        input_str = context.input_str
        position = context.position
        layout_content = context.layout_content
        h_print("Position:",
                pos_to_line_col(input_str, position), level=1)
        h_print("Context:", _(position_context(context)), level=1)
        if layout_content:
            h_print("Layout: ", "'{}'".format(_(layout_content)), level=1)
        if expected_symbols:
            h_print("Symbols expected: ",
                    [s.name for s in expected_symbols], level=1)
        if lookahead_tokens:
            h_print("Token(s) ahead:", _(str(lookahead_tokens)), level=1)

    @no_colors
    def _trace_head(self, new_head, label):
        self.dot_trace += '{} [label="{}"];\n'.format(new_head.key, label)

    @no_colors
    def _trace_step(self, old_head, new_head, root_head, label=''):
        new_head_key = new_head.key if isinstance(new_head, GSSNode) \
                       else new_head
        self.dot_trace += '{} -> {} [label="{}. {}" {}];\n'.format(
            old_head.key, new_head_key, self.debug_step, label,
            TRACE_DOT_STEP_STYLE)
        self.dot_trace += '{} -> {};\n'.format(new_head_key, root_head.key)

    @no_colors
    def _trace_step_finish(self, from_head):
        self._trace_step(from_head, "success", from_head)

    @no_colors
    def _trace_step_kill(self, from_head):
        self.dot_trace += \
            '{}_killed [shape="diamond" fillcolor="red" label="killed"];\n'\
            .format(from_head.key)
        self.dot_trace += '{} -> {}_killed [label="{}." {}];\n'\
            .format(from_head.key, from_head.key, self.debug_step,
                    TRACE_DOT_STEP_STYLE)

    @no_colors
    def _trace_step_drop(self, from_head, to_head):
        self.dot_trace += '{} -> {} [label="drop empty" {}];\n'\
            .format(from_head.key, to_head.key, TRACE_DOT_DROP_STYLE)

    def _export_dot_trace(self):
        file_name = "{}_trace.dot".format(self.file_name) \
                    if self.file_name else "parglare_trace.dot"
        with codecs.open(file_name, 'w', encoding="utf-8") as f:
            f.write(DOT_HEADER)
            f.write(self.dot_trace)
            f.write("}\n")

        prints("Generated file {}.".format(file_name))
        prints("You can use dot viewer or generate pdf with the "
               "following command:")
        h_print("dot -Tpdf {0} -O {0}.pdf".format(file_name))


class GSSNode(object):
    """Graphs Structured Stack node.

    Attributes:
        context(Context): The parsing context.
        any_empty(bool): If some of this node parent links results are empty.
        all_empty(bool): If all of this node parent link results are empty.
        parents(list): list of (parent GSSNode, result, any_empty, all_empty)
             Each stack node might have multiple parents which represent
             multiple path parse took to reach the current state. Each
             parent link keeps a result of semantic action executed during
             shift or reduce operation that created this node/link and the
             flag if any part of the result is obtained using epsilon/empty
             production.
    """
    __slots__ = ['context', 'parents', 'any_empty', 'all_empty',
                 'number_of_trees', '_hash']

    def __init__(self, context, number_of_trees=0):
        self.context = context

        # Initialize to neutral elements
        self.any_empty = False
        self.all_empty = True

        self.parents = []
        self.number_of_trees = number_of_trees

        self._hash = hash((self.context.state.state_id,
                           self.context.start_position,
                           self.context.token_ahead))

    def less_empty(self, other):
        return (other.all_empty and not self.all_empty) or \
            (other.any_empty and not self.any_empty)

    def merge_head(self, other, parser):
        """Merge same top stack nodes.

        Merge will be succesfull only if this node is "more empty" than the
        other node.
        """
        # Reject merging if other node is "more empty"
        if other.all_empty or self.less_empty(other):
            if parser.debug:
                h_print("Rejected merging of empty head: ", other, level=1)
            return False
        else:
            if self.parents and other.less_empty(self):
                if parser.debug:
                    h_print("Merging less empty head to more empty",
                            " -> less empty head wins.", level=1)
                    if parser.debug_trace:
                        for p in self.parents:
                            parser._trace_step_drop(self, p[0])
                self.any_empty = False
                self.all_empty = True
                self.parents = []
                self.number_of_trees = 0

            self.any_empty |= other.any_empty
            self.all_empty &= other.all_empty
            self.number_of_trees += other.number_of_trees
            self.parents.extend(other.parents)

            if parser.debug:
                h_print("Merging head ", other, level=1)
                h_print("to head", self, level=2)
            return True

    def create_link(self, parent, result, any_empty, all_empty, parser):
        self.parents.append((parent, result, any_empty, all_empty))
        self.number_of_trees += parent.number_of_trees
        self.any_empty |= any_empty
        self.all_empty &= all_empty
        if parser.debug:
            h_print("Creating link \tfrom head:", self, level=2)
            h_print("  to head:", parent, level=4)

    def for_token(self, token):
        """Create head for the given token either by returning this head if the
        token is appropriate or making a clone.

        This is used to support lexical ambiguity. Multiple tokens might be
        matched at the same state and position. In this case parser should
        fork and this is done by cloning stack head.

        """
        if self.context.token_ahead is None:
            self.context.token_ahead = token
            return self
        elif self.context.token_ahead == token:
            return self
        else:
            context = copy(self.context)
            context.token_ahead = token
            new_head = GSSNode(context, self.number_of_trees)
            new_head.parents = list(self.parents)
            new_head.any_empty = self.any_empty
            new_head.all_empty = self.all_empty
            return new_head

    def __eq__(self, other):
        """Stack nodes are equal if they are on the same position in the
        same state for the same lookahead token.

        """
        return self.context.state.state_id == other.context.state.state_id \
            and self.context.start_position == other.context.start_position \
            and self.context.token_ahead == other.context.token_ahead

    def __ne__(self, other):
        return not self == other

    def __str__(self):
        return _("<state={}:{}, id={}, pos={}, endpos={}{}, empty=[{},{}], "
                 "parents={}, trees={}>".format(
                     self.context.state.state_id, self.context.state.symbol,
                     id(self),
                     self.context.start_position, self.context.end_position,
                     ", token ahead={}".format(self.context.token_ahead)
                     if self.context.token_ahead is not None else "",
                     self.any_empty, self.all_empty, len(self.parents),
                     self.number_of_trees))

    def __repr__(self):
        return str(self)

    def __hash__(self):
        return self._hash

    @property
    def key(self):
        """Head unique idenfier used for dot trace."""
        return "head_{}_{}_{}".format(self.context.state.state_id,
                                      self.context.start_position,
                                      self.context.end_position)


DOT_HEADER = """
    digraph parglare_trace {
    rankdir=LR
    fontname = "Bitstream Vera Sans"
    fontsize = 8
    node[
        style=filled,
        fillcolor=aliceblue
    ]
    nodesep = 0.3
    edge[dir=black,arrowtail=empty]

"""

TRACE_DOT_STEP_STYLE = 'color="red" style="dashed"'
TRACE_DOT_DROP_STYLE = 'color="orange" style="dotted"'
