class GrammarError(Exception):
    pass


class ParseError(Exception):
    def __init__(self, file_name, input_str, position, message_factory):
        from parglare.parser import pos_to_line_col
        self.file_name = file_name
        self.position = position
        self.line, self.column = pos_to_line_col(input_str, position)
        super(ParseError, self).__init__(
            message_factory(file_name, input_str, position))


# Error message factories
def _full_context(input_str, position):
    from parglare.parser import pos_to_line_col, position_context
    line, column = pos_to_line_col(input_str, position)
    context = position_context(input_str, position)
    return context, line, column


def nomatch_error(symbols):
    def _inner(file_name, input_str, position):
        context, line, column = _full_context(input_str, position)
        return 'Error {}at position {},{} => "{}". Expected: {}'.format(
                'in file "{}" '.format(file_name)
                if file_name else "",
                line, column, context,
                ' or '.join([s.name for s in symbols]))
    return _inner


def disambiguation_error(symbols):
    def _inner(file_name, input_str, position):
        context, line, column = _full_context(input_str, position)
        return 'Error {}at position {},{} => "{}". ' \
            'Can\'t disambiguate between: {}'.format(
                'in file "{}" '.format(file_name)
                if file_name else "",
                line, column, context,
                ' or '.join([s.name for s in symbols]))
    return _inner


class ParserInitError(Exception):
    pass


class DisambiguationError(Exception):
    def __init__(self, symbols):
        self.symbols = symbols


class LRConflict(Exception):
    def __init__(self, message, state, symbols):
        self.state = state
        self.symbols = symbols
        super(LRConflict, self).__init__(message)


class ShiftReduceConflict(LRConflict):
    def __init__(self, state, symbols, production):
        self.production = production
        message = "{}\nIn state {} and input symbol {} can't " \
                  "decide whether to shift or reduce by production '{}'." \
            .format(str(state), state.state_id, symbols, production)
        super(ShiftReduceConflict, self).__init__(message, state, symbols)


class ReduceReduceConflict(LRConflict):
    def __init__(self, state, symbols, production1, production2):
        self.production1 = production1
        self.production2 = production2
        message = "{}\nIn state {} and input symbol(s) {} can't " \
                  "decide whether to reduce by production '{}' or by '{}'." \
            .format(str(state), state.state_id, symbols,
                    production1, production2)
        super(ReduceReduceConflict, self).__init__(message, state, symbols)


class NoActionsForStartRule(Exception):
    def __init__(self):
        super(NoActionsForStartRule, self).__init__(
            "No SHIFT actions for start rule. Your start rule is probably "
            "infinitely recursive.")
