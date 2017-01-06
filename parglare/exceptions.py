class ParseError(Exception):
    def __init__(self, position, symbols):
        self.position = position
        self.symbols = symbols
        super(ParseError, self).__init__(
            "Error at position %d. Expected: %s" %
            (position, " or ".join([s.name for s in symbols])))


class ParserInitError(Exception):
    pass


class ShiftReduceConflict(Exception):
    def __init__(self, state, symbol, production):
        self.state = state
        self.symbol = symbol
        self.production = production
        super(ShiftReduceConflict, self).__init__(
            "In state {} and symbol '{}' on the input can't decide whether "
            "to shift or reduce by production '{}'."
            .format(state.state_id, symbol, production))
