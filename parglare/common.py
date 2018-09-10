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
    line, column (int):
    """

    __slots__ = ['input_str', 'start_position', 'end_position', 'position',
                 'file_name', '_line', '_column']

    def __init__(self, context=None, file_name=None):

        self.input_str = context.input_str if context else None
        self.start_position = context.start_position if context else None
        self.end_position = context.end_position if context else None
        self.position = context.position if context else None
        if file_name:
            self.file_name = file_name
        elif context:
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
            return _a('{}{}:{}:"{}"'
                      .format("{}:".format(self.file_name)
                              if self.file_name else "",
                              line, column,
                              position_context(self)))
        elif self.context.file_name:
            return _a(self.file_name)
        else:
            return "<Unknown location>"


def position_context(context):
    """
    Returns position context string.
    """
    start = max(context.position-10, 0)
    c = text(context.input_str[start:context.position]) + "*" \
        + text(context.input_str[context.position:context.position+10])
    return replace_newlines(c)


def replace_newlines(in_str):
    try:
        return in_str.replace("\n", "\\n")
    except AttributeError:
        return in_str


def load_python_module(mod_name, mod_path):
    """
    Loads Python module from an arbitrary location.
    See https://stackoverflow.com/questions/67631/how-to-import-a-module-given-the-full-path  # noqa
    """
    if sys.version_info >= (3, 5):
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            mod_name, mod_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    elif sys.version_info >= (3, 3):
        from importlib.machinery import SourceFileLoader
        module = SourceFileLoader(
            mod_name, mod_path).load_module()
    else:
        import imp
        module = imp.load_source(mod_name, mod_path)

    return module


def get_collector():
    """
    Produces action/recognizers collector/decorator that will collect all
    decorated objects under dictionary attribute `all`.
    """
    all = {}

    class Collector(object):
        def __call__(self, name_or_f):
            """
            If called with action/recognizer name return decorator.
            If called over function apply decorator.
            """
            is_name = type(name_or_f) in [str, text]

            def decorator(f):
                if is_name:
                    name = name_or_f
                else:
                    name = f.__name__
                objects = all.get(name, None)
                if objects:
                    if type(objects) is list:
                        objects.append(f)
                    else:
                        all[name] = [objects, f]
                else:
                    all[name] = f
                return f
            if is_name:
                return decorator
            else:
                return decorator(name_or_f)

    objects = Collector()
    objects.all = all
    return objects
