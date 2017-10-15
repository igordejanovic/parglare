# Actions

Actions (a.k.a. _semantic actions_ or _reductions actions_) are Python callables
(functions or lambdas mostly) that get called to reduce the recognized pattern
to some higher concept. E.g. in the calc example actions are called to calculate
sub-expressions.

There are two consideration to think of:

- Which actions are called?
- When actions are called?

## Custom actions and built-in actions

If you don't provide actions of your own the parser will return nested list
corresponding to your grammar. Each non-terminal result in a list of evaluated
sub-expression while each terminal result in the matched string. If the parser
parameter `build_tree` is set to `True` the parser will
build [a parse tree](./parse_trees.md).

Custom actions are provided to the parser during parser instantiation as
`actions` parameter which must be a Python dict where the keys are the names of
the rules from the grammar and values are the action callables or a list of
callables if the rule has more than one production/choice. You can provide
additional actions that are not named after the grammar rule names, these
actions may be referenced from the grammar
using
[`@` syntax for action specification](./actions.md#referencing-rule-actions-from-a-grammar).

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
which gives [parsing context information](#the-context-object) (like the start
and end position where the match occured, the parser instance etc.). The second
parameters `nodes` is a list of actual results of sub-expressions given in the
order defined in the grammar.

For example:

    lambda _, nodes: nodes[0] * nodes[2],

In this line we don't care about context thus giving it the `_` name. `nodes[0]`
will cary the value of the left sub-expression while `nodes[2]` will carry the
result of the right sub-expression. `nodes[1]` must be `*` and we don't need to
check that as the parser already did that for us.

The result of the parsing will be the evaluated expression as the actions will
get called along the way and the result of each actions will be used as an
element of the `nodes` parameter in calling actions higher in the hierarchy.

If we don't provide `actions`, by default parglare will return a matched string
for each terminal and a list of sub-expressions for each non-terminal
effectively producing nested lists. If we set `build_tree` parameter of the
parser to `True` the parser will produce a [parse tree](./parse_trees.md) whose
elements are instances of `NodeNonTerm` and `NodeTerm` classes representing a
non-terminals and terminals respectively.


## Time of actions call

In parglare actions can be called during parsing (i.e. on the fly) which you
could use if you want to transform input immediately without building the parse
tree. But there are times when you would like to build a tree first and call
actions afterwards. For example, a very good reason is if you are using GLR and
you want to be sure that actions are called only on the final tree.

!!! note
    If you are using GLR be sure that your actions has no side-effects, as the
    dying parsers will left those side-effects behind leading to unpredictable
    behaviour. In case of doubt create trees first, choose the right one and
    call actions afterwards with the `call_actions` parser method.

To get the tree and call actions afterwards you supply `actions` parameter to
the parser as usual and set `build_tree` to `True`. When the parser finishes
successfully it will return the parse tree which you pass to the `call_actions`
method of the parser object to execute actions. For example:

    parser = Parser(g, actions=actions)
    tree = parser.parse("34 + 4.6 / 2 * 4^2^2 + 78")
    result = parser.call_actions(tree)


## The Context object

The first parameter passed to the action function is the Context object. This
object provides us with the parsing context of where the match occurred.

Following attributes are available on the context object:

- `start_position`/`end_position` - the beginning and the end in the input
  stream where the match occured. `start_position` is the location of the first
  element/character in the input while the `end_position` is one past the last
  element/character of the match. Thus `end_position - start_position` will give
  the lenght of the match including the layout. You can use
  `parglare.pos_to_line_col(input, position)` function to get line and column of
  the position. This function returns a tuple `(line, column)`.

- `input_str` - the input string (or list of objects) that is being parsed.

- `layout_content` - is the layout (whitespaces, comments etc.) that are
  collected from the previous non-layout match. Default actions for building the
  parse tree will attach these layouts to the tree nodes.

- `symbol` - the grammar symbol (instance of either `Terminal` or `NonTerminal`
  which inherits `GrammarSymbol`) this match is for.

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


## Built-in actions

parglare provides some common actions in the module `parglare.actions`. You
can
[reference these actions directly from the grammar](#referencing-rule-actions-from-a-grammar).
Built-in actions are used implicitly by parglare as default actions in
particular case (e.g.
for [syntactic sugar](./grammar_language.md#syntactic-sugar-bnf-extensions)) but you
might need to reference some of these actions.


Following are parglare built-in actions from the `parglare.actions` module:

- `pass_none` - returns `None`;

- `pass_nochange` - returns second parameter of action callable (`value` or
  `nodes`) unchanged;

- `pass_empty` - returns an empty list `[]`;

- `pass_single` - returns `nodes[0]`. Used implicitly by rules where all
  productions have only a single rule reference on the RHS;

- `pass_inner` - returns `nodes[1]`. Handy to extract sub-expression value for
  values in parentheses;

- `collect` - Used for rules of the form `Elements: Elements Element |
  Element;`. Implicitly used for `+` operator. Returns list;

- `collect_sep` - Used for rules of the form `Elements: Elements separator
  Element | Element;`. Implicitly used for `+` with separator. Returns list;

- `collect_optional` - Can be used for rules of the form `Elements: Elements
  Element | Element | EMPTY;`. Returns list;

- `collect_sep_optional` - Can be used for rules of the form `Elements: Elements
  separator Element | Element | EMPTY;`. Returns list;

- `collect_right` - Can be used for rules of the form `Elements: Element
  Elements | Element;`. Returns list;

- `collect_right_sep` - Can be used for rules of the form `Elements: Element
  separator Elements | Element;`. Returns list;

- `collect_right_optional` - Can be used for rules of the form `Elements:
  Element Elements | Element | EMPTY;`. Returns list;

- `collect_right_sep_optional` - Can be used for rules of the form `Elements:
  Element separator Elements | Element | EMPTY;`. Returns list;

- `optional` - Used for rules of the form `OptionalElement: Element | EMPTY;`.
  Implicitly used for `?` operator. Returns either a sub-expression value or
  `None` if empty match.

- `obj` - Used implicitly by rules
  using [named matches](./grammar_language.md#named-matches). Creates Python object with
  attributes derived from named matches.


## Referencing rule actions from a grammar

By default action with the name same as the rule name will be searched in the
`actions` dict. You can override this by specifying action name for the rule
directly in the grammar using `@` syntax.

For example:

```
@myaction
some_rule: first second;
```

For rule `some_rule` action with the name `myaction` will be searched in the
`actions` dict or [built-in actions](#built-in-actions) provided by the
`parglare.actions` module. This is helpful if you have some common action that
can be used for multiple rules in your grammar. Also this can be used to specify
built-in actions to be used for each rule directly in the grammar.


## Actions for rules using named matches

If [named matches](./grammar_language.md#named-matches) are used in the grammar rule,
action will be called with additional keyword parameters named by the name of
LHS of rule assignments. If no action is specified for the rule a built-in
action `obj` is called and will produce instance of dynamically created Python
class corresponding to the grammar rule. See more in the section
on [named matches](./grammar_language.md#named-matches).

If for some reason you want to override default behavior that create Python
object you can create action like this:

    S: first=a second=digit+[comma];
    a: "a";
    digit: /\d+/;


now create action function that accepts additional params:

    def s_action(context, nodes, first, second):
       ... do some transformation and return the result of S evaluation
       ... nodes will contain subexpression results by position while
       ... first and second will contain the values of corresponding
       ... sub-expressions

register action on `Parser` instance as usual:

    parser = Parser(grammar, actions={"S": s_action})
