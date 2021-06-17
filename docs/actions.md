# Actions

Actions (a.k.a. _semantic actions_ or _reductions actions_) are Python callables
(functions or lambdas mostly) that get called to reduce the recognized pattern
to some higher concept. E.g. in the calc example actions are called to calculate
sub-expressions.

!!! note

    LR parser can call the actions during parsing. GLR parser always build the parse
    forest and the actions can be called afterwards on a chosen tree with
    `parser.call_actions`.

There are two consideration to think of:

- Which actions are called?
- When actions are called?


## Custom actions and built-in actions

If you don't provide actions of your own the parser will return nested list
corresponding to your grammar. Each non-terminal result in a list of evaluated
sub-expression while each terminal result in the matched string. If the parser
parameter `build_tree` is set to `True` the parser will build [a parse
tree](./parse_forest_trees.md#parse-trees).

Custom actions are provided to the parser during parser instantiation as
`actions` parameter which must be a Python dict where the keys are the names of
the rules from the grammar and values are the action callables or a list of
callables if the rule has more than one production/choice. You can provide
additional actions that are not named after the grammar rule names, these
actions may be referenced from the grammar using [`@` syntax for action
specification](./grammar_language.md#referencing-semantic-actions-from-a-grammar).


Lets take a closer look at the quick intro example:

```python
grammar = r"""
E: E '+' E  {left, 1}
  | E '-' E  {left, 1}
  | E '*' E  {left, 2}
  | E '/' E  {left, 2}
  | E '^' E  {right, 3}
  | '(' E ')'
  | number;

terminals
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
```

Here you can see that for rule `E` we provide a list of lambdas, one lambda for
each operation. The first element of the list corresponds to the first
production of the `E` rule (`E '+' E {left, 1}`), the second to the second and
so on. For `number` rule there is only a single lambda which converts the
matched string to the Python `float` type, because `number` is a terminal
definition and thus the second parameter in action call will not be a list but a
matched value itself.

At the end we instantiate the parser and pass in our `actions` using the
parameter.

Each action callable receive two parameters. The first is the context object
which gives [parsing context information](./common.md#the-context-object) (like
the start and end position where the match occurred, the parser instance etc.).
The second parameters `nodes` is a list of actual results of sub-expressions
given in the order defined in the grammar.

For example:

```python
lambda _, nodes: nodes[0] * nodes[2],
```

In this line we don't care about the context thus giving it the `_` name.
`nodes[0]` will cary the value of the left sub-expression while `nodes[2]` will
carry the result of the right sub-expression. `nodes[1]` must be `*` and we
don't need to check that as the parser already did that for us.

The result of the parsing will be the evaluated expression as the actions will
get called along the way and the result of each actions will be used as an
element of the `nodes` parameter in calling actions higher in the hierarchy.

If we don't provide `actions`, by default parglare will return a matched string
for each terminal and a list of sub-expressions for each non-terminal
effectively producing nested lists. If we set `build_tree` parameter of the
parser to `True` the parser will produce a [parse tree](./parse_forest_trees.md)
whose elements are instances of `NodeNonTerm` and `NodeTerm` classes
representing a non-terminals and terminals respectively.


## `action` decorator

You can use a special decorator/collector factory `parglare.get_collector` to
create decorator that can be used to collect all actions.

```python
from parglare import get_collector

action = get_collector()

@action
def number(_, value):
    return float(value)

@action('E')
def sum_act(_, nodes):
    return nodes[0] + nodes[2]

@action('E')
def pass_act_E(_, nodes):
    return nodes[0]

@action
def T(_, nodes):
    if len(nodes) == 3:
        return nodes[0] * nodes[2]
    else:
        return nodes[0]

@action('F')
def parenthesses_act(_, nodes):
    return nodes[1]

@action('F')
def pass_act_F(_, nodes):
    return nodes[0]

p = Parser(grammar, actions=action.all)
```

In the previous example `action` decorator is created using `get_collector`
factory. This decorator is parametrized where optional parameter is the name of
the action. If the name is not given the name of the decorated function will be
used. As you can see in the previous example, same name can be used multiple
times (e.g. `E` for `sum_act` and `pass_act_E`). If same name is used multiple
times all action functions will be collected as a list in the order of
definition. Dictionary holding all actions for the created action decorator is
`action.all`.


## Time of actions call

!!! note

    This applies for LR parsing only. GLR parser always build a forest and actions
    are called afterwards with `parser.call_actions`.

In parglare actions can be called during parsing (i.e. on the fly) which you
could use if you want to transform input immediately without building the parse
tree. But there are times when you would like to build a tree first and call
actions afterwards.

To get the tree and call actions afterwards you supply `actions` parameter to
the parser as usual and set `build_tree` to `True`. When the parser finishes
successfully it will return the parse tree which you pass to the `call_actions`
method of the parser object to execute actions. For example:

    parser = Parser(g, actions=actions)
    tree = parser.parse("34 + 4.6 / 2 * 4^2^2 + 78")
    result = parser.call_actions(tree)


## Built-in actions

parglare provides some common actions in the module `parglare.actions`. You can
[reference these actions directly from the
grammar](./grammar_language.md#referencing-semantic-actions-from-a-grammar).
Built-in actions are used implicitly by parglare as default actions in
particular case (e.g. for [syntactic
sugar](./grammar_language.md#syntactic-sugar-bnf-extensions)) but you might want
to reference some of these actions directly.

Following are parglare built-in actions from the `parglare.actions` module:

- **pass_none** - returns `None`;

- **pass_nochange** - returns second parameter of action callable (`value` or
  `nodes`) unchanged;

- **pass_empty** - returns an empty list `[]`;

- **pass_single** - returns `nodes[0]`. Used implicitly by rules where all
  productions have only a single rule reference on the RHS;

- **pass_inner** - returns `nodes[1:-1]` or `nodes[1] if len(nodes)==3`. Handy
  to strip surrounding parentheses;

- **collect** - Used for rules of the form `Elements: Elements Element |
  Element;`. Implicitly used for `+` operator. Returns list;

- **collect_sep** - Used for rules of the form `Elements: Elements separator
  Element | Element;`. Implicitly used for `+` with separator. Returns list;

- **collect_optional** - Can be used for rules of the form `Elements: Elements
  Element | Element | EMPTY;`. Returns list;

- **collect_sep_optional** - Can be used for rules of the form `Elements: Elements
  separator Element | Element | EMPTY;`. Returns list;

- **collect_right** - Can be used for rules of the form `Elements: Element
  Elements | Element;`. Returns list;

- **collect_right_sep** - Can be used for rules of the form `Elements: Element
  separator Elements | Element;`. Returns list;

- **collect_right_optional** - Can be used for rules of the form `Elements:
  Element Elements | Element | EMPTY;`. Returns list;

- **collect_right_sep_optional** - Can be used for rules of the form `Elements:
  Element separator Elements | Element | EMPTY;`. Returns list;

- **optional** - Used for rules of the form `OptionalElement: Element | EMPTY;`.
  Implicitly used for `?` operator. Returns either a sub-expression value or
  `None` if empty match.

- **obj** - Used implicitly by rules
  using [named matches](./grammar_language.md#named-matches-assignments).
  Creates Python object with attributes derived from named matches. Objects
  created this way have additional attributes
  `_pg_start_position`/`_pg_end_position` with start/end position in the input
  stream where the object is found.



## Actions for rules using named matches

If [named matches](./grammar_language.md#named-matches-assignments) are used in
the grammar rule, action will be called with additional keyword parameters named
by the name of LHS of rule assignments. If no action is specified for the rule a
built-in action `obj` is called and will produce instance of dynamically created
Python class corresponding to the grammar rule. See more in the section
on [named matches](./grammar_language.md#named-matches-assignments).

If for some reason you want to override default behavior that create Python
object you can create action like this:

```nohighlight
S: first=a second=digit+[comma];

terminals
a: "a";
digit: /\d+/;
```


now create action function that accepts additional params:

```python
def s_action(context, nodes, first, second):
    ... do some transformation and return the result of S evaluation
    ... nodes will contain subexpression results by position while
    ... first and second will contain the values of corresponding
    ... sub-expressions
```

register action on `Parser` instance as usual:

```python
parser = Parser(grammar, actions={"S": s_action})
```
