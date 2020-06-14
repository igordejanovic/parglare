# -*- coding: utf-8 -*-
import os
from parglare import Grammar, Parser


def test_grammar_with_unicode():
    this_folder = os.path.dirname(__file__)
    grammar = Grammar.from_file(os.path.join(this_folder, "names.pg"))
    parser = Parser(grammar, consume_input=False)
    inp = 'МИША МЫЛ РАМУ'
    result = parser.parse(inp)
    assert result
