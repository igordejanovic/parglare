class NotInitialized(Exception):
    def __init__(self):
        super(NotInitialized, self).__init__(
            "Grammar is not initialized. You should call 'init_grammar'.")


class ParseError(Exception):
    def __init__(self, position, symbols):
        self.position = position
        self.symbols = symbols
        super(ParseError, self).__init__(
            "Error at position %d. Expected: %s" %
            (position, " or ".join([s.name for s in symbols])))
