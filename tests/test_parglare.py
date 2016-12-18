#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_parglare
----------------------------------

Tests for `parglare` module.
"""

import pytest
from parglare import grammar, parser


def test_parser():
    g = grammar.Grammar.from_file('some_file.g')
    p = parser.Parser(g)

    p.parse_file('some_file.txt')
