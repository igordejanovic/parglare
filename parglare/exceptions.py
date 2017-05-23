class GrammarError(Exception):
    pass


class ParseError(Exception):
    def __init__(self, file_name, input_str, position, symbols):
        from parglare.parser import pos_to_line_col, position_context
        self.file_name = file_name
        self.position = position
        self.symbols = symbols
        self.line, self.column = pos_to_line_col(input_str, position)
        context = position_context(input_str, position)
        super(ParseError, self).__init__(
            'Error {}at position {},{} => "{}". Expected: {}'.format(
                'in file "{}" '.format(self.file_name)
                if self.file_name else "",
                self.line, self.column, context,
                ' or '.join([s.name for s in symbols])))


class ParserInitError(Exception):
    pass


class LRConflict(Exception):
    def __init__(self, message, state, symbol):
        self.state = state
        self.symbol = symbol
        super(LRConflict, self).__init__(message)


class ShiftReduceConflict(LRConflict):
    def __init__(self, state, symbol, production):
        self.production = production
        message = "In state {} and input symbol '{}' can't " \
                  "decide whether to shift or reduce by production '{}'." \
            .format(state.state_id, symbol, production)
        super(ShiftReduceConflict, self).__init__(message, state, symbol)


class ReduceReduceConflict(LRConflict):
    def __init__(self, state, symbol, production1, production2):
        self.production1 = production1
        self.production2 = production2
        message = "In state {} and input symbol '{}' can't " \
                  "decide whether to reduce by production '{}' or by '{}'." \
            .format(state.state_id, symbol, production1, production2)
        super(ReduceReduceConflict, self).__init__(message, state, symbol)


class NoActionsForStartRule(Exception):
    def __init__(self):
        super(NoActionsForStartRule, self).__init__(
            "No SHIFT actions for root rule. Is your root rule infinitely "
            "recursive?")
