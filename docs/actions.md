# Actions

Actions (a.k.a. _semantic actions_ or _reductions actions_) are Python callables
(functions or lambdas mostly) that get called to reduce the recognized pattern
to some higher concept. E.g. in the calc example actions are called to calculate
subexpressions.

There are two consideration to think of:

- Which actions are called?
- When actions are called?

## Custom actions and default actions

If you don't provide actions of your own the default parglare actions will build
the parse tree.

Actions are provided to the parser during parser instantiation as `actions`
parameter which must be a Python dict where the keys are the names of the rules
from the grammar and values are the action callables or a list of callables if
the rule has more than one production/choice.

Lets take a closer look at the quick intro example:

    grammar = r"""
    E: E '+' E  {left, 1}
     | E '-' E  {left, 1}
     | E '*' E  {left, 2}
     | E '/' E  {left, 2}
     | E '^' E  {right, 3}
     | '(' E ')'
     | number;
    number: /\d+(\.\d+)?/;
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
    parser = Parser(g, actions=actions)
    result = parser.parse("34 + 4.6 / 2 * 4^2^2 + 78")

Here you can see that for rule `E` we provide a list of lambdas, one lambda for
each operation. The first element of the list corresponds to the first
production of the `E` rule (`E '+' E {left, 1}`), the second to the second and
so on. For `number` rule there is only a single lambda which converts the
matched string to the Python `float` type, because `number` has only a single
production. Actually, `number` is a terminal definition and thus the second
parameter in action call will not be a list but a matched value itself. At the
end we instantiate the parser and pass in our `actions` using the parameter.

Each action callable receive two parameters. The first is the context object
which gives parsing context information (like the start and end position where
the match occured, the parser instance etc.). The second parameters `nodes` is a
list of actual results of subexpressions given in the order defined in the grammar.

For example:

    lambda _, nodes: nodes[0] * nodes[2],

In this line we don't care about context thus giving it the `_` name. `nodes[0]`
will cary the value of the left subexpression while `nodes[2]` will carry the
result of the right subexpression. `nodes[1]` must be `*` and we don't need to
check that as the parser already did that for us.

The result of the parsing will be the evaluated expression as the actions will
get called along the way and the result of each actions will be used as an
element of the `nodes` parameter in calling actions higher in the hierarchy.

If we don't provide `actions` the default will be used. The default parglare
actions build a [parse tree](./parse_trees.md) whose elements are instances of
`NodeNonTerm` and `NodeTerm` classes representing a non-terminals and terminals
respectively.

If we set `build_tree` parser parameter to `False` and don't provide
actions, no actions will be called making the parser a mere recognizer, i.e.
parser will parse the input and return nothing if parse is successful or raise
`ParseError` if there is an error in the input.


## Time of actions call

In parglare actions can be called during parsing (i.e. on the fly) which you
could use if you want to transform input imediately without building the parse
tree. But there are times when you would like to build a tree first and call
actions afterwards. For example, you might want to do several different
transformation of the tree. Or, another very good reason is, you are using GLR
and you want to be sure that actions are called only on the final tree.

!!! note
    If you are using GLR be sure that your actions has no side-effects, as the
    dying parsers will left those side-effects behind leading to unpredictable
    behaviour. In case of doubt create trees first, choose the right one and
    call actions afterwards with the `call_actions` parser method.

To get the tree and call actions afterwards you don't supply `actions` parameter
to the parser. That way you get the parse tree as a result (or a list of parse
trees in case of GLR). After that you call `call_actions` method on the parser
giving it the root of the tree and the actions dict:

    parser = Parser(g)
    tree = parser.parse("34 + 4.6 / 2 * 4^2^2 + 78")
    result = parser.call_actions(tree, actions=actions)


## The Context object

The first parameter passed to the action function is the Context object. This
object provides us with the parsing context of where the match occured.

These attributes are available on the context object:

- `start_position`/`end_position` - the beginning and the end in the input
  stream where the match occured. `start_position` is the location of the first
  element/character in the input while the `end_position` is one past the last
  element/character of the match. Thus `end_position - start_position` will give
  the lenght of the match including the layout. You can use
  `parglare.pos_to_line_col(input, position)` function to get line and column of
  the position. This function returns a tuple `(line, column)`.

- `layout_content` - is the layout (whitespaces, comments etc.) that are
  collected from the previous non-layout match. Default actions will attach this
  layout to the tree node.

- `symbol` - the grammar symbol this match is for.

- `production` - an instance of `parglare.grammar.Production` class available
  only on reduction actions (not on shifts). Represents the grammar production.

- `node` - this is available only if the actions are called over the parse tree
  using `call_actions`. It represens the instance of `NodeNonTerm` or `NodeTerm`
  classes from the parse tree where the actions is executed.

- `parser` - is the reference to the parser instance. You should use this only
  to investigate parser configuration not to alter its state.

You can also use context object to pass information between lower level and
upper level actions. You can attach any attribute you like, the context object
is shared between action calls. It is shared with the internal layout parser
too.
