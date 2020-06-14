# -*- coding: utf-8 -*-
import pytest  # noqa
from parglare import Grammar, Parser
import re


def test_recognizer_context():
    grammar = """
    program: expression+[semicolon];
    expression: term+;

    terminals
    semicolon: ";";
    term:;
    """

    term_re = re.compile(r"[a-zA-Z_]+")

    def term(context, input, pos):
        match = term_re.match(input, pos)
        if match is None:
            return None
        return input[pos:match.end()]

    g = Grammar.from_string(grammar, recognizers={'term': term})
    parser = Parser(g)
    assert parser.parse("a bb cc; d ee f; g hh i")
