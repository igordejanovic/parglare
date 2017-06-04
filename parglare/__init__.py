# -*- coding: utf-8 -*-
# flake8: NOQA
from parglare.parser import Parser, LALR, SLR
from parglare.grammar import Grammar, NonTerminal, Terminal, \
    RegExRecognizer, EMPTY, EOF
from parglare.exceptions import ParseError, GrammarError

__author__ = """Igor R. Dejanovic"""
__email__ = 'igor DOT dejanovic AT gmail DOT com'
__version__ = '0.1'
