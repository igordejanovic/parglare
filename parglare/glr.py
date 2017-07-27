from parglare import Parser
import codecs
from itertools import chain
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
            self._start_trace()

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

        if self.debug:
            self._trace_head(start_head, str(start_head.state.state_id))

        # The main loop
        while self.heads_for_reduce:
            self._do_reductions(context)
            if self.heads_for_shift:
                self._do_shifts(context)

        if not self.finish_head:
            if self.debug:
                self._export_dot_trace()
            raise ParseError(
                file_name, input_str, self.last_position,
                nomatch_error(self.expected))

        results = [x[1] for x in self.finish_head.parents]
        if self.debug:
            print("*** {} sucessful parse(s).".format(len(results)))
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

        while heads_for_reduce:
            head = heads_for_reduce.pop()
            if debug:
                print("Reducing head: {}".format(str(head)))

            position = head.next_position
            if position > self.last_position:
                self.last_position = position
                self.expected = set()

            state = head.state
            actions = state.actions
            self.expected.update(actions.keys())

            lookahead_token = head.token_ahead

            if lookahead_token:
                # If this head is reduced it can only continue to be reduced by
                # the same token ahead. Check if the head is final.
                if lookahead_token.symbol is STOP:
                    symbol_action = actions.get(lookahead_token.symbol, None)
                    if symbol_action and symbol_action[0].action is ACCEPT:
                        if debug:
                            print("\t*** SUCCESS!!!!")
                            self._trace_link_finish(head)
                        self.finish_head = head
                layout_content = head.next_layout_content
                position = head.next_position
                tokens = [lookahead_token]
                if debug:
                    self._debug_context(
                        input_str, position, lookahead_token,
                        expected_symbols=[lookahead_token.symbol],
                        layout_content=layout_content)

            else:
                position, layout_content = self._skipws(context, input_str,
                                                        position)
                tokens = next_tokens(state, input_str, position)
                if debug:
                    self._debug_context(
                        input_str, position, lookahead_token,
                        expected_symbols=actions.keys(),
                        layout_content=layout_content)

            context.start_position = position
            context.layout_content = layout_content

            if not tokens:
                if debug:
                    # This head is dying
                    print("\t***Killing this head.")
                    self._trace_link_kill(head, "no actions")

            for token in tokens:
                symbol = token.symbol

                # Do all reductions for this head and tokens
                context.symbol = symbol
                reduce_head = head.for_token(token)
                reduce_head.next_position = position
                reduce_head.next_layout_content = layout_content
                reduce_actions = (a for a in actions.get(symbol, [])
                                  if a.action is REDUCE)
                for action in reduce_actions:
                    reduce(reduce_head, action.prod, token, context)

                symbol_act = actions.get(token.symbol, [None])[0]
                if symbol_act and symbol_act.action is SHIFT:
                    self.add_to_heads_for_shift(reduce_head)

                if debug:
                    print("\tNo more reductions for lookahead token {}."
                          .format(token))

    def _do_shifts(self, context):
        """
        Perform all shifts.
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
                print("Shifting head: {}".format(str(head)))

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
            if action:
                if action.action is SHIFT:
                    self.shift(head, token, action.state, context)
                elif action.action is REDUCE:
                    if debug:
                        # This head is dying
                        print("\t***Killing this head.")
                        self._trace_link_kill(
                            head, "can't shift {}".format(symbol))

    def reduce(self, head, production, token_ahead, context):
        """Executes reduce operation for the given head and production.
        """
        debug = self.debug
        sem_actions = self.sem_actions
        context.production = production

        if debug:
            print("\tReducing by prod {}".format(production))

        def execute_actions(context, subresults):
            result = None
            sem_action = sem_actions.get(production.symbol.name)
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

        prod_len = len(production.rhs)
        roots = []
        if not prod_len:
            # Special case is reduction of empty production.
            # We cache empty reduction in order to reuse semantic result
            # and to prevent infinite loops. For automata state self-reference
            # create stack node loop.
            result = self.empty_reductions_results.get(
                (head.state.state_id, production.prod_id), None)
            if not result:
                if debug:
                    print("\tEmpty production '{}' execute and cache cache."
                          .format(str(production)))
                context.end_position = context.start_position
                result = execute_actions(context, [])
                self.empty_reductions_results[
                    (head.state.state_id, production.prod_id)] = result
                new_state = head.state.gotos[production.symbol]
                if new_state == head.state:
                    if debug:
                        print("\tLooping automata transition.")
                    head.parents.append((head, result, True, True))
                else:
                    new_head = GSSNode(
                        new_state,
                        start_position=context.start_position,
                        end_position=context.start_position,
                        layout_content=context.layout_content)
                    new_head.token_ahead = token_ahead

                    self.merge_create_head(new_head, head, head, result,
                                           True, True, production)
        else:
            # Find roots of new heads by going backwards for prod_len steps
            # following all possible paths.
            # Collect subresults along the way to be used with semantic actions
            to_process = [(head, [], prod_len, False, True)]
            if debug:
                print("\tCalculate stack back paths of lenght {}, "
                      "choose only non-epsilon if possible:"
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
                print("\tRoots {}: {}".format(len(roots), roots))

            # Create new heads. Execute semantic actions.
            for root, subresults, any_empty, all_empty in roots:
                context.start_position = root.next_position
                context.end_position = head.end_position
                result = execute_actions(context, subresults)
                new_state = root.state.gotos[production.symbol]
                new_head = GSSNode(new_state,
                                   start_position=root.next_position,
                                   end_position=head.end_position,
                                   layout_content=context.layout_content)
                new_head.token_ahead = token_ahead
                new_head.next_layout_content = head.next_layout_content
                new_head.next_position = head.next_position

                self.merge_create_head(new_head, head, root, result,
                                       any_empty, all_empty,
                                       production)

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
        else:

            if self.debug:
                print("\tShift:{} \"{}\"".format(state.state_id, token.value),
                      "at position",
                      pos_to_line_col(self.input_str, context.start_position))

            context.end_position = context.start_position + len(token.value)
            result = None
            if state.symbol.name in self.sem_actions:
                result = self.sem_actions[state.symbol.name](context,
                                                             token.value)
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
                self._trace_head(new_head,
                                 "{}:{}".format(state.state_id,
                                                dot_escape(state.symbol.name)))
                self._trace_link(head, new_head,
                                 "S:{}".format(
                                     dot_escape(token.symbol.name)))

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
                print("\tNew head for shifting: {}.".format(str(new_head)))
            self.heads_for_shift.append(new_head)

    def merge_create_head(self, new_head, old_head, root_head, result,
                          any_empty, all_empty, production):
        """Adds new nead or merges if already exist on the stack."""

        new_head.create_link(root_head, result, any_empty, all_empty, self)
        for head in chain(self.heads_for_reduce,
                          [self.finish_head] if self.finish_head else []):
            if head == new_head:
                head.merge_head(new_head, self)
                break
        else:
            self.heads_for_reduce.append(new_head)
            if self.debug:
                print("\tNew reduced head {}.".format(str(new_head)))
                self._trace_head(new_head, "{}:{}".format(
                        new_head.state.state_id,
                        dot_escape(new_head.state.symbol.name)))
                self._trace_link(old_head, new_head,
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

    def _debug_active_heads(self, heads):
        print("Active heads {}: {}".format(len(heads), heads))
        print("Number of trees = {}".format(
            sum([h.number_of_trees for h in heads])))

    def _debug_context(self, input_str, position, lookahead_token,
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
        print("\tToken ahead: {}".format(lookahead_token))

    def _start_trace(self):
        self.dot_trace = ""
        self.trace_step = 1

    def _trace_head(self, new_head, label):
        self.dot_trace += '{} [label="{}"];\n'.format(new_head.key, label)

    def _trace_link(self, from_head, to_head, label):
        self.dot_trace += '{} -> {} [label="{} {}"];\n'.format(
            from_head.key, to_head.key, self.trace_step, label)
        self.trace_step += 1

    def _trace_link_finish(self, from_head):
        self.dot_trace += '{} -> success [label="{}"];\n'.format(
            from_head.key, self.trace_step)
        self.trace_step += 1

    def _trace_link_kill(self, from_head, label):
        self.dot_trace += '{} -> killed [label="{} {}"];\n'.format(
            from_head.key, self.trace_step, label)
        self.trace_step += 1

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
        parents(list): list of (result, parent GLRStackNode, epsilon)
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
                 'next_position', 'any_empty', 'all_empty', 'number_of_trees']

    def __init__(self, state, start_position, end_position, layout_content='',
                 number_of_trees=0):
        self.state = state
        self.start_position = start_position
        self.end_position = end_position
        self.layout_content = layout_content

        # Initialize to neutral elements
        self.any_empty = False
        self.all_empty = True

        self.parents = []
        self.token_ahead = None

        # Parser state
        self.next_layout_content = ''
        self.next_position = end_position
        self.number_of_trees = number_of_trees

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
        else:
            if self.parents and other.less_empty(self):
                if parser.debug:
                    print("\tMerging less empty head to more empty -> "
                          "droping all parent links.")
                self.parents = []
                self.number_of_trees = 0

            self.any_empty |= other.any_empty
            self.all_empty &= other.all_empty
            self.number_of_trees += other.number_of_trees
            self.parents.extend(other.parents)

            if parser.debug:
                print("\tMerging head {} \n\t\tto head {}.".format(
                    str(other), str(self)))
                parser._trace_link(other, self,
                                   "R-merge:{}".format(
                                     dot_escape(self.state.symbol.name)))

    def create_link(self, parent, result, any_empty, all_empty, parser):
        self.parents.append((parent, result, any_empty, all_empty))
        self.number_of_trees += parent.number_of_trees
        self.any_empty |= any_empty
        self.all_empty &= all_empty
        if parser.debug:
            print("\tCreating link \tfrom head {}\n\t\t\tto head   {}"
                  .format(self, parent))
            parser._trace_link(parent, self,
                               "S-reuse:{}".format(
                                   dot_escape(self.state.symbol.name)))

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
                if self.token_ahead else "",
                self.any_empty, self.all_empty, len(self.parents),
                self.number_of_trees)

    def __repr__(self):
        return str(self)

    @property
    def key(self):
        """Head unique idenfier used for dot trace."""
        return "head_{}_{}".format(self.state.state_id, self.start_position)


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
