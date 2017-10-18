# Disambiguation

At each step LR parser has to decide which operation to execute: SHIFT (to
consume the next token) or REDUCE (to reduce what it saw previously to some
higher level concept).
See [section on LR parsing and conflicts](./lr_parsing.md).


Defining language by CFG alone often leads to ambiguous languages. Sometimes
this is what we want, i.e. our inputs indeed have multiple interpretation and we
want all of them. This is usually true for natural languages. But when we deal
with computer languages we want to avoid ambiguity as there should be only one
interpretation for each valid input. We want to define unambiguous language.

To constrain our grammar and make it define unambiguous language we use so
called _disambiguation filters_. These filters are in charge of choosing the
right interpretation/tree when there is ambiguity in the our grammar.

Even in the simple expression grammar there is ambiguity. For example,
`2 + 3 * 4` expression — in case we know nothing about priorities of arithmetic
operations — can be interpreted in two different ways: `(2 + 3) * 4` and
`2 + (3 * 4)`. Without priorities we would be obliged to use parentheses
everywhere to specify the right interpretation.

Ambiguity is a one source of conflicts in the LR grammars. The other is limited
lookahead. Whatever is the source of conflicts `GLRParser` can cope with it. In
case of ambiguity the parser will return all interpretations possible. In case
of a limited lookahead the parser will investigate all possible paths and
resolve to the correct interpretation further down the input stream.

If our grammar is ambiguous and our language is not that means that we need to
constrain our grammar using disambiguation filters to better describe our
language. Ideally, we strive for a grammar that describe all valid sentences in
our language with a single interpretation for each of them and nothing more.


## Static disambiguation filters

Static disambiguation filters are given in the grammar at the end of the
production using `{}` syntax. There is also
a [dynamic disambiguation filter](./dynamic-disambiguation-filter) that is most
powerful and is specified as a Python function.


### priority

Priority is probably the simplest form of disambiguation. It is also the
strongest in parglare as it's first checked. It is given as a numeric value
where the default is 10. When the parser can't decide what operation to use it
will favor the one associated with the production with a higher priority.

For example:

```
E: E "*" E {2};
E: E "+" E {1};
```
This gives priority of `2` to the production `E "*" E` and `1` to the production
`E "+" E`. When parglare needs to decide, e.g. between shifting `+` or reducing
`*` it saw, it will choose reduce as the multiplication production has higher
priority.

Priority can also be given to terminal productions.


### associativity

Associativity is used for disambiguation between productions of the same
priority. In the grammar fragment above we still have ambiguity for expression:

```
2 + 3 + 5
```

There are two interpretations `(2 + 3) + 5` and `2 + (3 + 5)`. Of course, with
arithmentic `+` operation the result will be the same but that's not true for
each operation. Anyway, parse trees will be different so some choice has to be
made.

In this situation associativity is used. Both `+` and `*` in arithmentic are
left associative (i.e. the operation is evaluated from left to right).

```
E: E "*" E {2, left};
E: E "+" E {1, left};
```

Now, the expression above is not ambiguous anymore. It is interpreted as `(2 +
3) + 5`.

The associativity given in the grammar is either `left` or `right`. Default is
no associativity, i.e. associativity is not used for disambiguation decision.


### prefer

