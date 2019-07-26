# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import pytest  # noqa
from parglare import Grammar, Parser, Recognizers
import re


def test_recognizer_context():
    grammar = """
    program: expression+[semicolon];
    expression: term+;

    terminals
    semicolon: ";";
    term:;
    """

    class MyRecognizers(Recognizers):

        term_re = re.compile(r"[a-zA-Z_]+")

        def term(self, input, pos):
            match = self.term_re.match(input, pos)
            if match is None:
                return None
            return input[pos:match.end()]

    g = Grammar.from_string(grammar, recognizers=MyRecognizers())
    parser = Parser(g)
    assert parser.parse("a bb cc; d ee f; g hh i")
