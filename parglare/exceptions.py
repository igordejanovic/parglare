from parglare.termui import s_header as _


class LocationError(Exception):
    def __init__(self, location, message):
        self.location = location
        super(LocationError, self).__init__(
            "Error at {} => {}".format(location, message))


class GrammarError(LocationError):
    def __init__(self, location, message):
        super(GrammarError, self).__init__(location, message)


class ParseError(LocationError):
    def __init__(self, location, symbols_expected, tokens_ahead=None,
                 symbols_before=None, last_heads=None, grammar=None):
        """
        Args:
        location(Location): The :class:`Location` of the error.
        symbols_expected(list): A list of :class:`GrammarSymbol` expected at
            the location
        tokens_ahead(list): A list of :class:`Token` recognized at the current
            location.
        symbols_before(list): A list of :class:`GrammarSymbol` recognized just
            before the current position
        last_heads(list): A list of :class:`GSSNode` GLR heads before the
            error.
        grammar(Grammar): An instance of :class:`Grammar` being used for
            parsing.
        """
        self.symbols_expected = symbols_expected
        self.tokens_ahead = tokens_ahead if tokens_ahead else []
        self.symbols_before = symbols_before if symbols_before else []
        self.last_heads = last_heads
        self.grammar = grammar
        message = expected_message(symbols_expected, tokens_ahead)
        super(ParseError, self).__init__(location, message)


def expected_message(symbols_expected, tokens_ahead=None):
    return _('Expected: ') \
        + _(' or ').join(sorted([s.name for s in symbols_expected])) \
        + ((_(' but found ') +
            _(' or ').join(sorted([str(t) for t in tokens_ahead])))
           if tokens_ahead else '')


def expected_symbols_str(symbols):
    return " or ".join(sorted([s.name for s in symbols]))


def disambiguation_error(tokens):
    return "Can't disambiguate between: {}".format(
                _(' or ').join(sorted([str(t) for t in tokens])))


class ParserInitError(Exception):
    pass


class DisambiguationError(LocationError):
    def __init__(self, location, tokens):
        self.tokens = tokens
        message = disambiguation_error(tokens)
        super(DisambiguationError, self).__init__(location, message)


class DynamicDisambiguationConflict(Exception):
    def __init__(self, context, actions):
        self.state = state = context.state
        self.token = token = context.token
        self.actions = actions

        from parglare.parser import SHIFT
        message = "{}\nIn state {}:{} and input symbol '{}' after calling"\
                  " dynamic disambiguation still can't decide "\
                  .format(str(state), state.state_id, state.symbol, token)
        if actions[0].action == SHIFT:
            prod_str = " or ".join(["'{}'".format(str(a.prod))
                                    for a in actions[1:]])
            message += "whether to shift or reduce by "\
                       "production(s) {}.".format(prod_str)
        else:
            prod_str = " or ".join(["'{}'".format(str(a.prod))
                                    for a in actions])
            message += "which reduction to perform: {}".format(prod_str)

        self.message = message

    def __str__(self):
        return self.message


class LRConflict(object):
    def __init__(self, state, term, productions):
        self.state = state
        self.term = term
        self.productions = productions

    @property
    def dynamic(self):
        return self.term in self.state.dynamic


class SRConflict(LRConflict):
    def __init__(self, state, term, productions):
        super(SRConflict, self).__init__(state, term, productions)

    def __str__(self):
        prod_str = " or ".join(["'{}'".format(str(p))
                                for p in self.productions])
        message = "{}\nIn state {}:{} and input symbol '{}' can't " \
                  "decide whether to shift or reduce by production(s) {}.{}" \
            .format(str(self.state), self.state.state_id, self.state.symbol,
                    self.term, prod_str,
                    " Dynamic disambiguation strategy will be called."
                    if self.dynamic else "")

        return message


class RRConflict(LRConflict):
    def __init__(self, state, term, productions):
        super(RRConflict, self).__init__(state, term, productions)

    def __str__(self):
        prod_str = " or ".join(["'{}'".format(str(p))
                                for p in self.productions])
        message = "{}\nIn state {}:{} and input symbol '{}' can't " \
                  "decide which reduction to perform: {}.{}" \
                  .format(str(self.state), self.state.state_id,
                          self.state.symbol, self.term, prod_str,
                          " Dynamic disambiguation strategy will be called."
                          if self.dynamic else "")
        return message


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


class LoopError(Exception):
    pass
