from __future__ import unicode_literals

from .exceptions import expected_message
from .common import Location


def expected_symbols_str(symbols):
    return " or ".join(sorted([s.name for s in symbols]))


class Error(object):
    """
    Instances of this class are used for error reporting if error recovery
    is used.
    """

    __slots__ = ['location', 'expected_symbols', 'tokens_ahead', 'message']

    def __init__(self, context, expected_symbols, tokens_ahead=None):
        """

        Args:
            context (Context): The parsing context.
            expected_symbols: A set of expected grammar symbols at the
                location.
            tokens_ahead: A set of recognized but not expected tokens if any at
                the given location.
        """
        self.location = Location(context)
        self.expected_symbols = expected_symbols
        self.tokens_ahead = tokens_ahead
        self.message = "Error at " + str(self.location) \
            + expected_message(expected_symbols, tokens_ahead)

    def __str__(self):
        return self.message
