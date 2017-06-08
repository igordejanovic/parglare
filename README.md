[![Build Status](https://travis-ci.org/igordejanovic/parglare.svg?branch=master)](https://travis-ci.org/igordejanovic/parglare)
[![Coverage Status](https://coveralls.io/repos/github/igordejanovic/parglare/badge.svg?branch=master)](https://coveralls.io/github/igordejanovic/parglare?branch=master)
![Status](https://img.shields.io/pypi/status/parglare.svg)
![Python versions](https://img.shields.io/pypi/pyversions/parglare.svg)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

# parglare

A pure Python (G)LR parser with LALR or SLR tables and integrated scanner.

This lib is in the beta. It is not tested extensively in real-world projects yet.


## What is done so far

- Textual syntax for grammar specification. Parsed with parglare.
- LR parser with SLR and LALR tables calculation (LALR is the default). LALR is
  modified to avoid REDUCE/REDUCE conflicts on state merging. Although not
  proven, this should enable handling of all LR(1) grammars with reduced set of
  states and without conflicts. For grammars that are not LR(1) a GLR parsing is
  provided.
- Scanner is integrated into parsing. This give more power as the token
  recognition is postponed and done in the parsing context at the current
  parsing location.
- GLR parsing (Tomita-style algorithm) with a modification to work with
  integrated scanning. Optional lexical disambiguation using GLR machinery.
- Parsing list of arbitrary objects: bytes, numbers, any Python objects!
  See `recognizers` parameter to grammar construction in
  `test_parse_list_of_objects.py` test.
- Declarative associativity and priority-based conflict resolution for productions
  - See the `calc` example, or the quick intro bellow.
- Lexical disambiguation strategy.
  - Priorities are used first.
  - String recognizers are preferred over regexes (i.e. the most specific match).
  - The longest-match strategy is used if multiple regexes matches with the same
    priority. For further disambiguation if longest-match fails `prefer` rule
    may be given in terminal definition.
- Semantic actions with default actions (controlled by `actions` and
  `default_actions` parameters for the `Parser` class).
  - If no action is specified for a given reduction, default will be called
    which will build nodes of a parse tree. With default actions enabled and no
    user actions parglare will return a parse tree.
  - If no actions are provided and the default actions are explicitely disabled
    parser works as a recognizer, i.e. no reduction actions are called and the
    only output of the parser is whether the input was recognized or not.
- Support for language comments/whitespaces using special rule `LAYOUT`. By
  default whitespaces are skipped. This is controled by `ws` parameter to the
  parser constructor which is by default set to `\t\n `. If set to `None` no
  whitespace skipping is provided. If there is a rule `LAYOUT` in the grammar
  this rule is used instead. An additional parser with the layout grammar will
  be built to handle whitespaces.
- cli command `pglr` for grammar check and PDA visualization (export to dot).
- Debug print/tracing of both grammar construction, DPDA states construction and
  parsing process (set `debug=True` and/or `layout_debug=True`to the
  `Parser` instantiation and/or call to `Grammar.from_<>`).
- Tests. I'm trying to maintain high test code coverage.
- There are a few examples (see `examples` folder).

## TODO

- Docs
- Tables caching/loading (currently tables are calculated whenever `Parser` is
  instantiated)
- Error recovery

## Quick intro

This is just a small example to get the general idea. This example shows how to
parse and evaluate expressions with 5 operations with different priority and
associativity. Evaluation is done using semantic/reduction actions.

The whole expression evaluator is done in under 30 lines of code!

Until docs is done see the `example` folder and `tests` for more.


```python
from parglare import Parser, Grammar

grammar = r"""
E = E '+' E  {left, 1}
  | E '-' E  {left, 1}
  | E '*' E  {left, 2}
  | E '/' E  {left, 2}
  | E '^' E  {right, 3}
  | '(' E ')'
  | number;
number = /\d+(\.\d+)?/;
"""

actions = {
    "E": [lambda _, nodes: nodes[0] + nodes[2],
          lambda _, nodes: nodes[0] - nodes[2],
          lambda _, nodes: nodes[0] * nodes[2],
          lambda _, nodes: nodes[0] / nodes[2],
          lambda _, nodes: nodes[0] ** nodes[2],
          lambda _, nodes: nodes[1],
          lambda _, nodes: nodes[0]],
    "number": lambda _, value: float(value),
}

g = Grammar.from_string(grammar)
parser = Parser(g, debug=True, actions=actions)

result = parser.parse("34 + 4.6 / 2 * 4^2^2 + 78")

print("Result = ", result)

# Output
# -- Debuging/tracing output with detailed info about grammar, productions,
# -- terminals and nonterminals, DFA states, parsing progress,
# -- and at the end of the output:
# Result = 700.8
```

## License

MIT

## Python versions

Tested with 2.7, 3.3-3.6

## Credits

Initial layout/content of this package was created with [Cookiecutter](https://github.com/audreyr/cookiecutter) and the [audreyr/cookiecutter-pypackage](https://github.com/audreyr/cookiecutter-pypackage) project template.

