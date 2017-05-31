class GLRStack(object):
    """
    A data structure representing a forkable stack from Tomita's paper.

    Attributes:
        heads(list of GLRStackNode)
    """
    def __init__(self):
        self.heads = []

    def reduce(self, head, production):
        """Executes reduce operation for the given head and production.

        Reduces given head by the production determined by the given token.
        Creates new head. Remove action from current head. If head has no more
        actions it is removed from heads list. The given token shall be the
        only token ahead of the new head. Try to merge new head if the same
        head exists. Execute reduce semantic action.
        """

    def shift(self, position, state):
        """Execute shift operation at the given position to the given state.

        Shift token determined by the given state from input at given position
        and create the new head. Parents will be all nodes that had shift
        action with the given state at the given position.
        """


class GLRStackNode(object):
    """
    Attributes:
        state(LRState):
        position(int):
        parents_production(dict): { production: parent GLRStackNode}
             Each stack node might have multiple parents which represent
             multiple path parses took to reach the current state.
        tokens_ahead(list of Token): A list of tokens recognized in the
             input in the current state and position.
        actions(list of lists of Action): Possible actions for each token.
    """
    def __init__(self, state, position):
        self.state = state
        self.position = position
        self.parents_production = {}
        self.tokens_ahead = []
        self.actions = []