This disambiguation filter is applicable to terminal productions only. It will
be used to choose the right recognizer/terminal in case
of [lexical ambiguity](#lexical-ambiguity).

For example:

```
INT = /[-+]?[0-9]+\b/ {prefer};
FLOAT = /[-+]?[0-9]*\.?[0-9]+([eE][-+]?[0-9]+)?\b/;
```

If in the grammar we have a possibility that both recognizers are tried, both
will succeed for input `23`, but we want `INT` to be choosen in this case.


## Dynamic disambiguation filter

All previously described filters are of static nature, i.e. they are compiled
during LR table calculation (by removing erroneous automata transitions) and
they don't depend on the parsed input.

There are sometimes situations when parsing decision depends on the input.

For example, lets say that we need to parse arithmetic expression but our
operation priority increase for operations that are introduced later in the
input.

```
1 + 2 * 3 - 4 + 5
```
Should be parsed as:

```
((1 + (2 * (3 - 4))) + 5)
```

While

```
1 - 2 + 3 * 4 + 5
```

should be parsed as:

```
(1 - ((2 + (3 * 4)) + 5))
```

As you can see, operations that appears later in the input are of higher priority.

In parglare you can implement this dynamic behavior in two steps:

First, mark productions in your grammar by `dynamic` rule:

```
E: E op_sum E {dynamic}
 | E op_mul E {dynamic}
 | /\d+/;
op_sum: '+' {dynamic};
op_mul: '*' {dynamic};
```

This tells parglare that those production are candidates for dynamic ambiguity
resolution.

Second step is to register a function, during parser construction, that will be
used for resolution. This function operates as a filter for actions in a given
state and lookahead token. It receives the current action, a token ahead,
production (for REDUCE action), sub-results (for REDUCE action), and current LR
automata state and returns either `True` if the action is acceptable or `False`
otherwise. This function sometimes need to maintain some kind of state. To
initialize its state at the beginning it is called with `None` as parameters.

```
parser = Parser(grammar, dynamic_filter=custom_disambiguation_filter)
```

Where resolution function is of the following form:

```
def custom_disambiguation_filter(action, token, production, subresults, state):
    """Make first operation that appears in the input as lower priority.
    This demonstrates how priority rule can change dynamically depending
    on the input.
    """
    global operations

    # At the start of parsing this function is called with actions set to
    # None to give a chance for the strategy to initialize.
    if action is None:
        operations = []
        return

    actions = state.actions[token.symbol]

    # Lookahead operation
    shift_op = token.symbol

    if action is SHIFT:
        if shift_op not in operations:
            operations.append(shift_op)
        if len(actions) == 1:
            return True
        red_op = [a for a in actions if a.action is REDUCE][0].prod.rhs[1]
        return operations.index(shift_op) > operations.index(red_op)

    elif action is REDUCE:

        # Current reduction operation
        red_op = production.rhs[1]
        if red_op not in operations:
            operations.append(red_op)

        if len(actions) == 1:
            return True

        # If lookahead operation is not processed yet is is of higer priority
        # so do not reduce.
        # If lookahead is in operation and its index is higher do not reduce.
        return (shift_op in operations
                and (operations.index(shift_op)
                     <= operations.index(red_op)))
```

This function is a predicate that will be called for each action for productions
marked with `dynamic` (SHIFT action for dynamic terminal production and REDUCE
action for dynamic non-terminal productions). You are provided with enough
information to make a custom decision whether to perform or reject the
operation.

Parameters are:

- **action** - either SHIFT or REDUCE constant from `parglare` module,

- **token (Token)** - a [lookahead token](./parser.md#token),

- **production (Production)** - a [production]() to be reduced. Valid only for
  REDUCE.

- **subresults (list)** - a sub-results for the reduction. Valid only for
  REDUCE. The length of this list is equal to `len(production.rhs)`.

- **state (LRState)** - current LR parser state.

For details see [test_dynamic_disambiguation_filters.py](https://github.com/igordejanovic/parglare/blob/master/tests/func/test_dynamic_disambiguation_filters.py).


## Lexical ambiguities

There is another source of ambiguities.

Parglare uses integrated scanner, thus tokens are determined on the fly. This
gives greater lexical disambiuation power but lexical ambiguities might arise
nevertheless. Lexical ambiguity is a situation when at some place in the input
more than one recognizer match successfully.

For example, if in the input we have `3.4` and we expect at this place either an
integer or a float. Both of these recognizer can match the input. The integer
recognizer would match `3` while the float recognizer would match `3.4`. What
should we use?

parglare has implicit lexical disambiguation strategy that will:

1. Use priorities first.
2. String recognizers are preferred over regexes (i.e. the most specific match).
3. If priorities are the same and we have no string recognizers use
   longest-match strategy.
4. If more recognizers still match use `prefer` rule if given.
5. If all else fails raise an exception. In case of GLR, ambiguity will be
   handled by parser forking, i.e. you will end up with all solutions/trees.


Thus, in terminal definition rules we can use priorities to favor some of the
recognizers, or we can use `prefer` to favor recognizer if there are multiple
matches of the same length.

For example:

      number = /\d+/ {15};

or:

      number = /\d+/ {prefer};

In addition, you can also specify terminal to take a part in dynamic
disambiguation:

      number = /\d+/ {dynamic};
