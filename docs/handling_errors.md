# Handling errors

When parglare encounters a situation in which no SHIFT or REDUCE operation could
be performed it will report an error by raising an instance of
`parglare.ParseError` class.

`ParseError` has the following attributes:

- **location** - an instance of the [Location class](./common.md#location-class)
  with information of the position and span of the error.

- **symbols_expected (list)** - a list of expected symbol at the location.

- **tokens_ahead (list)** - a list of tokens recognized at the position by
  trying all terminal symbols recognizers from the grammar. Note that this list
  might be empty in case nothing can be recognized at the position or it might
  have more than one element if more recognizers succeeds (lexical ambiguity).

- **symbols_before (list)** - a list of last seen symbols. In the case of LR
  parser it will always be a single element list. In the case of GLR there might
  be more symbols if there were multiple parser heads.


# Error recovery

There are a lot of situations where you would want parser to report all the
errors in one go. To do this, parser has to recover from errors, i.e. get to
the valid state and continue.

To enable error recovery set `error_recovery` [parameter of parser
construction](./parser.md#error_recovery) to `True`. This will enable implicit
error recovery strategy that will simply drop characther/object at the place of
the error and try to continue. All errors will be collected as an `errors` list
on the parser instance.

Each error is an instance of [`ParseError` class](#handling-errors). In case no
recovery is possible last `ParseError` will be raised.


## Custom recovery strategy

To provide a custom strategy for error recovery set `error_recovery` to a Python
function. This function should have the following signature:

    def error_recovery_strategy(context, error):
        ...


- **context** - the [context object](./common.md#the-context-object) at the
  place where error occurred.
- **error** - [`ParseError` instance](#handling-errors).

Using the context object you can query the state of the parser. E.g. to get the
position use `context.position`, to get the parser state use `context.state`, to
get expected symbols in this state use `context.state.actions.keys()`.

To get information about the error use `error` object. E.g. to get expected
symbols at this position for which parser can succesfully continue use
`error.symbols_expected`.

The recovery function should return the tuple `(token, position)`. `position`
should be a new position where the parser should continue or `None` if position
should not change. `token` should be a new token introduced at the given
position or `None` if no new token is introduced. If both `token` and `position`
are `None` error recovery didn't succeed.

The `token` symbol should be from the `error.symbols_expected` for the parser to
recover successfully. `token` should be an instance of
[`parser.Token`](./parser.md#token). This class constructor accepts `symbol`,
`value` and `length`. `symbol` should be a grammar symbol from
`expected_symbols`, `value` should be a matched part of the input (actually, in
the context of error recovery this value is a made-up value) and length is the
length of the token. For introduced tokens, length should be set to 0.
