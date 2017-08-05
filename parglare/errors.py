from __future__ import unicode_literals


class Error(object):
    """
    Instances of this class are used for error reporting in the context
    of error recovery.
    """
    def __init__(self, position, length, message=None):
        """
        :param position: Position in the stream where the error starts.
        :param lenght: The length of the erroneous piece of input.
        :param message: A message to the user about the error.
        """
        self.position = position
        self.length = length
        self.message = message if message else "Unexpected input."

    def __str__(self):
        return self.message
