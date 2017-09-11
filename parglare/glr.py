from __future__ import print_function, unicode_literals
import codecs
from itertools import chain
from parglare import Parser
from .exceptions import DisambiguationError, ParseError, nomatch_error
from .parser import position_context, SHIFT, REDUCE, ACCEPT, \
    default_reduce_action, default_shift_action, pos_to_line_col, STOP, \
    Context
from .export import dot_escape


class GLRParser(Parser):
    """
    A Tomita-style GLR parser.
    """

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
            print("\n*** PARSING STARTED\n")
            if self.debug_trace:
                self._start_trace()

        self.errors = []
        self.current_error = None

        # Initialize dynamic disambiguation
        if self.dynamic_filter:
            if self.debug:
                print("\Initializing dynamic disambiguation.")
            self.dynamic_filter(None, None, None, None, None)

        self.last_position = 0
        self.expected = set()
        self.empty_reductions_results = {}
        self.context = context = context if context else Context()
        position, layout_content = self._skipws(context, input_str, position)

        # We start with a single parser head in state 0.
        start_head = GSSNode(self.table.states[0],
                             start_position=position,
                             end_position=position,
                             layout_content=layout_content,
                             number_of_trees=1)
        self.heads_for_reduce = [start_head]
        self.heads_for_shift = []

        self.input_str = input_str
        self.file_name = file_name
        self.finish_head = None

        if self.debug and self.debug_trace:
            self._trace_head(start_head, str(start_head.state.state_id))

        # The main loop
        while self.heads_for_reduce:
            self._do_reductions(context)
            if self.heads_for_shift:
                self._do_shifts(context)
            # If after shifting we don't have any heads for reduce
            # and we haven't found any final parse, do recovery.
            if self.error_recovery:
                if not self.heads_for_reduce and not self.finish_head:
                    self._do_recovery(context)
                else:
                    # Get out from error recovery mode.
                    self.current_error = None
                    # Report dying heads
                    if self.debug:
                        for h in self.heads_for_recovery:
                            print("\t** Killing head: {}".format(h))
                            if self.debug_trace:
                                self._trace_step_kill(h)

        if not self.finish_head:
            if self.debug and self.debug_trace:
                self._export_dot_trace()
            raise ParseError(
                file_name, input_str, self.last_position,
                nomatch_error(self.expected))

        results = [x[1] for x in self.finish_head.parents]
        if self.debug:
            print("*** {} sucessful parse(s).".format(len(results)))
            if self.debug_trace:
                self._export_dot_trace()

        return results

    def _do_reductions(self, context):
        """
        Reduces active heads until no more heads can be reduced.
        """
        debug = self.debug
        if debug:
            print("\n**REDUCING HEADS")
            self._debug_active_heads(self.heads_for_reduce)

        next_tokens = self._next_tokens
        reduce = self.reduce
        input_str = self.input_str

        # Reductions
        heads_for_reduce = self.heads_for_reduce
        self.heads_for_shift = []

        # For automata loop detection
        self.reducing_heads = []

        if self.error_recovery:
            # Pairs of (new_position, token) keyed by (position, symbols)
            self.recovery_results = {}
            # Pairs of (head, symbols)
            self.heads_for_recovery = []

        while heads_for_reduce:
            head = heads_for_reduce.pop()
            self.reducing_heads.append(head)
            if debug:
                print("\nReducing head: {}".format(str(head)))

            position = head.next_position
            if position > self.last_position:
                self.last_position = position
                self.expected = set()

            state = head.state
            actions = state.actions
            self.expected.update(actions.keys())

            lookahead_token = head.token_ahead

            if lookahead_token is not None:
                layout_content = head.next_layout_content
                position = head.next_position
                tokens = [lookahead_token]

                if debug:
                    self._debug_context(
                        input_str, position, lookahead_token,
                        expected_symbols=[lookahead_token.symbol],
                        layout_content=layout_content)

                # If this head is reduced it can only continue to be reduced by
                # the same token ahead. Check if the head is final.
                if lookahead_token.symbol is STOP:
                    symbol_action = actions.get(lookahead_token.symbol, None)
                    if symbol_action and symbol_action[0].action is ACCEPT:
                        if debug:
                            print("\t*** SUCCESS!!!!")
                            if self.debug_trace:
                                self._trace_step_finish(head)
                        if self.finish_head:
                            self.finish_head.merge(head)
                        else:
                            self.finish_head = head
                        continue

            else:
                position, layout_content = self._skipws(context, input_str,
                                                        position)
                tokens = next_tokens(state, input_str, position)
                if debug:
                    self._debug_context(
                        input_str, position, tokens,
                        expected_symbols=actions.keys(),
                        layout_content=layout_content)

            context.start_position = position
            context.layout_content = layout_content

            if not tokens:
                if debug:
                    # This head is dying
                    print("\t***Killing this head.")
                    if self.debug_trace:
                        self._trace_step_kill(head)

            for token in tokens:
                symbol = token.symbol
                symbol_actions = actions.get(symbol, [])

                # Do all reductions for this head and tokens
                context.symbol = symbol
                reduce_head = head.for_token(token)
                reduce_head.next_position = position
                reduce_head.next_layout_content = layout_content
                reduce_actions = [a for a in symbol_actions
                                  if a.action is REDUCE]
                for action in reduce_actions:
                    reduce(reduce_head, action.prod, token, context)

                symbol_act = symbol_actions[0] if symbol_actions else None
                if symbol_act and symbol_act.action is SHIFT:
                    self.add_to_heads_for_shift(reduce_head)
                elif not reduce_actions:
                    if self.error_recovery:
                        # If this head is not reduced and no shift is possible
                        # collect if for possible recovery.
                        self.heads_for_recovery.append(
                            (reduce_head, frozenset(actions.keys())))
                    elif debug:
                        print("\t** Killing head: {}".format(reduce_head))
                        if self.debug_trace:
                            self._trace_step_kill(reduce_head)

                if debug:
                    print("\n\tNo more reductions for this head and "
                          "lookahead token {}.".format(token))

    def _do_shifts(self, context):
        """Perform all shifts.

        Heads that are shifted successfully will be new candidates for
        reducing. If head is not shifted we have a dying head. They will be
        collected for error recovery if enabled.

        """
        debug = self.debug
        if self.debug:
            print("\n**SHIFTING HEADS")

        heads_for_shift = self.heads_for_shift
        input_str = self.input_str
        self.last_shifts = {}

        if self.debug:
            self._debug_active_heads(heads_for_shift)

        heads_for_shift.sort(key=lambda h: h.end_position)
        for head in heads_for_shift:
            if debug:
                print("\nShifting head: {}".format(str(head)))

            position = head.next_position
            layout_content = head.next_layout_content
            state = head.state
            actions = state.actions
            token = head.token_ahead

            context.start_position = position
            context.layout_content = layout_content
            context.symbol = symbol = token.symbol

            if debug:
                self._debug_context(input_str, position, token,
                                    expected_symbols=None,
                                    layout_content=layout_content)

            # First action should be SHIFT if it is possible to shift by this
            # token.
            action = actions.get(symbol, [None])[0]
            if action and action.action is SHIFT:
                if self.dynamic_filter and \
                    not self._call_dynamic_filter(
                            SHIFT, token, None, None, state):
                        pass
                else:
                    self.shift(head, token, action.state, context)
            else:
                # This should never happen as the shift possibility is checked
                # during reducing and only those heads that can be shifted are
                # appended to heads_for_shift
                assert False, "No shift operation possible."

    def reduce(self, head, production, token_ahead, context):
        """Executes reduce operation for the given head and production.
        """
        debug = self.debug
        context.production = production

        if debug:
            print("\n\t* Reducing by prod {}".format(production))

        prod_len = len(production.rhs)
        roots = []
        if not prod_len:
            if self.dynamic_filter and \
                not self._call_dynamic_filter(
                        REDUCE, token_ahead, production, [], head.state):
                    pass
            else:
                context.end_position = context.start_position
                new_state = head.state.gotos[production.symbol]
                new_head = GSSNode(
                    new_state,
                    start_position=context.start_position,
                    end_position=context.start_position,
                    layout_content=context.layout_content,
                    token_ahead=token_ahead)

                self.merge_create_head(new_head, head, head,
                                       context, [],
                                       True, True, production)
        else:
            # Find roots of new heads by going backwards for prod_len steps
            # following all possible paths.
            # Collect subresults along the way to be used with semantic actions
            to_process = [(head, [], prod_len, False, True)]
            if debug:
                print("\tCalculate reduction paths of length {}, "
                      "choose only non-empty if possible:"
                      .format(prod_len))
                print("\t\tstart node=[{}], symbol={}, empty=[{},{}], "
                      "length={}".format(head, head.state.symbol,
                                         head.any_empty,
                                         head.all_empty, prod_len))
            roots = []
            while to_process:
                node, subresults, length, path_has_empty, path_all_empty \
                    = to_process.pop()
                length = length - 1
                for parent, res, any_empty, all_empty in node.parents:
                    path_has_empty = path_has_empty or any_empty
                    path_all_empty = path_all_empty and all_empty
                    if debug:
                        print("\t\tnode=[{}], symbol={}, "
                              "any_empty={}, all_empty={}, length={}".format(
                                  parent, parent.state.symbol,
                                  path_has_empty, path_all_empty, length))
                    parent_subres = [res] + subresults
                    if length:
                        to_process.append(
                            (parent, parent_subres, length,
                             path_has_empty, path_all_empty))
                    else:
                        roots.append((parent, parent_subres,
                                      path_has_empty, path_all_empty))

            # Favour non-empty paths if exists or partialy empty.
            # In none of those exist use empty paths.
            non_empty = [r for r in roots if not r[2] and not r[3]]
            if non_empty:
                roots = non_empty
            else:
                non_empty = [r for r in roots if not r[3]]
                if non_empty:
                    roots = non_empty

            if debug:
                print("\n\tReduction roots = {}:".format(len(roots)))
                for r in roots:
                    print("\t\t{}".format(str(r[0])))

            # Create new heads.
            for idx, (root, subresults, any_empty, all_empty) \
                    in enumerate(roots):
                if debug:
                    print("\n\tReducing for root {}:".format(idx + 1))

                if self.dynamic_filter and \
                    not self._call_dynamic_filter(REDUCE, token_ahead,
                                                  production, subresults,
                                                  head.state):
                        pass
                else:
                    new_state = root.state.gotos[production.symbol]
                    new_head = GSSNode(new_state,
                                       start_position=root.next_position,
                                       end_position=head.end_position,
                                       layout_content=context.layout_content,
                                       token_ahead=token_ahead)
                    new_head.next_layout_content = head.next_layout_content
                    new_head.next_position = head.next_position

                    self.merge_create_head(new_head, head, root,
                                           context, subresults,
                                           any_empty, all_empty,
                                           production)
                if debug:
                    print()

        return bool(roots)

    def shift(self, head, token, state, context):
        """Execute shift operation at the given position to the given state.

        Shift token determined by the given state from input at given position
        and create the new head. Parents will be all nodes that had shift
        action with the given state at the given position.
        """

        last_shifts = self.last_shifts
        debug = self.debug
        context.symbol = token.symbol

        shifted_head = last_shifts.get((state.state_id,
                                        context.start_position, token.symbol),
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
                print("\n\tShift:{} \"{}\"".format(state.state_id,
                                                   token.value),
                      "at position",
                      pos_to_line_col(self.input_str, context.start_position))

            context.end_position = context.start_position + len(token)
            result = None
            sem_action = state.symbol.action
            if not sem_action:
                sem_action = self.sem_actions.get(state.symbol.name)
            if sem_action:
                result = sem_action(context, token.value)
            elif self.default_actions:
                result = default_shift_action(context, token.value)

            if debug:
                print("\tAction result = type:{} value:{}"
                      .format(type(result), repr(result)))

            new_head = GSSNode(
                state,
                start_position=context.start_position,
                end_position=context.end_position,
                layout_content=context.layout_content)

            # Cache this shift for further shift of the same symbol on the same
            # position.
            last_shifts[(state.state_id, context.start_position,
                         token.symbol)] = new_head

            self.heads_for_reduce.append(new_head)
            if debug:
                print("\tNew shifted head {}.".format(str(new_head)))
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

    def add_to_heads_for_shift(self, new_head):
        """Adds new head for shift or merges if already added."""
        for head in self.heads_for_shift:
            if head == new_head:
                if self.debug:
                    print("\tMerging head for shifting.")
                head.merge_head(new_head, self)
                break
        else:
            if self.debug:
                print("\n\tNew head for shifting: {}.".format(str(new_head)))
            self.heads_for_shift.append(new_head)

    def merge_create_head(self, new_head, old_head, root_head, context,
                          subresults, any_empty, all_empty, production):
        """Adds new head or merges if already exist on the stack. Executes semantic
        actions. Detects automata looping.
        """

        debug = self.debug

        def execute_actions(context, subresults):
            result = None
            sem_action = production.symbol.action
            if not sem_action:
                sem_action = self.sem_actions.get(production.symbol.name)
            if sem_action:
                if type(sem_action) is list:
                    result = sem_action[production.prod_symbol_id](context,
                                                                   subresults)
                else:
                    result = sem_action(context, subresults)
            elif self.default_actions:
                result = default_reduce_action(context, nodes=subresults)

            if debug:
                print("\tAction result = type:{} value:{}"
                      .format(type(result), repr(result)))
            return result

        if new_head == old_head:
            # Special case is reduction of empty production. For automata state
            # self-reference create stack node loop.
            if debug:
                print("\tLooping automata transition.")
            result = execute_actions(context, subresults)
            old_head.parents.append((old_head, result, True, True))

        if (all_empty or any_empty) and new_head in self.reducing_heads:
            # Detect automata loop. If we are reducing to the head we already
            # had and the new head is empty we have a loop due to EMPTY
            # reductions.
            if debug:
                print("\tAutomata loop detected. "
                      "Rejecting the new head: {}".format(str(new_head)))
            return

        result = execute_actions(context, subresults)
        for head in chain(self.heads_for_reduce,
                          [self.finish_head] if self.finish_head else []):
            if head == new_head:
                new_head.create_link(root_head, result, any_empty, all_empty,
                                     self)
                if head.merge_head(new_head, self):
                    if self.debug and self.debug_trace:
                        self._trace_step(old_head, head, root_head,
                                         "R:{}".format(
                                             dot_escape(str(production))))
                break
        else:
            self.heads_for_reduce.append(new_head)
            if self.debug:
                print("\tNew reduced head {}.".format(str(new_head)))
                if self.debug_trace:
                    self._trace_head(new_head, "{}:{}".format(
                        new_head.state.state_id,
                        dot_escape(new_head.state.symbol.name)))
            new_head.create_link(root_head, result, any_empty, all_empty, self)

            if self.debug and self.debug_trace:
                self._trace_step(old_head, new_head, root_head,
                                 "R:{}".format(dot_escape(str(production))))

    def _next_tokens(self, state, input_str, position):
        try:
            tok = super(GLRParser, self)._next_token(state, input_str,
                                                     position)
            tokens = [tok]
        except DisambiguationError as e:
            # Lexical ambiguity will be handled by GLR
            tokens = e.tokens

        return tokens

    def _do_recovery(self, context):
        """If recovery is enabled, does error recovery for the heads in
        heads_for_recovery.

        """
        debug = self.debug
        input_str = self.input_str
        for head, symbols in self.heads_for_recovery:
            if debug:
                print("\n\t**Error found. Recovery initiated for head {}."
                      .format(head))
                print("\tSymbols expected: {}".format(symbols))
            if context.start_position in self.recovery_results:
                position, token = self.recovery_results[context.start_position]
                if debug:
                    print("\tReusing cached recovery results.")
            else:
                if type(self.error_recovery) is bool:
                    # Default recovery
                    if debug:
                        print("\tDoing default error recovery.")
                    error, position, token = self.default_error_recovery(
                        input_str, context.start_position, set(symbols))
                else:
                    # Custom recovery provided during parser construction
                    if debug:
                        print("\tDoing custom error recovery.")
                    error, position, token = self.error_recovery(
                        self, input_str, context.start_position, set(symbols))

                if error:
                    self.errors.append(error)
                    if debug:
                        print("\tError: {}".format(str(error)))
                else:
                    # In GLR multiple heads may initiate recovery at the same
                    # position. If there is already error created at current
                    # position update expected symbols.
                    try:
                        last_error = self.errors[-1]
                        if last_error.expected_symbols and symbols:
                            last_error.expected_symbols.update(symbols)
                    except IndexError:
                        pass

                # Cache results
                self.recovery_results[context.start_position] = position, token

            if (position and position <= len(input_str)) or token is not None:
                assert not(position and token is not None), \
                    "Ambiguous recovery! Can't introduce new token and " \
                    "advance position at the same time."
                if position:
                    head.next_position = position
                    if debug:
                        print("\tAdvancing position to {}."
                              .format(pos_to_line_col(input_str, position)))
                elif debug:
                    print("\tIntroducing token {}.".format(repr(token)))

                head.token_ahead = token
                self.heads_for_reduce.append(head)
            else:
                if debug:
                    print("\tKilling head: {}".format(head))
                    if self.debug_trace:
                        self._trace_step_kill(head)

    def _debug_active_heads(self, heads):
        print("Active heads {}: {}".format(len(heads), heads))
        print("Number of trees = {}".format(
            sum([h.number_of_trees for h in heads])))

    def _debug_context(self, input_str, position, lookahead_tokens,
                       expected_symbols=None,
                       layout_content=''):
        print("\tPosition:", pos_to_line_col(input_str, position))
        print("\tContext:", position_context(input_str, position))
        lc = layout_content.replace("\n", "\\n") \
            if type(layout_content) is str else layout_content
        if layout_content:
            print("\tLayout: '{}'".format(lc))
        if expected_symbols:
            print("\tSymbols expected: {}".format(
                [s.name for s in expected_symbols]))
        print("\tToken(s) ahead: {}".format(lookahead_tokens))

    def _start_trace(self):
        self.dot_trace = ""
        self.trace_step = 1

    def _trace_head(self, new_head, label):
        self.dot_trace += '{} [label="{}"];\n'.format(new_head.key, label)

    def _trace_step(self, old_head, new_head, root_head, label=''):
        new_head_key = new_head.key if isinstance(new_head, GSSNode) \
                       else new_head
        self.dot_trace += '{} -> {} [label="{}. {}" {}];\n'.format(
            old_head.key, new_head_key, self.trace_step, label,
            TRACE_DOT_STEP_STYLE)
        self.dot_trace += '{} -> {};\n'.format(new_head_key, root_head.key)
        self.trace_step += 1

    def _trace_step_finish(self, from_head):
        self._trace_step(from_head, "success", from_head)

    def _trace_step_kill(self, from_head):
        self.dot_trace += '{}_killed [shape="diamond" label="killed"];\n'\
            .format(from_head.key)
        self.dot_trace += '{} -> {}_killed;\n'\
            .format(from_head.key, from_head.key)
        self.trace_step += 1

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

        print("Generated file {}.".format(file_name))
        print("You can use dot viewer or generate pdf with the "
              "following command:")
        print("dot -Tpdf {0} -O {0}.pdf".format(file_name))


class GSSNode(object):
    """Graphs Structured Stack node.

    Attributes:
        state(LRState):
        start_position, end_position(int):
        layout_content(str):
        any_empty(bool): If some of this node parent links results are empty.
        all_empty(bool): If all of this node parent link results are empty.
        parents(list): list of (parent GLRStackNode, result, any_empty,
             all_empty)
             Each stack node might have multiple parents which represent
             multiple path parse took to reach the current state. Each
             parent link keeps a result of semantic action executed during
             shift or reduce operation that created this node/link and the
             flag if any part of the result is obtained using epsilon/empty
             production.
        token_ahead(Token): Token recognized ahead at next_position in given
             state. Used with nodes created during reduction. Newly shift
             created nodes will have token_ahead set to None and will do
             scanning to obtain possible tokens ahead.
    """
    __slots__ = ['state', 'start_position', 'end_position', 'layout_content',
                 'parents', 'token_ahead', 'next_layout_content',
                 'next_position', 'any_empty', 'all_empty', 'number_of_trees',
                 '_hash']

    def __init__(self, state, start_position, end_position, layout_content='',
                 number_of_trees=0, token_ahead=None):
        self.state = state
        self.start_position = start_position
        self.end_position = end_position
        self.layout_content = layout_content

        # Initialize to neutral elements
        self.any_empty = False
        self.all_empty = True

        self.parents = []
        self.token_ahead = token_ahead

        # Parser state
        self.next_layout_content = ''
        self.next_position = end_position
        self.number_of_trees = number_of_trees

        self._hash = hash((self.state.state_id, self.start_position,
                           self.token_ahead))

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
                print("\tRejected merging of empty head: {}".format(other))
            return False
        else:
            if self.parents and other.less_empty(self):
                if parser.debug:
                    print("\tMerging less empty head to more empty -> "
                          "less empty head wins.")
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
                print("\tMerging head {} \n\t\tto head {}.".format(
                    str(other), str(self)))
            return True

    def create_link(self, parent, result, any_empty, all_empty, parser):
        self.parents.append((parent, result, any_empty, all_empty))
        self.number_of_trees += parent.number_of_trees
        self.any_empty |= any_empty
        self.all_empty &= all_empty
        if parser.debug:
            print("\tCreating link \tfrom head {}\n\t\t\tto head   {}"
                  .format(self, parent))

    def for_token(self, token):
        """Create head for the given token either by returning this head if the
        token is appropriate or making a clone.

        This is used to support lexical ambiguity. Multiple tokens might be
        matched at the same state and position. In this case parser should
        fork and this is done by cloning stack head.

        """
        if self.token_ahead == token:
            return self
        else:
            new_head = GSSNode(self.state,
                               self.start_position,
                               self.end_position,
                               self.layout_content,
                               self.number_of_trees)
            new_head.parents = list(self.parents)
            new_head.token_ahead = token
            new_head.any_empty = self.any_empty
            new_head.all_empty = self.all_empty
            new_head.next_layout_content = self.next_layout_content
            new_head.next_position = self.next_position
            return new_head

    def __eq__(self, other):
        """Stack nodes are equal if they are on the same position in the same state for
        the same lookahead token.

        """
        return self.state.state_id == other.state.state_id \
            and self.start_position == other.start_position \
            and self.token_ahead == other.token_ahead

    def __ne__(self, other):
        return not self == other

    def __str__(self):
        return "state={}:{}, pos={}, endpos={}{}, empty=[{},{}], " \
            "parents={}, trees={}".format(
                self.state.state_id, self.state.symbol,
                self.start_position, self.end_position,
                ", token ahead={}".format(self.token_ahead)
                if self.token_ahead is not None else "",
                self.any_empty, self.all_empty, len(self.parents),
                self.number_of_trees)

    def __repr__(self):
        return str(self)

    def __hash__(self):
        return self._hash

    @property
    def key(self):
        """Head unique idenfier used for dot trace."""
        return "head_{}_{}_{}".format(self.state.state_id, self.start_position,
                                      self.end_position)


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
