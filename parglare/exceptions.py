class GrammarError(Exception):
    pass


def pos_to_line_col(input_str, position):
    line = 1
    old_pos = 0
    try:
        cur_pos = input_str.index("\n")
        while cur_pos < position:
            old_pos = cur_pos
            cur_pos = input_str.index("\n", cur_pos + 1)
            line += 1
    except ValueError:
        pass

    return line, position - old_pos


class ParseError(Exception):
    def __init__(self, input_str, position, symbols):
        self.position = position
        self.symbols = symbols
        self.line, self.column = pos_to_line_col(input_str, position)
        context = input_str[position-10:position] + "*" \
            + input_str[position:position+10]
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
