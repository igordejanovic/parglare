from parglare import Parser
import codecs
from itertools import chain
from .exceptions import DisambiguationError, ParseError, nomatch_error
from .parser import position_context, SHIFT, REDUCE, ACCEPT, \
    default_reduce_action, default_shift_action, pos_to_line_col, \
    EMPTY_token
from .grammar import EMPTY
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
            print("*** Parsing started")
            self.dot_trace = 'killed [label="Killed"];\n'
            self.dot_trace += 'success [label="SUCCESS"];\n'
            self.trace_step = 1

        # We start with a single parser head in state 0.
        self.heads = [GSSNode(self.table.states[0], position)]
        self.input_str = input_str
        self.file_name = file_name
        self.finish_head = None
        self.last_shifts = {}
        context = type(str("Context"), (), {})

        # Prefething
        heads = self.heads
        debug = self.debug
        next_token = self._next_token
        shift = self.shift
        reduce = self.reduce

        if debug:
            self.dot_trace += '{} [label="{}"];\n'.format(
                heads[0].key, heads[0].state.state_id)

        while heads:

            heads.sort(key=lambda x: x.position, reverse=True)

            if debug:
                print("Active heads {}: {}".format(len(self.heads),
                                                   self.heads))

            head = heads.pop()
            if debug:
                print("Current head: {}".format(str(head)))

            if head.position > position:
                self.last_shifts = {}

            position = head.position
            state = head.state
            actions = state.actions

            if head.token:
                tokens = [head.token]
                if EMPTY in actions:
                    tokens.append(EMPTY_token)
            else:
                try:
                    token, position = \
                        next_token(state, input_str, position, context, True)
                    tokens = [token]
                except DisambiguationError as e:
                    # Lexical ambiguity will be handled by GLR
                    tokens = e.tokens
                    position = e.position

                head.position = position

            valid_tokens = [token for token in tokens
                            if token.symbol in actions]

            if debug:
                print("\tPosition:", pos_to_line_col(input_str, position))
                print("\tContext:", position_context(input_str, position))
                print("\tExpecting: {}".format(
                    [x.name for x in actions.keys()]))
                print("\tTokens ahead: {}".format(tokens))

            context.position = position

            tokens = valid_tokens
            if not tokens:
                if debug:
                    # This head is dying
                    print("\t***Killing this head.")
                    self.dot_trace += '{} -> killed [label="{}"];\n'.format(
                        head.key, self.trace_step)
                    self.trace_step += 1

            for token in tokens:
                symbol = token.symbol

                # Do all reductions for this head and token
                context.symbol = symbol
                for action in (a for a in actions[symbol]
                               if a.action is REDUCE):
                    reduce(head, action.prod, token, context)

                # If there is shift action for this token do it.
                action = actions[symbol][0]
                if action.action is SHIFT:
                    shift(head, token, action.state, context)

                elif action.action is ACCEPT:
                    if debug:
                        print("\t*** SUCCESS!!!!")
                        self.dot_trace += '{} -> success [label="{}"];\n'\
                            .format(head.key, self.trace_step)
                        self.trace_step += 1
                    self.finish_head = head

        if not self.finish_head:
            raise ParseError(file_name, input_str, position,
                             nomatch_error([x for x in actions]))

        results = [x[1] for x in self.finish_head.parents]
        if debug:
            print("*** {} sucessful parse(s).".format(len(results)))
            self._export_dot_trace()

        return results

    def reduce(self, head, production, token, context):
        """Executes reduce operation for the given head and production.

        Reduces given head by the production determined by the given token.
        Creates new head. Remove action from current head. If head has no more
        actions it is removed from heads list. The given token shall be the
        only token ahead of the new head. Try to merge new head if the same
        head exists. Execute reduce semantic action.
        """
        context.symbol = production.symbol
        debug = self.debug
        sem_actions = self.sem_actions

        if debug:
            print("\tReducing by prod {}".format(production))

        # Find roots of new heads
        # Collect subresults along the way to be used with semantic actions
        to_process = [(head, [], len(production.rhs))]
        roots = []
        while to_process:
            node, subresults, length = to_process.pop()
            length = length - 1
            for parent, res in node.parents:
                parent_subres = [res] + subresults
                if length:
                    to_process.append((parent, parent_subres, length))
                else:
                    roots.append((parent, parent_subres))

        if debug:
            print("\tRoots {}: {}".format(len(roots), roots))

        # Create new heads. Execute semantic actions.
        for root, subresults in roots:
            new_state = root.state.gotos[production.symbol]

            new_head = GSSNode(new_state, context.position)
            new_head.token = token

            # Calling semantic actions
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

            new_head.parents.append((root, res))
            self.merge_heads(new_head, head, production)

    def shift(self, head, token, state, context):
        """Execute shift operation at the given position to the given state.

        Shift token determined by the given state from input at given position
        and create the new head. Parents will be all nodes that had shift
        action with the given state at the given position.
        """

        last_shifts = self.last_shifts
        debug = self.debug

        shifted_head = last_shifts.get((state.state_id, context.position),
                                       None)
        if shifted_head:
            # If this token has already been shifted connect
            # shifted head to this head.
            res = shifted_head.parents[0][1]
            shifted_head.parents.append((head, res))
            if debug:
                print("\tReusing shifted head {}.".format(shifted_head))
                self.dot_trace += '{} -> {} [label="{} S-reuse:{}"];\n'.format(
                    head.key, shifted_head.key, self.trace_step,
                    dot_escape(state.symbol.name))
                self.trace_step += 1

        else:

            if self.debug:
                print("\tShift:{} \"{}\"".format(state.state_id, token.value),
                      "at position",
                      pos_to_line_col(self.input_str, context.position))

            res = None
            if state.symbol.name in self.sem_actions:
                res = self.sem_actions[state.symbol.name](context,
                                                          token.value)
            elif self.default_actions:
                res = default_shift_action(context, token.value)

            if debug:
                print("\tAction result = type:{} value:{}"
                      .format(type(res), repr(res)))

            new_head = GSSNode(state,
                               position=context.position + len(token.value))
            new_head.parents = [(head, res)]

            # Cache this shift for further shift of the same symbol on the same
            # position.
            last_shifts[(state.state_id, context.position)] = new_head

            # Open question: Is it possible for this head to be merged?
            self.heads.append(new_head)
            if debug:
                print("\tNew shifted head {}.".format(str(new_head)))
                self.dot_trace += '{} [label="{}:{}"];\n'.format(
                    new_head.key, state.state_id,
                    dot_escape(state.symbol.name))
                self.dot_trace += '{} -> {} [label="{} S:{}"];\n'.format(
                    head.key, new_head.key,
                    self.trace_step, dot_escape(token.symbol.name))
                self.trace_step += 1

    def merge_heads(self, new_head, old_head, production):
        for head in chain(self.heads,
                          [self.finish_head] if self.finish_head else []):
            if head == new_head:
                if self.debug:
                    print("\tMerging heads {}.".format(str(head)))
                    self.dot_trace += \
                        '{} -> {} [label="{} R-merge\:{}"];\n'.format(
                            old_head.key, head.key,
                            self.trace_step,
                            dot_escape(head.state.symbol.name))
                    self.trace_step += 1
                head.parents.extend(new_head.parents)
                break
        else:
            self.heads.append(new_head)
            if self.debug:
                print("\tNew reduced head {}.".format(str(new_head)))
                self.dot_trace += \
                    '{} [label="{}:{}"];\n'.format(
                        new_head.key, new_head.state.state_id,
                        dot_escape(new_head.state.symbol.name))
                self.dot_trace += \
                    '{} -> {} [label="{} R\:{}"];\n'.format(
                        old_head.key, new_head.key,
                        self.trace_step,
                        dot_escape(str(production)))
                self.trace_step += 1

    def _export_dot_trace(self):
        file_name = self.file_name if self.file_name else "parglare_trace.dot"
        with codecs.open(file_name, 'w', encoding="utf-8") as f:
            f.write(DOT_HEADER)
            f.write(self.dot_trace)
            f.write("}\n")


class GSSNode(object):
    """Graphs Structured Stack node.

    Attributes:
        state(LRState):
        position(int):
        parents(list): list of (result, parent GLRStackNode)
             Each stack node might have multiple parents which represent
             multiple path parse took to reach the current state. Each
             parent link keeps a result of semantic action executed during
             shift or reduce operation that created this node/link.
        token(Token): Token recognized at given position in given state.
             Used with nodes created during reduction. Shift created nodes
             will have token set to None and will do scanning to obtain
             possible tokens ahead.
    """
    __slots__ = ['state', 'position', 'parents', 'token']

    def __init__(self, state, position):
        self.state = state
        self.position = position
        self.parents = []
        self.token = None

    def __eq__(self, other):
        """Stack nodes are equal if they are on the same position in the same state.
        """
        return self.position == other.position and self.state == other.state

    def __ne__(self, other):
        return not self == other

    def __str__(self):
        return "state={} position={}".format(self.state.state_id,
                                             self.position)

    def __repr__(self):
        return str(self)

    @property
    def key(self):
        """Head unique idenfier"""
        return 100000000 * self.state.state_id + self.position


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
