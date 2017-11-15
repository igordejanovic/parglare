from __future__ import unicode_literals


def expected_symbols_str(symbols):
    return " or ".join(sorted([s.name for s in symbols]))


class Error(object):
    """
    Instances of this class are used for error reporting in the context
    of error recovery.
    """
    def __init__(self, position, length, message=None, input_str=None,
                 expected_symbols=None,):
        """
        Either message should be given or input_str and expected_symbols.


        :param position: Position in the stream where the error starts.
        :param length: The length of the erroneous piece of input.
        :param message: A message to the user about the error.
        :param input_str: The input string/list.
        :param expected_symbols: A set of expected grammar symbols at the
             location.
        """
        self.position = position
        self.length = length
        self.message = message
        self.expected_symbols = set(expected_symbols) \
            if expected_symbols else None

    def __str__(self):
        if self.message:
            return self.message
        else:
            from parglare import pos_to_line_col
            line, col = pos_to_line_col(input, self.position)
            return "Unexpected input at position {}. Expected: {}"\
                .format((line, col),
                        expected_symbols_str(self.expected_symbols))
