from parglare import Parser
import codecs
from itertools import chain
from .exceptions import DisambiguationError, ParseError, nomatch_error
from .parser import position_context, SHIFT, REDUCE, ACCEPT, \
    default_reduce_action, default_shift_action, pos_to_line_col, \
    STOP, STOP_token, Token
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

    def parse(self, input_str, position=0, file_name=None):
        """
        Parses the given input string.
        Args:
            input_str(str): A string to parse.
            position(int): Position to start from.
            file_name(str): File name if applicable. Used in error reporting.
        """

        if self.debug:
            print("\n*** PARSING STARTED\n")
            self._start_trace()

        self.last_position = 0
        self.expected = set()
        self.empty_reductions_res = {}
        position, layout_content = self._skipws(input_str, position)

        # We start with a single parser head in state 0.
        start_head = GSSNode(self.table.states[0],
                             start_position=position,
                             end_position=position,
                             layout_content=layout_content,
                             empty=False,
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
            self._do_reductions()
            if self.heads_for_shift:
                self._do_shifts()

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

    def _do_reductions(self):
        """
        Reduces active heads until no more heads can be reduced.
        """
        debug = self.debug
        if debug:
            print("\n**REDUCING HEADS")
            print("Active heads {}: {}".format(len(self.heads_for_reduce),
                                               self.heads_for_reduce))
            print("Number of trees = {}".format(
                sum([h.number_of_trees for h in self.heads_for_reduce])))
        context = type(str("Context"), (), {})
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
                    print("\tPosition:", pos_to_line_col(input_str, position))
                    print("\tContext:", position_context(input_str, position))
                    print("\tLayout: '{}'".format(
                        layout_content.replace("\n", "\\n")))
                    print("\tLookahead token: {}".format(lookahead_token))

            else:
                position, layout_content = self._skipws(input_str,
                                                        position)
                tokens = next_tokens(state, input_str, position)
                if debug:
                    print("\tContext:", position_context(input_str, position))
                    print("\tTokens expected: {}".format(
                        [a.name for a in actions]))
                    print("\tTokens ahead: {}".format(tokens))

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

    def _do_shifts(self):
        """
        Perform all shifts.
        """
        debug = self.debug
        if self.debug:
            print("\n**SHIFTING HEADS")

        heads_for_shift = self.heads_for_shift
        input_str = self.input_str
        context = type(str("Context"), (), {})
        self.last_shifts = {}

        if self.debug:
            print("Active heads {}: {}".format(len(heads_for_shift),
                                               heads_for_shift))
            print("Number of trees = {}".format(
                sum([h.number_of_trees for h in self.heads_for_shift])))

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
                print("\tPosition:", pos_to_line_col(input_str, position))
                print("\tContext:", position_context(input_str, position))
                print("\tLayout: '{}'".format(
                    layout_content.replace("\n", "\\n")))
                print("\tLookahead token: {}".format(token))

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

        if debug:
            print("\tReducing by prod {}".format(production))

        def execute_actions(context, subresults):
            res = None
            sem_action = sem_actions.get(production.symbol.name)
            if sem_action:
                if type(sem_action) is list:
                    res = sem_action[production.prod_symbol_id](context,
                                                                subresults)
                else:
                    res = sem_action(context, subresults)
            elif self.default_actions:
                res = default_reduce_action(context, nodes=subresults)

            if debug:
                print("\tAction result = type:{} value:{}"
                      .format(type(res), repr(res)))
            return res

        prod_len = len(production.rhs)
        roots = []
        if not prod_len:
            # Special case is reduction of empty production.
            # We cache empty reduction in order to reuse semantic result
            # and to prevent infinite loops.
            res = self.empty_reductions_res.get(
                (head.state.state_id, production.prod_id), None)
            if not res:
                if debug:
                    print("\tEmpty production '{}' execute and cache cache."
                          .format(str(production)))
                context.end_position = context.start_position
                res = execute_actions(context, [])
                self.empty_reductions_res[
                    (head.state.state_id, production.prod_id)] = res
                new_state = head.state.gotos[production.symbol]
                if new_state == head.state:
                    if debug:
                        print("\tLooping automata transition.")
                    head.parents.append((head, res))
                else:
                    new_head = GSSNode(
                        new_state,
                        start_position=context.start_position,
                        end_position=context.start_position,
                        layout_content=context.layout_content,
                        empty=True)
                    new_head.token_ahead = token_ahead

                    self.merge_create_head(new_head, head, head, res,
                                           production)
        else:
            # Find roots of new heads
            # Collect subresults along the way to be used with semantic actions
            to_process = [(head, [], prod_len, head.empty, head.empty)]
            if debug:
                print("\tCalculate stack back paths of lenght {}, "
                      "choose only non-epsilon if possible:"
                      .format(prod_len))
                print("\t\tstart node=[{}], symbol={}, empty={}, length={}"
                      .format(head, head.state.symbol, head.empty, prod_len))
            roots = []
            while to_process:
                node, subresults, length, path_has_empty, path_all_empty \
                    = to_process.pop()
                length = length - 1
                for parent, res in node.parents:
                    path_has_empty = path_has_empty or parent.empty
                    path_all_empty = path_all_empty and parent.empty
                    if debug:
                        print("\t\tnode=[{}], symbol={}, "
                              "has_empty={}, all_empty={}, length={}".format(
                                  parent, parent.state.symbol,
                                  path_has_empty, path_all_empty, length))
                    parent_subres = [res] + subresults
                    if length:
                        to_process.append(
                            (parent, parent_subres, length,
                             path_has_empty, path_all_empty))
                    else:
                        roots.append((parent, parent_subres, path_all_empty))

            # Eliminate emtpy paths if non-empty exists.
            # First eliminate paths that has at least one subnode empty.
            # If that fails, eliminate nodes that have all subnodes empty.
            non_epsilon = [r for r in roots if not r[2]]
            if non_epsilon:
                roots = non_epsilon
            else:
                non_epsilon = [r for r in roots if not r[3]]
                if non_epsilon:
                    roots = non_epsilon

            if debug:
                print("\tRoots {}: {}".format(len(roots), roots))

            # Create new heads. Execute semantic actions.
            for root, subresults, empty in roots:
                context.start_position = root.next_position
                context.end_position = head.end_position
                res = execute_actions(context, subresults)
                new_state = root.state.gotos[production.symbol]
                new_head = GSSNode(new_state,
                                   start_position=root.next_position,
                                   end_position=head.end_position,
                                   layout_content=context.layout_content,
                                   empty=empty)
                new_head.token_ahead = token_ahead
                new_head.next_layout_content = head.next_layout_content
                new_head.next_position = head.next_position

                self.merge_create_head(new_head, head, root, res, production)

        return bool(roots)

    def shift(self, head, token, state, context):
        """Execute shift operation at the given position to the given state.

        Shift token determined by the given state from input at given position
        and create the new head. Parents will be all nodes that had shift
        action with the given state at the given position.
        """

        last_shifts = self.last_shifts
        debug = self.debug

        shifted_head = last_shifts.get((state.state_id,
                                        context.start_position, token.symbol),
                                       None)
        if shifted_head:
            # If this token has already been shifted connect
            # shifted head to this head.
            res = shifted_head.parents[0][1]
            shifted_head.create_link(head, res, self)
        else:

            if self.debug:
                print("\tShift:{} \"{}\"".format(state.state_id, token.value),
                      "at position",
                      pos_to_line_col(self.input_str, context.start_position))

            context.end_position = context.start_position + len(token.value)
            res = None
            if state.symbol.name in self.sem_actions:
                res = self.sem_actions[state.symbol.name](context,
                                                          token.value)
            elif self.default_actions:
                res = default_shift_action(context, token.value)

            if debug:
                print("\tAction result = type:{} value:{}"
                      .format(type(res), repr(res)))

            new_head = GSSNode(
                state,
                start_position=context.start_position,
                end_position=context.end_position,
                layout_content=context.layout_content,
                empty=False)

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

            new_head.create_link(head, res, self)

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
                          production):
        new_head.create_link(root_head, result, self)
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
        """
        For the current position in the input stream and actions in the current
        state find next token.
        """

        actions = state.actions
        finish_flags = state.finish_flags

        in_len = len(input_str)

        tokens = []
        for idx, symbol in enumerate(actions):
            tok = symbol.recognizer(input_str, position)
            if tok:
                tokens.append(Token(symbol, tok))
                if finish_flags[idx]:
                    break

        if len(tokens) > 1:
            try:
                tok = self._lexical_disambiguation(tokens)
                tokens = [tok]
            except DisambiguationError as e:
                # Lexical ambiguity will be handled by GLR
                tokens = e.tokens

        # tokens.append(EMPTY_token)
        if position == in_len:
            tokens.append(STOP_token)

        return tokens

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
        empty(bool): If this node represents empty/epsilon tree.
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
                 'next_position', 'empty', 'number_of_trees']

    def __init__(self, state, start_position, end_position, layout_content='',
                 empty=False, number_of_trees=0):
        self.state = state
        self.start_position = start_position
        self.end_position = end_position
        self.layout_content = layout_content
        self.empty = empty

        self.parents = []
        self.token_ahead = None

        # Parser state
        self.next_layout_content = ''
        self.next_position = end_position
        self.number_of_trees = number_of_trees

    def merge_head(self, other, parser):
        # Reject mergin if other node is empty and this is not
        if other.empty and not self.empty:
            if parser.debug:
                print("\tRejected merging of empty head: {}".format(other))
        else:
            if self.parents and not other.empty and self.empty:
                if parser.debug:
                    print("\tMerging non-empty head to empty -> droping all "
                          "parent links.")
                self.parents = []
                self.number_of_trees = 0
                self.empty = False
            self.parents.extend(other.parents)
            self.number_of_trees += other.number_of_trees
            if parser.debug:
                print("\tMerging head {} \n\t\tto head {}.".format(
                    str(other), str(self)))
                parser._trace_link(other, self,
                                   "R-merge:{}".format(
                                     dot_escape(self.state.symbol.name)))

    def create_link(self, parent, result, parser):
        if self.parents and parent.empty and not self.empty:
            if parser.debug:
                print("\tRejected linking of empty head: {}".format(parent))
        else:
            if self.parents and not parent.empty and self.empty:
                if parser.debug:
                    print("\tLinking non-empty head to empty -> droping all "
                          "parent links.")
                self.parents = []
                self.number_of_trees = 0
                self.empty = False

            self.parents.append((parent, result))
            self.number_of_trees += parent.number_of_trees
            if parser.debug:
                print("\tCreating link to {}.".format(self))
                parser._trace_link(parent, self,
                                   "S-reuse:{}".format(
                                     dot_escape(self.state.symbol.name)))

    def for_token(self, token):
        """Create head for the given token either by returning this head if the
        token is appropriate or making a clone.
        """
        if self.token_ahead == token:
            return self
        else:
            new_head = GSSNode(self.state,
                               self.start_position,
                               self.end_position,
                               self.layout_content,
                               self.empty,
                               self.number_of_trees)
            new_head.parents = list(self.parents)
            new_head.token_ahead = token
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
        return "state={}:{}, pos={}, endpos={}{}, empty={}, parents={}, trees={}".format(
            self.state.state_id, self.state.symbol,
            self.start_position, self.end_position,
            ", token ahead={}".format(self.token_ahead)
            if self.token_ahead else "",
            self.empty, len(self.parents), self.number_of_trees)

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
