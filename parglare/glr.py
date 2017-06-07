from parglare import Parser
from .exceptions import DisambiguationError, ParseError, nomatch_error
from .parser import position_context, SHIFT, REDUCE, ACCEPT, \
    default_reduce_action, default_shift_action, pos_to_line_col


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

        # We start with a single parser head in state 0.
        self.heads = [GSSNode(self.table.states[0], position)]
        self.input_str = input_str
        context = type(str("Context"), (), {})
        context.debug = self.debug
        results = []

        self.last_shifts = {}

        while self.heads:

            self.heads.sort(key=lambda x: x.position, reverse=True)

            if self.debug:
                print("Active heads {}: {}".format(len(self.heads),
                                                   self.heads))

            head = self.heads.pop()
            if self.debug:
                print("Current head: {}".format(str(head)))

            if head.position > position:
                self.last_shifts = {}

            position = head.position
            state = head.state
            actions = state.actions

            if head.token:
                tokens = [head.token]
            else:
                try:
                    token, position = \
                        self._next_token(state, input_str, position,
                                         context, True)
                    tokens = [token]
                except DisambiguationError as e:
                    # Lexical ambiguity will be handled by GLR
                    tokens = e.tokens
                    position = e.position

                head.position = position

            if self.debug:
                print("\tPosition:", pos_to_line_col(input_str, position))
                print("\tContext:", position_context(input_str, position))
                print("\tExpecting: {}".format(
                    [x.name for x in actions.keys()]))
                print("\tTokens ahead: {}".format(tokens))

            context.position = position

            for token in tokens:
                symbol = token.symbol
                if symbol not in actions:
                    # This head is dying
                    if self.debug:
                        print("\t***Killing this head.")

                    if not self.heads:
                        # Last head got killed. Report parsing error.
                        raise ParseError(file_name, input_str, position,
                                         nomatch_error([x for x in actions]))

                    break
                # Do all reductions for this head and token
                context.symbol = symbol
                for action in (a for a in actions[symbol]
                               if a.action is REDUCE):
                    self.reduce(head, action.prod, token, context)

                # If there is shift action for this token do it.
                action = actions[symbol][0]
                if action.action is SHIFT:
                    self.shift(head, token, action.state, context)

                elif action.action is ACCEPT:
                    print("\t*** SUCCESS!!!!")

        results = [x[1] for x in head.parents]
        if self.debug:
            print("*** {} sucessful parse(s).".format(len(results)))

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

        if context.debug:
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

        if self.debug:
            print("\tRoots {}: {}".format(len(roots), roots))

        # Create new heads. Execute semantic actions.
        for root, subresults in roots:
            new_state = root.state.gotos[production.symbol]

            new_head = GSSNode(new_state, context.position)
            new_head.token = token

            # Calling semantic actions
            res = None
            sem_action = self.sem_actions.get(production.symbol.name)
            if sem_action:
                if type(sem_action) is list:
                    res = sem_action[production.prod_symbol_id](context,
                                                                subresults)
                else:
                    res = sem_action(context, subresults)
            elif self.default_actions:
                res = default_reduce_action(context, nodes=subresults)

            if context.debug:
                print("\tAction result = type:{} value:{}"
                      .format(type(res), repr(res)))

            new_head.parents.append((root, res))
            self.merge_heads(new_head)

    def shift(self, head, token, state, context):
        """Execute shift operation at the given position to the given state.

        Shift token determined by the given state from input at given position
        and create the new head. Parents will be all nodes that had shift
        action with the given state at the given position.
        """

        last_shifts = self.last_shifts
        if state.state_id in last_shifts:
            # If this token has already been shifted connect
            # shifted head to this head.
            res = last_shifts[state.state_id].parents[0][1]
            last_shifts[state.state_id].parents.append((head, res))
            if self.debug:
                print("\tReusing shifted head {}.".format(
                    self.last_shifts[state.state_id]))

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

            if context.debug:
                print("\tAction result = type:{} value:{}"
                      .format(type(res), repr(res)))

            new_head = GSSNode(state,
                               position=context.position + len(token.value))
            new_head.parents = [(head, res)]

            # Cache this shift for further shift of the same symbol on the same
            # position.
            last_shifts[state.state_id] = new_head

            # Open question: Is it possible for this head to be
            # merged?
            self.heads.append(new_head)
            if self.debug:
                print("\tNew shifted head {}.".format(
                    str(new_head)))

    def merge_heads(self, new_head):
        for head in self.heads:
            if head == new_head:
                if self.debug:
                    print("\tMerging heads {}.".format(str(head)))
                head.parents.extend(new_head.parents)
                break
        else:
            self.heads.append(new_head)
            if self.debug:
                print("\tNew reduced head {}.".format(str(new_head)))


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
