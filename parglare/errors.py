from __future__ import unicode_literals


def expected_symbols_str(symbols):
    return " or ".join(sorted([s.name for s in symbols]))


class Error(object):
    """
    Instances of this class are used for error reporting in the context
    of error recovery.
    """
    def __init__(self, context, length, message=None, expected_symbols=None):
        """
        Either message should be given or input_str and expected_symbols.

        Args:
            length: The length of the erroneous piece of input.
            message: A message to the user about the error.
            expected_symbols: A set of expected grammar symbols at the
                location.
        """
        self.position = context.position
        self.input_str = context.input_str
        self.length = length
        self.message = message
        self.expected_symbols = set(expected_symbols) \
            if expected_symbols else None

    def __str__(self):
        if self.message:
            return self.message
        else:
            from parglare import pos_to_line_col
            line, col = pos_to_line_col(self.input_str, self.position)
            return "Unexpected input at position {}. Expected: {}"\
                .format((line, col),
                        expected_symbols_str(self.expected_symbols))
