# The parglare grammar language

The parglare grammar specification language is based
on [BNF](https://en.wikipedia.org/wiki/Backus%E2%80%93Naur_form)
with [syntactic sugar extensions](#syntactic-sugar-bnf-extensions) which are
optional and builds on top of a pure BNF. parglare is based
on
[Context-Free Grammars (CFGs)](https://en.wikipedia.org/wiki/Context-free_grammar) and
a grammar is written declaratively. You don't have to think about the parsing
process like in
e.g. [PEGs](https://en.wikipedia.org/wiki/Parsing_expression_grammar).
Ambiguities are dealt with explicitly (see
the [section on conflicts](./lr_parsing.md#resolving-conflicts)).

Grammar consists of a set of derivation rules where each rule is of the form:

```
<symbol>: <expression> ;
```

where `<symbol>` is grammar non-terminal and `<expression>` is a sequence of
terminals and non-terminals separated by choice operator `|`.

For example:

```
Fields: Field | Fields "," Field;
```

Here `Fields` is a non-terminal grammar symbol and it is defined as either a
single `Field` or, recursively, as `Fields` followed by a string terminal `,`
and than by another `Field`. It is not given here but `Field` could also be
defined as a non-terminal. For example:

```
Field: QuotedField | FieldContent;
```

Or it could be defined as a terminal:

```
Field: /[A-Z]*/;
```

This terminal definition uses regular expression recognizer.

## Terminals

Terminal symbols of the grammar define the fundamental or atomic elements of
your language -- tokens or lexemes (e.g. keywords, numbers). In parglare a
terminal is connected to the recognizer which is an object used to recognize
token of a particular type in the input. Most of the time you will do parsing of
textual content and you will need textual recognizers. These recognizers are
built-in and there are two type of textual recognizers:

- string recognizer
- regular expression recognizer

### String recognizer

String recognizer is defined as a plain string inside of double quotes:

    my_rule: "start" other_rule "end";

In this example `"start"` and `"end"` will be terminals with string recognizers
that match exactly the words `start` and `end`.

You can write string recognizing terminal directly in the rule expression or you
can define terminal separately and reference it by name, like:

    my_rule: start other_rule end;
    start: "start";
    end: "end";

Either way it will be the same terminal. You will usually write it as a separate
terminal if the terminal is used at multiple places in the grammar.


### Regular expression recognizer

Or regex recognizer for short is a regex pattern written inside slashes
(`/.../`).

For example:

     number: /\d+/;

This rule defines terminal symbol `number` which has a regex recognizer and will
recognize one or more digits as a number.


### Custom recognizers

If you are parsing arbitrary input (non-textual) you'll have to provide your own
recognizers. In the grammar, you just have to provide terminal symbol without
body, i.e. without string or regex recognizer. You will provide missing
recognizers during grammar instantiation from Python. Although you don't supply
body of the terminal you can define [disambiguation rules](./disambiguation.md)
as usual.

Lets say that we have a list of integers (real list of Python ints, not a text
with numbers) and we have some weird requirement to break those numbers
according to the following grammar:

      Numbers: all_less_than_five  ascending  all_less_than_five EOF;
      all_less_than_five: all_less_than_five  int_less_than_five
                        | int_less_than_five;
      int_less_than_five: ;  // <--- This terminal has no recognizer in the grammar


So, we should first match all numbers less than five and collect those, than we
should match a list of ascending numbers and than list of less than five again.
`int_less_than_five` and `ascending` are terminals/recognizers that will be
defined in Python and passed to grammar construction. `int_less_than_five` will
recognize Python integer that is, well, less than five. `ascending` will
recognize a sublist of integers in ascending order.

For more details on the usage
see
[this test](https://github.com/igordejanovic/parglare/blob/master/tests/func/test_recognizers.py).

More on this topic can be found in [a separate section](./recognizers.md).

!!! note
    You can directly write regex or string recognizer at the place of terminal:

        some_rule: "a" aterm "a";
        aterm: "a";

    Writting `"a"` in `some_rule` is equivalent to writing terminal reference
    `aterm`. Rule `aterm` is terminal definition rule. All occurences of `"a"`
    as well as `aterm` will result in the same terminal in the grammar.


## Usual patterns

This section explains how some common grammar patterns can be written using just
a plain BNF notation.

### One or more

    // sections rule bellow will match one or more section.
    sections: sections section | section;

In this example `sections` will match one or more `section`. Notice the
recursive definition of the rule. You can read this as _`sections` is either a
single section or `sections` and a `section`_.

!!! note

    Please note that you could do the same with this rule:

        sections: section sections | section;

    which will give you similar result but the resulting tree will be different.
    Notice the recursive reference is now at the and of the first production.
    Previous example will reduce sections early and than add another section to it,
    thus the tree will be expanding to the left. The example in this note will
    collect all the sections and than start reducing from the end, thus building a
    tree expanding to the right. These are subtle differences that are important
    when you start writing your semantic actions. Most of the time you don't care
    about this so use the first version as it is more efficient and parglare
    provides built-in actions for these common cases.

### Zero or more

    // sections rule bellow will match zero or more section.
    sections: sections section | section | EMPTY;

In this example `sections` will match zero or more `section`. Notice the
addition of the `EMPTY` choice at the end. This means that matching nothing is a
valid `sections` non-terminal.

Same note from above applies here to.

### Optional

    document: optheader body;
    optheader: header | EMPTY;

In this example `optheader` is either a header or nothing.


## Syntactic sugar - BNF extensions

Previous section gives the overview of the basic BNF syntax. If you got to use
various BNF extensions
(like [Kleene star](https://en.wikipedia.org/wiki/Kleene_star)) you might find
writing patterns in the previous section awkward. Since some of the patterns are
used frequently in the grammars (zero-or-more, one-or-more etc.) parglare
provides syntactic sugar for this common idioms using a well known regular
expression syntax.

### Optional

`Optional` can be specified using `?`. For example:

    S: "2" b? "3"?;
    b: "1";

Here, after `2` we might have terminal `b` but it is optional, as well as `3`
that follows.

Lets see what the parser will return for various inputs (the `grammar` variable
is a string holding grammar from above):

    g = Grammar.from_string(grammar)
    p = Parser(g)

    input_str = '2 1 3'
    result = p.parse(input_str)
    assert result == ["2", "1", "3"]

    input_str = '2 3'
    result = p.parse(input_str)
    assert result == ["2", None, "3"]


!!! note
    Syntax equivalence for `optional` operator:

        S: b?;
        b: "1";

    is equivalent to:

        S: b_opt;
        b_opt: b | EMPTY;
        b: "1";

    Behind the scenes parglare will create `b_opt` rule.
    All syntactic sugar additions operate by creating additional rules in the
    grammar during table construction.


### One or more

`One or more` match is specified using `+` operator. For example:

    S: "2" c+;
    c: "c";

After `2` we expect to see one or more `c` terminals.

Lets see what the parser will return for various inputs (the `grammar` variable
is a string holding grammar from above):

    g = Grammar.from_string(grammar)
    p = Parser(g)

    input_str = '2 c c c'
    result = p.parse(input_str)
    assert result == ["2", ["c", "c", "c"]]

    input_str = '2 c'
    result = p.parse(input_str)
    assert result == ["2", ["c"]]

So the sub-expression on the second position (`c+` sub-rule) will by default
produce a list of matched `c` terminals. If `c` is missing
a [parse error](./handling_errors.md) will be raised.

!!! note
    Syntax equivalence for `one or more`:

        S: a+;
        a: "a";

    is equivalent to:

        S: a_1;
        @collect
        a_1: a_1 a | a;
        a: "a";


`+` operator allows repetition modifier for separators. For example:

    S: "2" c+[comma];
    c: "c";
    comma: ",";

`c+[comma]` will match one or more `c` terminals separated by whatever is
matched by the `comma` rule.


Lets see what the parser will return for various inputs (the `grammar` variable
is a string holding grammar from above):

    g = Grammar.from_string(grammar)
    p = Parser(g)

    input_str = '2 c, c,  c'
    result = p.parse(input_str)
    assert result == ["2", ["c", "c", "c"]]

    input_str = '2 c'
    result = p.parse(input_str)
    assert result == ["2", ["c"]]

As you can see giving a separator modifier allows us to parse a list of items
separated by the whatever is matched by the rule given inside `[]`.


!!! note
    Syntax equivalence `one or more with separator `:

        S: a+[comma];
        a: "a";
        comma: ",";

    is equivalent to:

        S: a_1_comma;
        @collect_sep
        a_1_comma: a_1_comma comma a | a;
        a: "a";
        comma: ",";

    Making the name of the separator rule a suffix of the additional rule
    name makes sure that only one additional rule will be added to the
    grammar for all instances of `a+[comma]`, i.e. same base rule with the
    same separator.


### Zero or more

`Zero or more` match is specified using `*` operator. For example:

    S: "2" c*;
    c: "c";

This syntactic addition is similar to `+` except that it doesn't require rule to
match at least once. If there is no match, resulting sub-expression will be an
empty list. For example:

    g = Grammar.from_string(grammar)
    p = Parser(g)

    input_str = '2 c c c'
    result = p.parse(input_str)
    assert result == ["2", ["c", "c", "c"]]

    input_str = '2'
    result = p.parse(input_str)
    assert result == ["2", []]


    Syntax equivalence `zero of more`:

        S: a*;
        a: "a";

    is equivalent to:

        S: a_0;
        a_0: a_1 | EMPTY;
        @collect
        a_1: a_1 a | a;
        a: "a";

    So using of `*` creates both `a_0` and `a_1` rules.
    Action attached to `a_0` returns a list of matched `a` and empty list
    if no match is found.

Same as `one or more` this operator may use separator modifiers.

!!! note
    Syntax equivalence `zero or more with separator `:

        S: a*[comma];
        a: "a";
        comma: ",";

    is equivalent to:

        S: a_0_comma;
        a_0_comma: a_1_comma | EMPTY;
        @collect_sep
        a_1_comma: a_1_comma comma a | a;
        a: "a";

    where action is attached to `a_0_comma` to provide returning a list of
    matched `a` and empty list if no match is found.


## Named matches (*assignments*)

In section on [actions](./actions.md) you can see that semantic action (Python
callable) connected to a rule will be called with two parameters: a context and
a list of sub-expressions evaluation results. This require you to use positional
access in the list of sub-expressions.

`Named matches` (a.k.a `assignments`) enable giving a name to the sub-expression
directly in the grammar.

For example:

    S: first=a second=digit+[comma];
    a: "a";
    digit: /\d+/;

In this example root rule matches one `a` and then one or more digit separated
by a comma. You can see that the first sub-expression (`a` match) is assigned to
`first` while the second sub-expression `digit+[comma]` is assigned to `second`.

`first` and `second` will now be an additional keyword parameters passed to the
semantic action. The values passed in using these parameters will be the results
of evaluation of the rules referenced by the assignments.

There are two kind of assignments:

- plain assignment (`=`) -- will collect RHS and pass it to the action under the
  names given by LHS,
- bool assignment (`?=`) -- will pass `True` if the match return non-empty
  result. If the result of RHS is empty the assignment will result in `False`
  being passed to the action.

Each rule using named matches result in a dynamically created Python class named
after the rule. These classes are kept in a dictionary `grammar.classes` and
used to instantiate Python objects during parsing by an implicitly
set [built-in `obj` action](./actions.md#built-in-actions).

Thus, for rules using named matches, default action is to create object with
attributes whose names are those of LHS of the assignments and values are from
RHS of the assignments (or boolean values for `bool` assignments). Each object
is an instance of corresponding dynamically created Python class.

Effectively, using named matches enables automatic creation of a nice AST.

!!! note

    You can, of course, override default action either in the grammar
    using `@` syntax or using rule name in `actions` dict given to the parser.
    See the next section.


## Referencing semantic actions from a grammar

By default [action](./actions.md) with the name same as the rule name will be
searched in the [`actions` dict](./parser.md#actions). You can override this by
specifying action name for the rule directly in the grammar using `@` syntax.

For example:

```
@myaction
some_rule: first second;
```

For rule `some_rule` action with the name `myaction` will be searched in the
`actions` dict or [built-in actions](#built-in-actions) provided by the
`parglare.actions` module. This is helpful if you have some common action that
can be used for multiple rules in your grammar. Also this can be used to specify
built-in action to be used for a rule directly in the grammar.


## Grammar comments

In parglare grammar, comments are available as both line comments and block
comments:


    // This is a line comment. Everything from the '//' to the end of line is a comment.

    /*
      This is a block comment.
      Everything in between `/*`  and '*/' is a comment.
    */


## Handling whitespaces and comments in your language

By default parser will skip whitespaces. Whitespace skipping is controlled
by [`ws` parameter to the parser](./parser.md#ws) which is by default set to
`'\n\t '`.

If you need more control of the layout, i.e. handling of not only whitespaces
but comments also, you can use a special rule `LAYOUT`:


      LAYOUT: LayoutItem | LAYOUT LayoutItem;
      LayoutItem: WS | Comment | EMPTY;
      WS: /\s+/;
      Comment: /\/\/.*/;

This will form a separate layout parser that will parse in-between each matched
tokens. In this example whitespaces and line-comments will be consumed by the
layout parser.

If this special rule is found in the grammar `ws` parser parameter is ignored.

Here is another example that gives support for both line comments and block
comments like the one used in the grammar language itself:

      LAYOUT: LayoutItem | LAYOUT LayoutItem;
      LayoutItem: WS | Comment | EMPTY;
      WS: /\s+/;
      Comment: '/*' CorNCs '*/' | /\/\/.*/;
      CorNCs: CorNC | CorNCs CorNC | EMPTY;
      CorNC: Comment | NotComment | WS;
      NotComment: /((\*[^\/])|[^\s*\/]|\/[^\*])+/;
