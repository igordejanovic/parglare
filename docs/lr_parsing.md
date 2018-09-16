# LR parsing, ambiguities and conflicts resolving

LR parser operates as a deterministic PDA (Push-down automata). It is a state
machine which is always in some state during parsing. The state machine must
deterministically decide what is the next state just based on its current state
and one token of lookahead (actually, parser could use more than one token of
lookahead thus being LR(2), LR(3) and so on, but they are not very practical).
This decision is given by LR tables which are precalculated from the grammar
before parsing even begins.

For example, let's see what happens if we have a simple expression grammar:

    E: E '+' E
     | E '*' E
     | number;
    number: /\d+/;

and we want to parse the following input:

     1 + 2 * 3

Language defined by this grammar is ambiguous as the expression can be
interpreted either as:

     ((1 + 2) * 3)

or:

     (1 + (2 * 3))


In the parsing process, parser starts in state 0 and it sees token `1` ahead
(one lookahead is used - LR(1)).

The only thing a parser can do in this case is to shift, i.e. to consume the
token and advance the position. This operation transition the automata to some
other state. From each state there is only one valid transition that can be
taken or the PDA won't be deterministic, i.e. we could simultaneously follow
different paths (that is exactly what the `GLRParser` does).

Current position would be (the dot represents the position):

     1 . + 2 * 3

Now the parser sees `+` token ahead and the tables will tell him to reduce the
number he just saw to `E` (a number is an expression according to the grammar).
Thus, on the stack the parser will have an expression `E` (actually, LR states
are kept on the stack but that's not important for this little analysis). This
reduction will advace PDA to some other state again. Each shift/reduce operation
change state so I'll not repeat that anymore.


!!! tip

    See [pglr command](./pglr.md) which can be used to visualize PDA. Try to
    visualize automata for this grammar.


After reduction parser will do shift of `+` token. There is nothing to reduce as
the sub-expression on stack is `E +` which can't be reduced as it's not complete.
So, the only thing we can do is to shift `2` token.

Now, the position is:

      1 + 2 . * 3

And the stack is:

      E + 2

And this is a place where the parser can't decide what to do. It can either
reduce the sum on the stack or shift `*` and `3` and reduce multiplication
first and the sumation afterwards.

If the sum is reduced first and `*` shifted afterwards we would get the
following result:

     (1 + 2) * 3

If the shift of `*` and `3` is done instead of reducing, the reduction would
first reduce multiplication and then sum (reduction is always done on the top of
the stack). We will have the following result:

    1 + (2 * 3)

From the point of view of arithmetic priorities, preferred solution is the last
one but the parser don't know arithmetic rules.

If you analyze this grammar using [pglr command](./pglr.md) you will see that
the LR tables have Shift/Reduce conflicts as there is a state in which parser
can't decide whether to shift or to reduce (we just saw that situation).

parglare gives you various tools to be more explicit with your grammar and to
resolve these conflicts.

There are two situations when conflicts can't be resolved:

- you need more than one lookahead to disambiguate,
- your language is inherently ambiguous.

If you end up in one of these situations you must use GLR parsing, which will
fork the parser at each state which has multiple paths, and explore all
possibilities.


## Resolving conflicts

When we run:

    $ pglr compile expr.pg

where in `expr.pg` we have the above grammar, we get the following output at the
end:

    *** S/R conflicts ***
    There are 4 S/R conflicts

    State 6
            1: E = E + E .   {+, *, STOP}
            1: E = E . + E   {+, *, STOP}
            2: E = E . * E   {+, *, STOP}

    In state 6 and input symbol '+' can't decide whether to shift or
    reduce by production(s) '1: E = E + E'.

    State 6
            1: E = E + E .   {+, *, STOP}
            1: E = E . + E   {+, *, STOP}
            2: E = E . * E   {+, *, STOP}

    In state 6 and input symbol '*' can't decide whether to shift or
    reduce by production(s) '1: E = E + E'.

    State 7
            2: E = E * E .   {+, *, STOP}
            1: E = E . + E   {+, *, STOP}
            2: E = E . * E   {+, *, STOP}

    In state 7 and input symbol '+' can't decide whether to shift or
    reduce by production(s) '2: E = E * E'.

    State 7
            2: E = E * E .   {+, *, STOP}
            1: E = E . + E   {+, *, STOP}
            2: E = E . * E   {+, *, STOP}

    In state 7 and input symbol '*' can't decide whether to shift or
    reduce by production(s) '2: E = E * E'.
    Grammar OK.
    There are 4 Shift/Reduce conflicts. Either use 'prefer_shifts' parser mode,
    try to resolve manually or use GLR parsing.


As we can see this grammar has 4 Shift/Reduce conflicts. At the end of the
output we get an advice to either use `prefer_shifts` strategy that will always
prefer shift over reduce. In this case that's not what we want.

If we look closely at the output we see that parglare gives us an informative
explanation why there are conflicts in our grammar.

The first conflict:


    State 6
            1: E = E + E .   {+, *, STOP}
            1: E = E . + E   {+, *, STOP}
            2: E = E . * E   {+, *, STOP}

    In state 6 and input symbol '+' can't decide whether to shift or
    reduce by production(s) '1: E = E + E'.

Tell us that when the parser saw addition — the dot in the above productions
represents all possible positions of the parser in the input stream in this
state — and there is `+` ahead, it doesn't know should it reduce the addition or
shift the `+` token.

This means that if we have an expression: `1 + 2 + 3` should we calculate it as
`(1 + 2) + 3` or as `1 + (2 + 3)`. Of course, the result in this case would be
the same, but imagine what would happen if we had subtraction operation instead
of addition. In arithmetic, this is defined by association which says that
addition if left associative, thus the operation is executed from left to right.

Parglare enables you to define associativity for you productions by specifying
`{left}` or `{right}` at the end of production. You can think of `left`
associativity as telling the parser to prefer reduce over shift for this
production and the `right` associativity for preferring shifts over reduces.

Let's see the second conflict:

    State 6
            1: E = E + E .   {+, *, STOP}
            1: E = E . + E   {+, *, STOP}
            2: E = E . * E   {+, *, STOP}

    In state 6 and input symbol '*' can't decide whether to shift or
    reduce by production(s) '1: E = E + E'.

In the same state, when we saw addition and have `*` ahead parser can't decide.

This means that if we have an expression: `1 + 2 * 3` should we calculate it as
`(1 + 2) * 3` or `1 + (2 * 3)`. In arithmetic this is handled by operation
priority. We want multiplication to be executed first, so we should raise the
priority of multiplication (or lower the priority of addition).



    E: E '+' E  {left, 1}
     | E '*' E  {left, 2}
     | number;
    number: /\d+/;


We have augmented our grammar to state that both operation are left associative,
thus the parser will know what to do in the case of `1 + 2 + 3` or `1 * 2 * 3`
it will reduce from left to right, i.e. prefer reduce over shifts. We also
specified that addition has a priority of 1 and multiplication has a priority of
2, thus the parser will know what to do in case of `1 + 2 * 3`, it will shift
`*` instead of reducing addition as the multiplication should be
reduced/calculated first.


!!! note

    The default priority for rules is 10.


This change in the grammar resolves all ambiguities and our grammar is now
LR(1).


See the section on [disambiguation strategies](./disambiguation.md) for more.
