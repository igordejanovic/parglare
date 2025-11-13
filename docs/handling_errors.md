# Handling errors

When parglare encounters a situation in which no SHIFT or REDUCE operation could
be performed it will report an error by raising an instance of
`parglare.SyntaxError` class.

`SyntaxError` has the following attributes:

- **location** - an instance of the [Location class](./common.md#location-class)
  with information of the span of the error.

- **symbols_expected (list)** - a list of expected symbol at the location.

- **tokens_ahead (list)** - a list of tokens recognized at the position by
  trying all terminal symbols recognizers from the grammar. Note that this list
  might be empty in case nothing can be recognized at the position or it might
  have more than one element if more recognizers succeeds (lexical ambiguity).
  To prevent a terminal to be used in this find-all approach you can mark the
  terminal by `unexpected: false` user meta-data.

- **symbols_before (list)** - a list of last seen symbols. In the case of LR
  parser it will always be a single element list. In the case of GLR there might
  be more symbols if there were multiple parser heads.

- **last_heads (list)** - A list of last GLR parser heads. Available only for
  GLR parsing.

- **grammar (Grammar)** - An instance of `parglare.Grammar` class used for
  parsing.


# Error recovery

There are a lot of situations where you would want parser to report all the
errors in one go. To do this, parser has to recover from errors, i.e. get to
the valid state and continue.

To enable error recovery set `error_recovery` [parameter of parser
construction](./parser.md#error_recovery) to `True`. This will enable implicit
error recovery strategy that will try to search for expected tokens in the input
ahead and when the first is found the parsing will continue. All errors will be
collected as an `errors` list on the parser instance.

Each error is an instance of [`SyntaxError` class](#handling-errors). In case no
recovery is possible last `SyntaxError` will be raised. `SyntaxError` has a
location which represents the span of the error in the input (e.g.
`error.location.start_position` and `error.location.end_position`).


## Custom recovery strategy

To provide a custom strategy for error recovery set `error_recovery` parser
constructor parameter to a Python function. This function should have the
following signature:

    def error_recovery_strategy(context, error):
        ...


- **context***- context like object (usually the parser head).
- **error** - [`SyntaxError` instance](#handling-errors).

Using the head object you can query the state of the parser. E.g. to get the
position use `context.position`, to get the parser state use `context.state`, to
get expected symbols in this state use `context.state.actions.keys()`.

To get information about the error use `error` object. E.g. to get expected
symbols at this position for which parser can successfully continue use
`error.symbols_expected`.

The recovery function should modify the head (e.g. its position and/or
`token_ahead`) and bring it to a state which can continue. If the recovery is
successful the function should return `True`, otherwise `False`.

You can call a default error recovery from your custom recovery by
`context.parser.default_error_recovery(context)`


## Custom error hints from examples

To improve error messages, you can define custom error hints by providing
examples of erroneous inputs and corresponding error message hints. If parglare
finds a `.pge` (parglare error examples) file in the same directory as the `.pg`
file, it will use it to produce a special table of hints that is used during
parsing to construct a more user-friendly error message.

The content of the `.pge` file consists of example-hint pairs in the form:

```
out = in1 + in2
:::+
'out' is a reserved keyword and cannot be used as a variable
```

The first line is the example that triggers the error. The last line is the hint
that will be part of the error message. The separator is `:::` with an optional
`+` at the end, which signifies that a lookahead token should be matched for
this rule to be used. The separator between example rules is `=====` (five
consecutive `=` characters).

When the parser instance is created, if the grammar is loaded from a file, a
file with the same base name as the grammar but with the `.pge` extension will
be searched for. If found, and there isn't a newer file with the `.pgec`
extension, it will be compiled by parsing each example until an error state is
reached. When that happens, for each example, the LR state, lookahead (if `+` is
found after `:::`), and the hint message will be saved to the `.pgec` file. If a
`.pgec` file is newer than the error examples file, it will be loaded and used
during parsing.

Later, during parsing, if hint states exist for the parser, the parser will
consult them when creating an error message by passing the hint message of the
corresponding state to the `SyntaxError` `hint` parameter. This will not modify
the original syntax error message but will add a hint below that better explains
the error.

For example, for the definition above if we try to parse input:

```
fn test():
    out = in1 + in2
```

We get error message:

```
2:7: syntax error: unexpected token =
    1 | fn test():
    2 |    out = in1 + in2
      |        ^^^ expected: <
  hint: Cannot use 'out' as variable name as it is a reserved keyword for IO variable declarations.
```

This is based on the paper:

```
JEFFERY, Clinton L. Generating LR syntax error messages from examples. ACM Transactions on Programming Languages and Systems (TOPLAS), 2003, 25.5: 631-640.
```
