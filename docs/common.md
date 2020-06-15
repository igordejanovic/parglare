# Common classes and functions

## The Context object

An object of this kind object is passed to various callback functions (actions,
recognizers, error recovery etc.). It is not always an instance of the same
class, but all context objects have the following properties:

- **start_position/end_position** - the beginning and the end in the input
  stream where the match occurred. `start_position` is the location of the first
  element/character in the input while the `end_position` is one past the last
  element/character of the match. Thus `end_position - start_position` will give
  the length of the match including the layout. You can use
  `parglare.pos_to_line_col(input, position)` function to get line and column of
  the position. This function returns a tuple `(line, column)`.

- **file_name** - the name/path of the file being parsed. `None` if Python
  string is parsed.

- **input_str** - the input string (or list of objects) that is being parsed.

- **layout_content** - is the layout (whitespaces, comments etc.) that are
  collected from the previous non-layout match.

- **layout_content_ahead** - layout content before `token_ahead`.

- **token**- the token shifted during SHIFT operation. Instance of
  `parglare.parser.Token`.

- **token_ahead** - the token recognized as a lookahead.

- **production** - an instance of `parglare.grammar.Production` class available
  only on reduction actions (not on shifts). Represents the grammar production.

- **state** - An instance of `parglare.tables.LRState`. The LR state of the
  parser automata. This object contains information of the possible actions in
  this state.

- **node** - this is available only if the actions are called over the parse tree
  using `call_actions`. It represens the instance of `NodeNonTerm` or `NodeTerm`
  classes from the parse tree where the actions is executed.

- **parser** - is the reference to the parser instance. You should use this only
  to investigate parser configuration not to alter its state.

- **head** - is a reference to the Graph-structured stack node (`GSSNode`). Only
  used for GLR parsing.

- **extra** - this attribute can store arbitrary user information for state
  tracking. If not given as a parameter to `parse` call a `dict` is used.


## Location class

Used at various places in parglare to define location and span in the files
(e.g. for error reporting).

### Attributes

- **input_str** - the input string being parsed.

- **file_name** (property) - the name of the file being parsed (`None` if string
  is parsed),

- **start_position/end_position** - an absolute position in the input where the
  span starts/ends,

- **line**/**column** (properites) - line and column where the span starts.

- **line_end**/**column_end** (properites) - line and column where the span
  ends.


If there is an error in the grammar itself parglare will raise
`parglare.GrammarError` exception.
