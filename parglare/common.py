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

    Args:
    context(Context): Parsing context used to populate this object.
    file_name(str): File name where this location is to be found.
        Takes precendence over `file_name` given in `context`.
    start_position(int): The beginning of the location.
        Takes precendence over `start_position` given in `context`.
    end_position(int): The end of the location.
        Takes precendence over `end_position` given in `context`.
    input_str(str): String representing textual content of the file being
        parsed.
        Takes precendence over `input_str` given in `context`.
    """

    __slots__ = ['file_name', 'start_position', 'end_position', 'line',
                 'column', 'input_str']

    def __init__(self, context=None, file_name=None, start_position=None,
                 end_position=None, input_str=None):

        if not context:
            self.file_name = file_name
            self.start_position = start_position
            self.end_position = end_position
            self.input_str = input_str
        else:
            self.file_name = file_name if file_name else context.file_name
            self.start_position = start_position \
                if start_position is not None else context.start_position
            self.end_position = end_position \
                if end_position is not None else context.end_position
            self.input_str = input_str \
                if input_str is not None else context.input_str

        # Evaluate this only when string representation is needed.
        # E.g. during error reporting
        self.line = None
        self.column = None

    def __str__(self):
        from parglare.parser import pos_to_line_col
        line, col = pos_to_line_col(self.input_str,
                                    self.start_position)
        self.line = line
        self.column = col
        return _a('{}{}:{}:"{}" => '.format("{}:".format(self.file_name)
                                            if self.file_name else "",
                                            line, col,
                                            position_context(
                                                self.input_str,
                                                self.start_position)))


def position_context(input_str, position):
    """
    Returns position context string.
    """
    start = max(position-10, 0)
    c = text(input_str[start:position]) + _a("*") \
        + text(input_str[position:position+10])
    c = c.replace("\n", "\\n")
    return c
