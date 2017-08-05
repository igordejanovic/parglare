from __future__ import unicode_literals


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


def disambiguation_error(tokens):
    def _inner(file_name, input_str, position):
        context, line, column = _full_context(input_str, position)
        return 'Error {}at position {},{} => "{}". ' \
            'Can\'t disambiguate between: {}'.format(
                'in file "{}" '.format(file_name)
                if file_name else "",
                line, column, context,
                ' or '.join([str(t) for t in tokens]))
    return _inner


class ParserInitError(Exception):
    pass


class DisambiguationError(Exception):
    def __init__(self, tokens):
        self.tokens = tokens


class LRConflict(object):
    def __init__(self, message, state, term, productions):
        self.message = message
        self.state = state
        self.term = term
        self.productions = productions


class SRConflict(LRConflict):
    def __init__(self, state, term, productions):
        prod_str = " or ".join(["'{}'".format(str(p))
                                for p in productions])
        message = "{}\nIn state {} and input symbol '{}' can't " \
                  "decide whether to shift or reduce by production(s) {}." \
            .format(str(state), state.state_id, term, prod_str)
        super(SRConflict, self).__init__(message, state, term, productions)


class RRConflict(LRConflict):
    def __init__(self, state, term, productions):
        prod_str = " or ".join(["'{}'".format(str(p))
                                for p in productions])
        message = "{}\nIn state {} and input symbol '{}' can't " \
                  "decide which reduction to perform: {}." \
                  .format(str(state), state.state_id, term, prod_str)
        super(RRConflict, self).__init__(message, state, term, productions)


class LRConflicts(Exception):
    def __init__(self, conflicts):
        self.conflicts = conflicts
        message = "\n{} conflicts in following states: {}"\
                  .format(self.kind,
                          set([c.state.state_id for c in conflicts]))
        super(LRConflicts, self).__init__(message)


class SRConflicts(LRConflicts):
    kind = "Shift/Reduce"


class RRConflicts(LRConflicts):
    kind = "Reduce/Reduce"
