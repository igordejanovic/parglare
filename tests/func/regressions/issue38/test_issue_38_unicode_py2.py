# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os
from parglare import Grammar
from parglare import Parser


def test_grammar_with_unicode():
    this_folder = os.path.dirname(__file__)
    grammar = Grammar.from_file(os.path.join(this_folder, "names.pg"))
    parser = Parser(grammar)
    inp = 'МИША МЫЛ РАМУ'
    result = parser.parse(inp)
    assert result
