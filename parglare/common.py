# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function
import sys
from parglare.termui import s_attention as _a

if sys.version < '3':
    text = unicode  # NOQA
else:
    text = str


class Location(object):
    """
    Represents a location (point or span) of the object in the source code.

    :ivar str input_str: An input string being parsed this location refers to.
    :ivar int start_position, end_position: The start/end of interval in the
        input string if applicable.
    :ivar int position: The position in the input string.
    :ivar str file_name: A path to the file this location refers to.
    :ivar int line, column: Properties for getting line/column of this
        location.
    """

    __slots__ = ['input_str', 'start_position', 'end_position', 'position',
                 'file_name', '_line', '_column']

    def __init__(self, context=None, file_name=None):
        """
        :param class:`Context` context: Parsing context used to populate this
            object.
        :param str file_name: A path to the file this location refers to.
        """

        self.input_str = context.input_str if context else None
        self.start_position = context.start_position if context else None
        self.end_position = context.end_position if context else None
        self.position = context.position if context else None
        self.file_name = file_name
        if not file_name and context:
            self.file_name = context.file_name

        # Evaluate this only when string representation is needed.
        # E.g. during error reporting
        self._line = None
        self._column = None

    @property
    def line(self):
        if self._line is None:
            self.evaluate_line_col()
        return self._line

    @property
    def column(self):
        if self._column is None:
            self.evaluate_line_col()
        return self._column

    def evaluate_line_col(self):
        from parglare.parser import pos_to_line_col
        self._line, self._column = \
            pos_to_line_col(self.input_str, self.start_position)

    def __str__(self):
        line, column = self.line, self.column
        if line is not None:
            return ('{}{}:{}:"{}"'
                    .format("{}:".format(self.file_name)
                            if self.file_name else "",
                            line, column,
                            position_context(self)))
        elif self.file_name:
            return _a(self.file_name)
        else:
            return "<Unknown location>"


def position_context(context):
    """
    Returns position context string.
    """
    start = max(context.position-10, 0)
    c = text(context.input_str[start:context.position]) + _a(" **> ") \
        + text(context.input_str[context.position:context.position+10])
    return replace_newlines(c)


def replace_newlines(in_str):
    try:
        return in_str.replace("\n", "\\n")
    except AttributeError:
        return in_str
