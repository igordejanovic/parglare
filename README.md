[![Build Status](https://travis-ci.org/igordejanovic/parglare.svg?branch=master)](https://travis-ci.org/igordejanovic/parglare)
[![Coverage Status](https://coveralls.io/repos/github/igordejanovic/parglare/badge.svg?branch=master)](https://coveralls.io/github/igordejanovic/parglare?branch=master)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

# parglare

A pure Python Scannerless LR parser (will be GLR soon) with LALR or SLR tables.

This lib is in the early phase of development. It is not tested extensively yet.
Do not use it for anything important.


## What is done so far

- Textual syntax for grammar specification. Parsed with parglare.
- SLR and LALR tables calculation (LALR is the default)
- Scannerless LR(1) parsing
  - Scanner is integrated into parsing. This give more power as the token
    recognition is postponed and done in the parsing context at the current
    parsing location.
- Declarative associativity and priority based conflict resolution for productions
  - See the `calc` example, or the quick intro bellow.
- Lexical disambiguation strategy.
  - The longest-match strategy is used first and then `str` over `regex` match
    (i.e. the most specific match). Terminal priority can be provided for
    further disambiguation if multiple regexes might match with the same length.
- Semantic actions and default (controlled by `actions` and `default_actions`
  parameters for the `Parser` class).
  - If no action is specified for a given reduction, default will be called
    which will build nodes of a parse tree.
  - If no actions are provided and the default actions are explicitely disabled
    parser works as a recognizer, i.e. no reduction actions are called and the
    only output of the parser is whether the input was recognized or not.
- Support for language comments/whitespaces using special rule `LAYOUT`.
- Debug print/tracing (set `debug=True` and/or `layout_debug=True`to the
  `Parser` instantiation).
- Parsing list of arbitrary objects: bytes, numbers, any Python objects!
  See `recognizers` parameter to grammar construction in
  `test_parse_list_of_objects.py` test.
- Tests. Code coverage is pretty high at the moment and I strive to be even
  higher.
- There are a few examples (see `examples` folder).

## TODO

- Docs
- Tables caching/loading (currently tables are calculated whenever `Parser` is
  instantiated)
- GLR parsing (Tomita's algorithm)
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

