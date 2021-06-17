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
right interpretation/tree when there is ambiguity in the grammar.

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
a [dynamic disambiguation filter](#dynamic-disambiguation-filter) that is most
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
arithmetic `+` operation the result will be the same but that's not true for
each operation. Anyway, parse trees will be different so some choice has to be
made.

In this situation associativity is used. Both `+` and `*` in arithmetic are
left associative (i.e. the operation is evaluated from left to right).

```
E: E "*" E {2, left};
E: E "+" E {1, left};
```

Now, the expression above is not ambiguous anymore. It is interpreted as `(2 +
3) + 5`.

The associativity given in the grammar is either `left` or `right`. Default is
no associativity, i.e. associativity is not used for disambiguation decision.


!!! tip

    Alternatively, you can use keyword `shift` instead of `right` and `reduce`
    instead of `left`.


### `nops` and `nopse`

These two are not actual filters but markers used to
disable [`prefer_shifts`](./parser.md#prefer_shifts) (`nops`)
and [`prefer_shifts_over_empty`](./parser.md#prefer_shifts_over_empty) (`nopse`)
set globally during parser construction on a production level. Productions using
these markers are not influenced by global parser setting meaning that table
construction will not eliminate possible reductions on these productions. Using
these markers have sense only for GLR parsing as the LR deterministic parser
can't be constructed anyway in case of conflicts.

For example:

    Statements: Statements1 {nops}
              | EMPTY;


### prefer

This disambiguation filter is applicable to terminal productions only. It will
be used to choose the right recognizer/terminal in case
of [lexical ambiguity](#lexical-ambiguities).

For example:

```
INT: /[-+]?[0-9]+\b/ {prefer};
FLOAT: /[-+]?[0-9]*\.?[0-9]+([eE][-+]?[0-9]+)?\b/;
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

Second step is to register a predicate function, during parser construction,
that will be used for resolution. This function operates as a filter for
actions. It receives the parsing context for the action, the LR automata states
between whom the transition is about to occur, and the sub-results in the case
of a reduction. The function should return `True` if the transition is allowed
or `False` otherwise. This function sometimes need to maintain some kind of
state. To initialize its state at the beginning it is called with `None` as
parameters.

```
parser = Parser(grammar, dynamic_filter=custom_disambiguation_filter)
```

Where resolution function is of the following form:

```python
def custom_disambiguation_filter(context, from_state, to_state, action,
                                 production, subresults):
    """
    Make first operation that appears in the input as lower priority.
    This demonstrates how priority rule can change dynamically depending
    on the input.
    """
    global operations

    # At the start of parsing this function is called with actions set to None
    # to give a chance for the strategy to initialize.
    if action is None:
        operations = []
        return

    if action is SHIFT:
        operation = context.token.symbol
    else:
        operation = context.token_ahead.symbol

    actions = from_state.actions[operation]
    if operation not in operations and operation.name != 'STOP':
        operations.append(operation)

    if action is SHIFT:
        shifts = [a for a in actions if a.action is SHIFT]
        if not shifts:
            return False

        reductions = [a for a in actions if a.action is REDUCE]
        if not reductions:
            return True

        red_op = reductions[0].prod.rhs[1]
        return operations.index(operation) > operations.index(red_op)

    elif action is REDUCE:

        # Current reduction operation
        red_op = production.rhs[1]

        # If operation ahead is STOP or is of less or equal priority -> reduce.
        return ((operation not in operations)
                or (operations.index(operation)
                    <= operations.index(red_op)))
```

This function is a predicate that will be called for each action for productions
marked with `dynamic` (SHIFT action for dynamic terminal production and REDUCE
action for dynamic non-terminal productions). You are provided with enough
information to make a custom decision whether to perform or reject the
operation.

Parameters are:

- **context** - [the parsing context object](./common.md#the-context-object).

- **from_state/to_state** -- `LRState` instances for the transition,

- **action** - either SHIFT or REDUCE constant from `parglare` module,

- **production** - a production used for the REDUCE operation. Valid only if
  action is REDUCE.

- **subresults (list)** - a sub-results for the reduction. Valid only for
  REDUCE. The length of this list is equal to `len(production.rhs)`.

For details see [test_dynamic_disambiguation_filters.py](https://github.com/igordejanovic/parglare/blob/master/tests/func/parsing/test_dynamic_disambiguation_filters.py).


## Lexical ambiguities

There is another source of ambiguities.

Parglare uses integrated scanner, thus tokens are determined on the fly. This
gives greater lexical disambiguation power but lexical ambiguities might arise
nevertheless. Lexical ambiguity is a situation when at some place in the input
more than one recognizer match successfully.

For example, if in the input we have `3.4` and we expect at this place either an
integer or a float. Both of these recognizer can match the input. The integer
recognizer would match `3` while the float recognizer would match `3.4`. What
should we use?

parglare has lexical disambiguation strategy that will use priorities first. If
this fails (i.e. all terminals have the same priority) we continue with implicit
disambiguation strategy as follows:

1. String recognizers are preferred over regexes (i.e. the most specific match).
2. If we still have multiple matches use longest-match strategy.
3. If more recognizers still match use `prefer` rule if given.
4. If all else fails raise an exception. In case of GLR, ambiguity will be
   handled by parser forking, i.e. you will end up with all solutions/trees.

Thus, in terminal definition rules we can use priorities to favor some of the
recognizers, or we can use `prefer` to favor recognizer if there are multiple
matches of the same length.

For example:

```nohighlight
number: /\d+/ {15};
```

or:

```nohighlight
number: /\d+/ {prefer};
```

!!! note

    Implicit lexical disambiguation is controlled by `lexical_disambiguation`
    parameter passed to `Parser`/`GLRParser` constructor. By default, `Parser`
    uses implict disambiguation while `GLRParser` doesn't.


In addition, you can also specify that the terminal takes part in dynamic
disambiguation:

```nohighlight
number: /\d+/ {dynamic};
```


## Custom token recognition and lexical disambiguation

In the previous section a built-in parglare lexical disambiguation strategy is
explained. There are use-cases when this strategy is not sufficient. For
example, if we want to do fuzzy match of tokens and choose the most similar
token at the position.

parglare solves this problem by enabling you to implement a custom token
recognition by registering a callable during parser instantiation that will,
during parsing, get all the symbols expected at the current location and return
a list of tokens (instances of [`Token` class](./parser.md#token-class)) or `None`/
empty list if no symbol is found at the location.

This callable is registered during parser instantiation as the parameter
`custom_token_recognition`.

```
parser = Parser(
    grammar, custom_token_recognition=custom_token_recognition)
```

The callable accepts:

- **context** - [the parsing context object](./common.md#the-context-object).

- **get_tokens** - a callable used to get the tokens recognized using the
  default strategy. Called without parameters. Custom disambiguation might
  decide to return this list if no change is necessary, reduce the list, or
  extend it with new tokens. See the example below how to return list with a
  token only if the default recognition doesn't succeed.

**Returns:** a list of [`Token` class instances](./parser.md#token-class) or
`None`/empty list if no token is found.

To instantiate `Token` pass in the symbol and the value of the token. Value of
the token is usually a sub-string of the input string.


In the following test `Bar` and `Baz` non-terminals are fuzzy matched. The
non-terminal with the higher score wins but only if the score is above 0.7.


```python
grammar = """
S: Element+;
Element: Bar | Baz | Number;

terminals
Bar: /Bar. \d+/;
Baz: /Baz. \d+/;
Number: /\d+/;
"""

g = Grammar.from_string(grammar)
grammar = [g]

def custom_token_recognition(context, get_tokens):
    """
    Custom token recognition should return a single token that is
    recognized at the given place in the input string.
    """
    # Call default token recognition.
    tokens = get_tokens()

    if tokens:
        # If default recognition succeeds use the result.
        return tokens
    else:
        # If no tokens are found do the fuzzy match.
        matchers = [
            lambda x: difflib.SequenceMatcher(None, 'bar.', x.lower()),
            lambda x: difflib.SequenceMatcher(None, 'baz.', x.lower())
        ]
        symbols = [
            grammar[0].get_terminal('Bar'),
            grammar[0].get_terminal('Baz'),
        ]
        # Try to do fuzzy match at the position
        elem = context.input_str[context.position:context.position+4]
        elem_num = context.input_str[context.position:]
        number_matcher = re.compile('[^\d]*(\d+)')
        number_match = number_matcher.match(elem_num)
        ratios = []
        for matcher in matchers:
            ratios.append(matcher(elem).ratio())

        max_ratio_index = ratios.index(max(ratios))
        if ratios[max_ratio_index] > 0.7 and number_match.group(1):
            return [Token(symbols[max_ratio_index], number_match.group())]


parser = Parser(
    g, custom_token_recognition=custom_token_recognition)


# Bar and Baz will be recognized by a fuzzy match
result = parser.parse('bar. 56 Baz 12')
assert result == ['bar. 56', 'Baz 12']

result = parser.parse('Buz. 34 bar 56')
assert result == ['Buz. 34', 'bar 56']

result = parser.parse('Ba. 34 baz 56')
assert result == ['Ba. 34', 'baz 56']

# But if Bar/Baz are too different from the correct pattern
# we get ParseError. In this case `bza` score is below 0.7
# for both Bar and Baz symbols.
with pytest.raises(ParseError):
    parser.parse('Bar. 34 bza 56')
```

!!! note

    `custom_token_recognition` can be used to implement custom lexical
    disambiguation by calling `get_tokens` and then reducing returned list to a
    list with a single result.


!!! tip

    See the end of [the parse trees section](parse_forest_trees.md) for a tip on how to
    investigate ambiguities in GLR parsing.
