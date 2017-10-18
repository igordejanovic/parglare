# Handling errors

When parglare encounter a situation in which no SHIFT or REDUCE operation could
be performed it will report an error by raising an instance of
`parglare.ParseError` class.

`ParseError` has the following attributes:

- **file_name** - the name of the file being parsed (`None` if string is
  parsed),

- **position** - an absolute position in the input where the error occured,

- **line**/**column** - line and column where the error occured.
  

If there is an error in the grammar itself parglare will raise
`parglare.GrammarError` exception.


# Error recovery

There are a lot of situations where you would want parser to report all the
errors in one go. To do this, parser has to recover from errors, i.e. get to
the valid state and continue.

To enable error recovery set
`error_recovery` [parameter of parser construction](./parser.md#error_recovery)
to `True`. This will enable implicit error recovery strategy that will simply
drop characther/object at the place of the error and try to continue. All errors
will be collected as an `errors` list on the parser instance.

Each error is an instance of `parglare.Error` class. This class has the
following attributes:

- **position** - an absolute position of the error,
- **length** - the length of erroneous part of input,
- **message** - the error message,
- **input_str** - the input string/list of objects,
- **expected_symbols** - A set of grammar symbols expected at the location.

which are supplied to the `Error` constructor to build a new instance. Either a
`message` or `input_str` with `expected_symbols` should be provided. If
`message` is given it is used as a string representation of the error, otherwise
the message is constructed based on other parameters.

`position` can be converted to `line, column` by calling
`parglare.pos_to_line_col(input, position)`.


## Custom recovery strategy

To provide a custom strategy for error recovery set `error_recovery` to a Python
function. This function should have the following signature:

    def error_recovery_strategy(parser, input, position, expected_symbols):
        ...


- **parser** - instance of the parser, should be used only for querying the
   configuration, not for altering the state,
- **input** - the input string/list,
- **position** - the position in the input where the error has been found,
- **expected_symbols** - a set grammar symbols that are expected at this
   position.

The recovery function should return the tuple `(error, position, token)`.
`error` should be an instance of `parglare.Error` class or `None` if no error
should be reported. `position` should be a new position where the parser should
continue or `None` if a new token is introduced. `token` should be a new token
introduced at the given position or `None` if position is advanced.

So, either position should be advanced if input is skipped, or new token should
be returned if a new token is introduced at the position. You can't both
advance position and introduce new token at the same time.

The `token` symbol should be from the `expected_symbols` for the parser to
recover successfully. `token` should be an instance
of [`parser.Token`](./parser.md#token). This class constructor accepts `symbol`,
`value` and `length`. `symbol` should a grammar symbol from `expected_symbols`,
`value` should be a matched part of the input (actually, in the context of error
recovery this value is a made-up value) and length is the length of the token.
For introduced tokens, length should be set to 0.
