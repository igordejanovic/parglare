class GrammarError(Exception):
    pass


class ParseError(Exception):
    def __init__(self, input_str, position, symbols):
        from parglare.parser import pos_to_line_col, position_context
        self.position = position
        self.symbols = symbols
        self.line, self.column = pos_to_line_col(input_str, position)
        context = position_context(input_str, position)
        super(ParseError, self).__init__(
            "Error at position %d,%d => \"%s\". Expected: %s" %
            (self.line, self.column, context,
             " or ".join([s.name for s in symbols])))


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
