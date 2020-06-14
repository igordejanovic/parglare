# Handling errors

When parglare encounters a situation in which no SHIFT or REDUCE operation could
be performed it will report an error by raising an instance of
`parglare.ParseError` class.

`ParseError` has the following attributes:

- **location** - an instance of the [Location class](./common.md#location-class)
  with information of the span of the error.

- **symbols_expected (list)** - a list of expected symbol at the location.

- **tokens_ahead (list)** - a list of tokens recognized at the position by
  trying all terminal symbols recognizers from the grammar. Note that this list
  might be empty in case nothing can be recognized at the position or it might
  have more than one element if more recognizers succeeds (lexical ambiguity).

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

Each error is an instance of [`ParseError` class](#handling-errors). In case no
recovery is possible last `ParseError` will be raised. `ParserError` has a
location which represents the span of the error in the input (e.g.
`error.location.start_position` and `error.location.end_position`).


## Custom recovery strategy

To provide a custom strategy for error recovery set `error_recovery` parser
constructor parameter to a Python function. This function should have the
following signature:

    def error_recovery_strategy(context, error):
        ...


- **context***- context like object (usually the parser head).
- **error** - [`ParseError` instance](#handling-errors).

Using the head object you can query the state of the parser. E.g. to get the
position use `context.position`, to get the parser state use `context.state`, to
get expected symbols in this state use `context.state.actions.keys()`.

To get information about the error use `error` object. E.g. to get expected
symbols at this position for which parser can succesfully continue use
`error.symbols_expected`.

The recovery function should modify the head (e.g. its position and/or
`token_ahead`) and bring it to a state which can continue. If the recovery is
successful the function should return `True`, otherwise `False`.

You can call a default error recovery from your custom recovery by
`context.parser.default_error_recovery(context)`
