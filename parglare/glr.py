# -*- coding: utf-8 -*-
import codecs
from itertools import takewhile
from parglare import Parser
from parglare import termui as t
from .parser import SHIFT, REDUCE, ACCEPT, pos_to_line_col, Token
from .common import replace_newlines as _, position_context
from .export import dot_escape
from .termui import prints, h_print, a_print


def no_colors(f):
    """
    Decorator for trace methods to prevent ANSI COLOR codes appearing in
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
    def __init__(self, *args, **kwargs):

        table = kwargs.get('table', None)
        lexical_disambiguation = kwargs.get('lexical_disambiguation', None)
        if table is None:
            # The default for GLR is not to use any strategy preferring shifts
            # over reduce thus investigating all possibilities.
            # These settings are only applicable if parse table is not computed
            # yet. If it is, then leave None values to avoid
            # "parameter overriden" warnings.
            prefer_shifts = kwargs.get('prefer_shifts', None)
            prefer_shifts_over_empty = kwargs.get('prefer_shifts_over_empty',
                                                  None)

            prefer_shifts = False \
                if prefer_shifts is None else prefer_shifts
            prefer_shifts_over_empty = False \
                if prefer_shifts_over_empty is None \
                else prefer_shifts_over_empty
            if lexical_disambiguation is None:
                lexical_disambiguation = False

            kwargs['prefer_shifts'] = prefer_shifts
            kwargs['prefer_shifts_over_empty'] = prefer_shifts_over_empty

        kwargs['lexical_disambiguation'] = lexical_disambiguation

        super(GLRParser, self).__init__(*args, **kwargs)

    def _check_parser(self):
        """
        Conflicts in table are allowed with GLR.
        """
        pass

    def parse(self, input_str, position=0, file_name=None, extra=None):
        """
        Parses the given input string.
        Args:
            input_str(str): A string to parse.
            position(int): Position to start from.
            file_name(str): File name if applicable. Used in error reporting.
            extra: An object that keeps custom parsing state. If not given
                initialized to dict.
        """

        if self.debug:
            a_print("*** PARSING STARTED\n")
            self.debug_step = 0
            if self.debug_trace:
                self.dot_trace = ""

        self.input_str = input_str
        self.file_name = file_name
        self.extra = {} if extra is None else extra

        # Error reporting and recovery
        self.errors = []
        self.in_error_reporting = False
        self.expected = set()
        self.tokens_ahead = []
        self.last_shifted_heads = []

        # A stack of heads being reduced. Contains tuples (head, list of
        # pending reductions). Used to perform reductions in a depth-first
        # manner.
        self.reducing_stack = []
        # For optimization, keep only state ids for quick check before
        # searching.
        self.reducing_stack_states = []

        # Heads that are fully reduced and thus are candidates for the next
        # shifting or accepting. Fully reduced heads (heads without any pending
        # reduction) from reducing_stack are merged to these heads.
        self.reduced_heads = {}

        # Heads created during shift operations.
        self.shifted_heads = []

        # Accepted (finished) heads
        self.accepted_heads = []

        # We start with a single parser head in state 0.
        start_head = GSSNode(self, self.table.states[0], 0, position,
                             number_of_trees=1)
        self._init_dynamic_disambiguation(start_head)
        self.shifted_heads.append(start_head)

        if self.debug and self.debug_trace:
            self._trace_head(start_head)

        # The main loop
        while True:
            if not self.in_error_reporting:
                self.last_shifted_heads = list(self.shifted_heads)
            self._do_reductions()
            if self.in_error_reporting:
                # Expected symbols are only those that can cause reduced head
                # to shift.
                self.expected = set([
                    h.token_ahead.symbol for h in self.reduced_heads
                    if h.token_ahead.symbol in h.state.actions
                    and SHIFT in [action.action
                                  for action
                                  in h.state.actions[h.token_ahead.symbol]]])
                if self.debug:
                    a_print("*** LEAVING ERROR REPORTING MODE.",
                            new_line=True)
                    h_print("Tokens expected:",
                            ', '.join([t.name for t in self.expected]),
                            level=1)
                    h_print("Tokens found:", self.tokens_ahead, level=1)

                self.reduced_heads = {}
                self.in_error_reporting = False

                # After leaving error reporting mode, register error and try
                # recovery if enabled
                context = self.last_shifted_heads[0]
                self.errors.append(
                    self._create_error(
                        context, self.expected,
                        tokens_ahead=self.tokens_ahead,
                        symbols_before=list(
                            {h.state.symbol
                             for h in self.last_shifted_heads}),
                        last_heads=self.last_shifted_heads))
                if self.error_recovery:
                    if self.debug:
                        a_print("*** STARTING ERROR RECOVERY.",
                                new_line=True)
                    if self._do_recovery():
                        # Error recovery succeeded
                        if self.debug:
                            a_print(
                                "*** ERROR RECOVERY SUCCEEDED. CONTINUING.",
                                new_line=True)
                        continue
                    else:
                        break
                else:
                    break
            else:
                self._do_shifts_accepts()
                if not self.shifted_heads and not self.accepted_heads:
                    if self.debug:
                        a_print("*** ENTERING ERROR REPORTING MODE.",
                                new_line=True)
                    self._enter_error_reporting()
                    continue

                if not self.shifted_heads:
                    break

        if self.debug and self.debug_trace:
            self._export_dot_trace()

        if self.accepted_heads:
            # Return results
            results = [x.results for head in self.accepted_heads
                       for x in head.parents]
            if self.debug:
                a_print("*** {} sucessful parse(s).".format(len(results)))

            self._remove_transient_state()
            return results
        else:
            # Report error
            self._remove_transient_state()
            raise self.errors[-1]

    def _do_reductions(self):
        """
        Perform all possible reductions for this shift level.
        """
        debug = self.debug

        if debug:
            a_print("** REDUCING", new_line=True)
            self._debug_active_heads(self.shifted_heads)

        if not self.in_error_reporting:
            # First we shall find lookaheads for all shifted heads and split
            # heads on lexical ambiguity.
            shifted_heads = []
            while self.shifted_heads:
                head = self.shifted_heads.pop()
                if head.token_ahead is not None:
                    # This might happen if this head is produced by error
                    # recovery
                    shifted_heads.append(head)
                    continue

                if debug:
                    h_print("Finding lookaheads", new_line=True)
                self._skipws(head, self.input_str)

                tokens = self._next_tokens(head)

                if debug:
                    self._debug_context(
                        head.position,
                        head.layout_content_ahead,
                        lookahead_tokens=tokens,
                        expected_symbols=head.state.actions.keys())

                if tokens:
                    while tokens:
                        # For lexical ambiguity create a new head for each new
                        # token recognized ahead.
                        shifted_heads.append(head.for_token(tokens.pop()))
                else:
                    # Can't find lookahead. This head can't progress
                    if debug:
                        h_print('No lookaheads found. Killing head.')

        else:
            shifted_heads = self.shifted_heads

        while shifted_heads:
            head = shifted_heads.pop()
            self._prepare_reductions(head)
            while self.reducing_stack:
                while self.reducing_stack[-1][1]:
                    reduction = self.reducing_stack[-1][1].pop()
                    new_head = self._reduce(head, reduction)
                    if new_head is not None:
                        head = new_head
                        self._prepare_reductions(head)

                # No more reduction for top of the stack head.
                # Pop of the stack and merge to reduced heads.
                head = self.reducing_stack.pop()[0]
                self.reducing_stack_states.pop()
                if self.debug:
                    h_print('No more reductions for head:', str(head),
                            level=1, new_line=True)
                reduced_head = self.reduced_heads.get(head, None)
                if reduced_head is None:
                    if self.debug:
                        h_print('Adding head to reduced heads.', level=1)
                    self.reduced_heads[head] = head
                else:
                    reduced_head.merge_head(head, self)

    def _do_shifts_accepts(self):
        """
        Do shifts and accepts of the reduced heads
        """

        debug = self.debug
        if debug:
            a_print("** SHIFTING", new_line=True)
            self._debug_active_heads(self.reduced_heads.values())

        while self.reduced_heads:
            head, __ = self.reduced_heads.popitem()
            actions = head.state.actions.get(head.token_ahead.symbol)
            action = actions[0] if actions else None

            if action is None or action.action == REDUCE:
                if debug:
                    a_print("Can't shift head: ", str(head), new_line=True)
            else:
                if action.action == ACCEPT:
                    if debug:
                        a_print('**ACCEPTING HEAD: ', str(head))
                    self.accepted_heads.append(head)

                else:
                    self._shift(head, action.state)

    def _prepare_reductions(self, head):
        """
        Finds all possible reduction for the given head and make a new stack
        entry with pending reductions.
        """
        debug = self.debug

        if debug:
            a_print("Preparing reductions for head: ", str(head),
                    new_line=True)

        productions = []
        symbol_actions = head.state.actions.get(head.token_ahead.symbol, [])
        for symbol_action in symbol_actions:
            action = symbol_action.action
            if action is REDUCE:
                productions.append(symbol_action.prod)

        if debug:
            h_print("\tProductions:\n\t\t",
                    '\n\t\t'.join([str(p) for p in productions]))

        reductions = []
        for production in productions:
            if debug:
                h_print('Processing production:', str(production),
                        level=1, new_line=True)
            prod_len = len(production.rhs)
            if prod_len == 0:
                # Special case, empty reduction
                reductions.append((head, production, [],
                                   head.position, head.position))
            else:
                # Find roots of possible reductions by going backwards for
                # prod_len steps following all possible paths. Collect
                # subresults along the way to be used with semantic actions
                to_process = [(head, [], prod_len, None)]
                if debug:
                    h_print("Calculate reduction paths of length {}:"
                            .format(prod_len), level=1)
                    h_print("start node=",
                            "[{}], symbol={}, "
                            "length={}".format(head, head.state.symbol,
                                               prod_len), level=2)
                while to_process:
                    (node,
                     results,
                     length,
                     last_parent) = to_process.pop()
                    length = length - 1
                    if debug:
                        h_print("node = {}".format(node), level=2,
                                new_line=True)
                        h_print("backpath length = {}{}"
                                .format(prod_len - length,
                                        " - ROOT" if not length else ""),
                                level=2)

                    first_parent = None
                    for parent in node.parents:
                        if debug:
                            h_print("", str(parent.head), level=3)

                        new_results = [parent.results] + results

                        if first_parent is None:
                            first_parent = parent

                        if last_parent is None:
                            last_parent = parent

                        if length:
                            to_process.append((parent.parent, new_results,
                                               length, last_parent))
                        else:
                            reductions.append((parent.parent,
                                               production,
                                               new_results,
                                               first_parent.start_position,
                                               last_parent.end_position))
                        first_parent = parent

            if debug:
                h_print("Reduction paths = ", len(reductions), level=1,
                        new_line=True)

                for idx, reduction in enumerate(reductions):
                    if debug:
                        h_print("Reduction {}:".format(idx + 1),
                                reductions,
                                level=1)
        self.reducing_stack.append((head, reductions))
        self.reducing_stack_states.append(head.state.state_id)

    def _reduce(self, head, reduction):
        """
        Executes the given reduction.
        """

        root_head, production, results, \
            start_position, end_position = reduction
        if start_position is None:
            start_position = end_position = root_head.position
        state = root_head.state.gotos[production.symbol]

        if self.debug:
            self.debug_step += 1
            a_print("{}. REDUCING head ".format(self.debug_step), str(head),
                    new_line=True)
            a_print("by prod ", production, level=1)
            a_print("to state {}:{}".format(state.state_id,
                                            state.symbol), level=1)
            a_print("root is ", root_head, level=1)
            a_print("Position span: {} - {}".format(start_position,
                                                    end_position), level=1)

        new_head = GSSNode(self, state, head.position,
                           head.shift_level,
                           number_of_trees=head.number_of_trees,
                           token_ahead=head.token_ahead)

        parent = GSSNodeParent(root_head, new_head, results,
                               start_position, end_position,
                               production=production)

        if not self.dynamic_filter or \
                self._call_dynamic_filter(parent, head.state, state,
                                          REDUCE, production, results):

            parent.results = self._call_reduce_action(parent, results)

            # Check for possible automata loops for the newly reduced head.
            # Handle loops by creating GSS loops for empty reduction loops or
            # rejecting cyclic reductions for non-empty reductions.
            if self.debug:
                h_print('Check loops. Reduce stack states:',
                        self.reducing_stack_states,
                        level=1)
            if new_head.state.state_id in self.reducing_stack_states:
                if root_head.shift_level == new_head.shift_level:
                    # Empty reduction. If we already have this on the reduce
                    # stack we shall make a GSS loop and remove this head from
                    # further reductions.
                    for shead, __ in reversed(self.reducing_stack):
                        if new_head == shead:
                            # If found we shall make a GSS loop only if the
                            # reduction is empty.
                            if root_head == head:
                                if self.debug:
                                    h_print('Looping due to empty reduction.'
                                            ' Making GSS loop.', level=1)
                                shead.create_link(parent)
                            else:
                                if self.debug:
                                    h_print(
                                        'Looping with an empty tree reduction',
                                        level=1)

                            if self.debug:
                                h_print('Not processing further this head.',
                                        level=1)
                            return
                else:
                    # Non-empty reduction If the same state has been reduced,
                    # we have looping by cyclic grammar and should report and
                    # reject invalid state.
                    for shead, __ in reversed(self.reducing_stack):
                        if new_head == shead \
                                and root_head == shead.parents[0].parent:
                            if self.debug:
                                a_print('Cyclic grammar detected. '
                                        'Breaking loop.',
                                        level=1)
                                h_print('Not processing further this head.',
                                        level=1)
                            return

            # No cycles. Do the reduction.
            if self.debug:
                a_print("New head: ", new_head, level=1, new_line=True)
                if self.debug_trace:
                    self._trace_head(new_head)
                    self._trace_step(head, new_head, root_head,
                                     "R:{}".format(dot_escape(production)))

            new_head.create_link(parent)
            return new_head

    def _shift(self, head, to_state):
        """
        Shifts the head and executes semantic actions.
        """
        debug = self.debug
        if debug:
            self.debug_step += 1
            a_print("{}. SHIFTING head: ".format(self.debug_step), head,
                    new_line=True)

        for shifted_head in self.shifted_heads:
            if shifted_head.state is to_state:
                break
        else:
            shifted_head = None

        if shifted_head:
            # If this token has already been shifted connect
            # shifted head to this head.
            shead_parent = shifted_head.parents[0]
            parent = GSSNodeParent(head, shifted_head, shead_parent.results,
                                   shead_parent.start_position,
                                   shead_parent.end_position,
                                   token=shead_parent.token)
            if not self.dynamic_filter or \
                    self._call_dynamic_filter(parent, head.state, to_state,
                                              SHIFT):

                shifted_head.create_link(parent)
                if debug and self.debug_trace:
                    token = head.token_ahead
                    self._trace_step(head, shifted_head, head,
                                     "S:{}({})".format(
                                        dot_escape(token.symbol.name),
                                        dot_escape(token.value)))
        else:
            # We need to create new shifted head
            if debug:
                self._debug_context(head.position,
                                    lookahead_tokens=head.token_ahead,
                                    expected_symbols=None)

            end_position = head.position + len(head.token_ahead)
            new_head = GSSNode(self, to_state, end_position,
                               head.shift_level + 1)
            parent = GSSNodeParent(head, new_head, None,
                                   head.position, end_position,
                                   token=head.token_ahead)

            if not self.dynamic_filter or \
                    self._call_dynamic_filter(parent, head.state, to_state,
                                              SHIFT):

                parent.results = self._call_shift_action(parent)

                if self.debug:
                    token = head.token_ahead
                    a_print("New shifted head ", new_head, level=1)
                    if self.debug_trace:
                        self._trace_head(new_head)
                        self._trace_step(head, new_head, head,
                                         "S:{}({})".format(
                                            dot_escape(token.symbol.name),
                                            dot_escape(token.value)))

                new_head.create_link(parent)
                self.shifted_heads.append(new_head)

    def _enter_error_reporting(self):
        """
        To correctly report what is found ahead and what is expected we shall:

            - execute all grammar recognizers at the farther position reached
              in the input by the active heads.  This will be part of the error
              report (what is found ahead if anything can be recognized).

            - for all last reducing heads, simulate parsing for each of
              possible lookaheads in the head's state until either SHIFT or
              ACCEPT is successfuly executed.  Collect each possible lookahead
              where this is achieved for reporting.  This will be another part
              of the error report (what is expected).

        """

        self.in_error_reporting = True

        # Start with the last shifted heads sorted by position.
        self.last_shifted_heads.sort(key=lambda h: h.position, reverse=True)
        last_head = self.last_shifted_heads[0]
        farthest_heads = takewhile(
            lambda h: h.position == last_head.position,
            self.last_shifted_heads)

        self.tokens_ahead = self._get_all_possible_tokens_ahead(last_head)

        for head in farthest_heads:
            for possible_lookahead in head.state.actions.keys():
                h = head.for_token(Token(possible_lookahead, []))
                self.shifted_heads.append(h)

    def _do_recovery(self):
        """
        If recovery is enabled, does error recovery for the heads in
        last_shifted_heads.

        """
        error = self.errors[-1]
        debug = self.debug
        self.shifted_heads = []
        for head in self.last_shifted_heads:
            if debug:
                input_str = head.input_str
                symbols = head.state.actions.keys()
                h_print("Recovery initiated for head {}.".format(head),
                        level=1, new_line=True)
                h_print("Symbols expected: ",
                        [s.name for s in symbols], level=1)
            if type(self.error_recovery) is bool:
                # Default recovery
                if debug:
                    prints("\tDoing default error recovery.")
                successful = self.default_error_recovery(head)
            else:
                # Custom recovery provided during parser construction
                if debug:
                    prints("\tDoing custom error recovery.")
                successful = self.error_recovery(head, error)

            if successful:
                error.location.context.end_position = head.position
                if debug:
                    a_print("New position is ",
                            pos_to_line_col(input_str, head.position),
                            level=1)
                    a_print("New lookahead token is ", head.token_ahead,
                            level=1)
                self.shifted_heads.append(head)
            else:
                if debug:
                    a_print("Killing head: ", head, level=1)
                    if self.debug_trace:
                        self._trace_step_kill(head)
        return bool(self.shifted_heads)

    def _remove_transient_state(self):
        """
        Delete references to transient parser objects to lower memory
        consumption.
        """
        del self.reduced_heads
        del self.shifted_heads
        del self.reducing_stack
        del self.reducing_stack_states
        del self.last_shifted_heads

    def _debug_active_heads(self, heads):
        if not heads:
            h_print('No active heads.')
        else:
            h_print("Active heads = ", len(heads))
            for head in heads:
                prints("\t{}".format(head))
            h_print("Number of trees = {}".format(
                sum([h.number_of_trees for h in heads])))

    def _debug_reduce_heads(self):
        heads = list(self.reduced_heads.values())
        h_print("Reduced heads = ", len(heads))
        for head in heads:
            prints("\t{}".format(head))

        heads = list(self.heads_for_reduction.values())
        h_print("Heads for reduction:", len(heads))
        for head in heads:
            prints("\t{}".format(head))

    def _debug_context(self, position, layout_content=None,
                       lookahead_tokens=None, expected_symbols=None):
        input_str = self.input_str
        h_print("Position:",
                pos_to_line_col(input_str, position))
        h_print("Context:", _(position_context(input_str, position)))
        if layout_content:
            h_print("Layout: ", "'{}'".format(_(layout_content)), level=1)
        if expected_symbols:
            h_print("Symbols expected: ",
                    [s.name for s in expected_symbols])
        if lookahead_tokens:
            h_print("Token(s) ahead:", _(str(lookahead_tokens)))

    @no_colors
    def _trace_head(self, head):
        self.dot_trace += '{} [label="{}:{}"];\n'\
            .format(head.key, head.state.state_id,
                    dot_escape(head.state.symbol.name))

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


class GSSNodeParent(object):
    """
    A link to the parent node in GSS stack.
    """

    __slots__ = ['parent', 'head', 'results', 'start_position', 'end_position',
                 'token', 'production', 'node', 'extra']

    def __init__(self, parent, head, results, start_position,
                 end_position=None, token=None, production=None):
        self.parent = parent
        self.head = head
        self.results = results
        self.start_position = start_position
        self.end_position = end_position \
            if end_position is not None else start_position

        # For shift nodes
        self.token = token

        # For reduced nodes
        self.production = production

        # Caching extra for faster access
        self.extra = self.head.parser.extra

        # Parse tree node used if parse tree is produced
        self.node = None

    @property
    def layout_content(self):
        return self.parent.layout_content_ahead

    def __getattr__(self, name):
        """
        All other property access is delegated to the parsing head.
        """
        return getattr(self.head, name)

    def __str__(self):
        return "start_position={}, end_position={}".format(
            self.start_position, self.end_position)

    def __repr__(self):
        return str(self)


class GSSNode(object):
    """
    Graphs Structured Stack node.

    Attributes:
        parser(GLRParser):
        state(LRState):
        position(int):
        shift_level(int):
        parents(list of GSSNodeParent):
             Each stack node might have multiple parents which represent
             multiple path parse took to reach the current state. Each
             parent link keeps a result of semantic action executed during
             shift or reduce operation that created this node/link and the
             link to the node from which it was reduced (None if shifted).
        node_id(int): Unique node id. Nodes with the same id and lookahead
            token are considered the same. Calculated from shift level and
            state id.
        number_of_trees(int): Total number of trees/solution defined by this
             head.
    """
    __slots__ = ['parser', 'node_id', 'state', 'position', 'shift_level',
                 'parents', 'number_of_trees', 'token_ahead',
                 'layout_content_ahead', '_hash']

    def __init__(self, parser, state, position, shift_level, number_of_trees=0,
                 token=None, token_ahead=None):
        self.parser = parser
        self.state = state
        self.position = position
        self.shift_level = shift_level
        self.node_id = 100000000 * state.state_id + shift_level

        self.token_ahead = token_ahead
        self.layout_content_ahead = ''

        self.parents = []
        self.number_of_trees = number_of_trees

    def merge_head(self, other, parser):
        """
        Merge same top stack nodes.
        """
        if self is other:
            pass
        self.number_of_trees += other.number_of_trees
        for p in other.parents:
            p.head = self
        self.parents.extend(other.parents)

        if parser.debug:
            h_print("Merging head ", other)
            h_print("to head", self, level=1)

    def create_link(self, parent):
        self.parents.append(parent)
        self.number_of_trees = parent.parent.number_of_trees
        if self.parser.debug:
            h_print("Creating link \tfrom head:", self, level=1)
            h_print("  to head:", parent.parent, level=3)

    def for_token(self, token):
        """
        Create head for the given token either by returning this head if the
        token is appropriate or making a clone.

        This is used to support lexical ambiguity. Multiple tokens might be
        matched at the same state and position. In this case parser should
        fork and this is done by cloning stack head.
        """
        if self.token_ahead is None:
            self.token_ahead = token
            return self
        elif self.token_ahead == token:
            return self
        else:
            new_head = GSSNode(self.parser, self.state, self.position,
                               self.shift_level, self.number_of_trees,
                               token_ahead=token)
            new_head.parents = list(self.parents)
            return new_head

    def __eq__(self, other):
        """
        Stack nodes are equal if they are on the same position in the same
        state for the same lookahead token.
        """
        return self.node_id == other.node_id \
            and self.token_ahead == other.token_ahead

    def __ne__(self, other):
        return not self == other

    def __str__(self):
        return _("<state={}:{}, id={}{}, position={}, "
                 "parents={}, trees={}>".format(
                     self.state.state_id, self.state.symbol,
                     id(self),
                     ", token ahead={}".format(self.token_ahead)
                     if self.token_ahead is not None else "",
                     self.position,
                     len(self.parents),
                     self.number_of_trees))

    def __repr__(self):
        return str(self)

    def __hash__(self):
        return hash((self.node_id, self.token_ahead.symbol))

    @property
    def key(self):
        """Head unique idenfier used for dot trace."""
        return "head_{}".format(id(self))

    @property
    def extra(self):
        return self.parser.extra

    @extra.setter
    def extra(self, new_value):
        self.parser.extra = new_value

    @property
    def input_str(self):
        return self.parser.input_str

    @property
    def file_name(self):
        return self.parser.file_name

    @property
    def symbol(self):
        return self.state.symbol


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
