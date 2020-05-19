# Actions

Actions (a.k.a. _semantic actions_ or _reductions actions_) are methods of an
object that get called to reduce the recognized pattern to some higher concept.
E.g. in the `calc` example actions are called to calculate sub-expressions.

There are two consideration to think of:

- Which actions are called?
- When actions are called?

## Custom actions and built-in actions

If you don't provide actions of your own the parser will return nested list
corresponding to your grammar. Each non-terminal result in a list of evaluated
sub-expression while each terminal result in the matched string. If the parser
parameter `build_tree` is set to `True` the parser will build [a parse
tree](./parse_trees.md).

Custom actions are provided to the parser during parser instantiation as
`actions` parameter which must be a Python object where the methods are named
after rules from the grammar. You can provide additional actions that are not
named after the grammar rule names, these actions may be referenced from the
grammar using [`@` syntax for action
specification](./grammar_language.md#referencing-semantic-actions-from-a-grammar).
A Python class that contains action methods must inherit `parglare.Actions`.
This base class defines built-in actions.


Lets take a closer look at the quick intro example:

```python
from parglare import Parser, Grammar, Actions
from operator import add, sub, mul, truediv, pow

grammar = r"""
@op E: E '+' E  {left, 1}
     | E '-' E  {left, 1}
     | E '*' E  {left, 2}
     | E '/' E  {left, 2}
     | E '^' E  {right, 3}
     | '(' E ')' {@inner}
     | number {@single};

terminals
number: /\d+(\.\d+)?/;
"""


class MyActions(Actions):
    def op(self, n):
        opfunc = {
            '+': add,
            '-': sub,
            '*': mul,
            '/': truediv,
            '^': pow
        }[n[1]]
        return opfunc(n[0], n[2])

    def number(self, n):
        return float(n)


g = Grammar.from_string(grammar)
parser = Parser(g, actions=MyActions())
result = parser.parse("34 + 4.6 / 2 * 4^2^2 + 78")
```

The actions for the grammar is defined as class `MyActions` which inherits
`Actions`. Base class contains built-in actions. We can see that `op` action is
defined for rule `E` by specifying `@op` before the rule name. By default
parglare will match the action by the rule name, but if different action name is
provided in the grammar it will be used instead. We can also see that the action
can be defined per production (as `@inner` given for production `'(' E ')'`). If
the action is defined for production it will take precedence over rule level
action. Thus, in this example for each production of rule `E` action `op` will
be called except for the two last production where action is redefined.

The `MyActions` class has `op` and `number` methods. `op` method is the action
referenced by the `E` rule while `number` will be called for terminal rule
`number` where default match by name is used.

Each action method receives one parameter which is a list of actual results of
sub-expressions (results from the lower level actions) given in the order
defined in the grammar. In the case of terminal rule actions, the received
parameter will be the matched input. In this example it will be the matched
number as a string so we shall convert it to `float` in the action.

For example, for the `op` action we know that the `op` method will be called for
the first 5 production of rule `E`. Each production is of the same form, the
only difference is the operation that is used so we first determine the
operation function by using `n[1]` which will be the matched operation. Then we
call the operation function with `n[0]` and `n[2]` which will be the left and
right operands respectively.

In addition, you can access the [parser context
object](./common.md#the-context-object) on the action object as `self.context`.
`Context` object can provide information like the start and end position where
the match occurred, the parser instance etc. Also, you have access to the index
of the production for which the action is called by `self.prod_idx`.

To use `MyAction` actions in our parser we pass an instance of this class as
`actions` parameter during parser construction.

The result of the parsing will be the evaluated expression as the actions will
get called along the way and the result of each actions will be used as an
element of the `n` parameter in calling actions higher in the hierarchy.

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

!!! warning

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


## Built-in actions

parglare provides some common actions in the base class `parglare.Actions`. You
can [reference these actions directly from the
grammar](./grammar_language.md#referencing-rule-actions-from-a-grammar).
Built-in actions are used implicitly by parglare as default actions in
particular case (e.g. for [syntactic
sugar](./grammar_language.md#syntactic-sugar-bnf-extensions)) but you might want
to reference some of these actions directly.

Following are parglare built-in actions from the `parglare.Actions` class:

- **none** - returns `None`;

- **nochange** - returns parameter of action callable (`value` or `nodes`)
  unchanged;

- **empty** - returns an empty list `[]`;

- **single** - returns `n[0]`. Used implicitly by rules where all productions
  have only a single rule reference on the RHS;

- **inner** - returns `n[1:-1]` or `n[1] if len(nodes)==3`. Handy to extract
  sub-expression value for values in parentheses;

- **collect** - Used for rules of the form `Elements: Elements Element |
  Element;`. Implicitly used for `+` operator (one-or-more). Returns list;

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

- **obj** - Used implicitly by rules using [named
  matches](./grammar_language.md#named-matches-assignments). Creates Python
  object with attributes derived from named matches. Objects created this way
  have additional attributes `_pg_start_position`/`_pg_end_position` with
  start/end position in the input stream where the object is found.



## Actions for rules using named matches

If [named matches](./grammar_language.md#named-matches-assignments) are used in
the grammar rule, action will be called with additional keyword parameters named
by the name of LHS of rule assignments. If no action is specified for the rule,
and `create_objects` parameter of `Grammar` constructor methods is set to `True`,
a built-in action `obj` is called and will produce instance of dynamically
created Python class corresponding to the grammar rule. See more in the section
on [named matches](./grammar_language.md#named-matches-assignments).

If for some reason you want to override default behavior that create Python
object you can create action like this:

```nohighlight
S: first=a second=digit+[comma];

terminals
a: "a";
digit: /\d+/;
```


now create action method that accepts additional params:

```python
  def S(self, n, first, second):
      ... do some transformation and return the result of S evaluation
      ... nodes will contain subexpression results by position while
      ... first and second will contain the values of corresponding
      ... sub-expressions
```
