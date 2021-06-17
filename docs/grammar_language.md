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

Each grammar file consists of three parts:
- zero or more imports of other grammar files. See [grammar
  modularization](./grammar_modularization.md)
- one or more derivation/production rules
- zero or more terminal definitions

Each derivation/production rule is of the form:

```nohighlight
<symbol>: <expression> ;
```

where `<symbol>` is grammar non-terminal and `<expression>` is a sequence of
terminals and non-terminals separated by choice operator `|`.

For example:

```nohighlight
Fields: Field | Fields "," Field;
```

Here `Fields` is a non-terminal grammar symbol and it is defined as either a
single `Field` or, recursively, as `Fields` followed by a string terminal `,`
and than by another `Field`. It is not given here but `Field` could also be
defined as a non-terminal. For example:

```nohighlight
Field: QuotedField | FieldContent;
```

Or it could be defined as a terminal in terminals section:

```nohighlight
terminals
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

Terminals are given at the end of the grammar file, after production rules,
following the keyword `terminals`.


### String recognizer

String recognizer is defined as a plain string inside of double quotes:

```nohighlight
my_rule: "start" other_rule "end";
```

In this example `"start"` and `"end"` will be terminals with string recognizers
that match exactly the words `start` and `end`.

You can write string recognizing terminal directly in the rule expression or you
can define terminal separately and reference it by name, like:

```nohighlight
my_rule: start other_rule end;

terminals
start: "start";
end: "end";
```

Either way it will be the same terminal. You can't mix those two approaches for
a single terminal. If you defined a terminal in the `terminals` section than you
can't use inline string matches for that terminal.

You will usually write it as a separate terminal if the terminal is used at
multiple places in the grammar or to provide disambiguation information for a
terminal (priority, `prefer` etc.).


### Regular expression recognizer

Or regex recognizer for short is a regex pattern written inside slashes
(`/.../`).

For example:

```nohighlight
number: /\d+/;
```

This rule defines terminal symbol `number` which has a regex recognizer and will
recognize one or more digits as a number.

!!! note

    You cannot write regex recognizers inline like you can do with string
    recognizers. This constraint is introduced because there is no sane way to
    deduce terminal name given its regex. Thus, you must write all regex
    recognizers/terminals in the `terminals` section at the end of the grammar
    file.


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

```nohighlight
Numbers: all_less_than_five  ascending  all_less_than_five;
all_less_than_five: all_less_than_five  int_less_than_five
                  | int_less_than_five;


terminals
// These terminals have no recognizers defined in the grammar
ascending: ;
int_less_than_five: ;
```

So, we should first match all numbers less than five and collect those, than we
should match a list of ascending numbers and than list of less than five again.
`int_less_than_five` and `ascending` are terminals/recognizers that will be
defined in Python and passed to grammar construction. `int_less_than_five` will
recognize Python integer that is, well, less than five. `ascending` will
recognize a sublist of integers in ascending order.

For more details on the usage
see
[this test](https://github.com/igordejanovic/parglare/blob/master/tests/func/recognizers/test_recognizers.py).

More on this topic can be found in [a separate section](./recognizers.md).


## Usual patterns

This section explains how some common grammar patterns can be written using just
a plain BNF notation.

### One or more

```nohighlight
// sections rule below will match one or more section.
sections: sections section | section;
```

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

```nohighlight
// sections rule below will match zero or more section.
sections: sections section | section | EMPTY;
```

In this example `sections` will match zero or more `section`. Notice the
addition of the `EMPTY` choice at the end. This means that matching nothing is a
valid `sections` non-terminal.

Same note from above applies here to.

### Optional

```nohighlight
document: optheader body;
optheader: header | EMPTY;
```

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

```nohighlight
S: "2" b? "3"?;

terminals
b: "1";
```

Here, after `2` we might have terminal `b` but it is optional, as well as `3`
that follows.

Lets see what the parser will return for various inputs (the `grammar` variable
is a string holding grammar from above):

```python
g = Grammar.from_string(grammar)
p = Parser(g)

input_str = '2 1 3'
result = p.parse(input_str)
assert result == ["2", "1", "3"]

input_str = '2 3'
result = p.parse(input_str)
assert result == ["2", None, "3"]
```


!!! note

    Syntax equivalence for `optional` operator:

        S: b?;

        terminals
        b: "1";

    is equivalent to:

        S: b_opt;
        b_opt: b | EMPTY;

        terminals
        b: "1";

    Behind the scenes parglare will create `b_opt` rule.
    All syntactic sugar additions operate by creating additional rules in the
    grammar during table construction.


### One or more

`One or more` match is specified using `+` operator. For example:

```nohighlight
S: "2" c+;

terminals
c: "c";
```

After `2` we expect to see one or more `c` terminals.

Lets see what the parser will return for various inputs (the `grammar` variable
is a string holding grammar from above):

```python
g = Grammar.from_string(grammar)
p = Parser(g)

input_str = '2 c c c'
result = p.parse(input_str)
assert result == ["2", ["c", "c", "c"]]

input_str = '2 c'
result = p.parse(input_str)
assert result == ["2", ["c"]]
```

So the sub-expression on the second position (`c+` sub-rule) will by default
produce a list of matched `c` terminals. If `c` is missing
a [parse error](./handling_errors.md) will be raised.

!!! note

    Syntax equivalence for `one or more`:

        S: a+;

        terminals
        a: "a";

    is equivalent to:

        S: a_1;
        @collect
        a_1: a_1 a | a;

        terminals
        a: "a";


`+` operator allows repetition modifier for separators. For example:

```nohighlight
S: "2" c+[comma];

terminals
c: "c";
comma: ",";
```

`c+[comma]` will match one or more `c` terminals separated by whatever is
matched by the `comma` rule.


Lets see what the parser will return for various inputs (the `grammar` variable
is a string holding grammar from above):

```python
g = Grammar.from_string(grammar)
p = Parser(g)

input_str = '2 c, c,  c'
result = p.parse(input_str)
assert result == ["2", ["c", "c", "c"]]

input_str = '2 c'
result = p.parse(input_str)
assert result == ["2", ["c"]]
```

As you can see giving a separator modifier allows us to parse a list of items
separated by the whatever is matched by the rule given inside `[]`.


!!! note

    Syntax equivalence `one or more with separator `:

        S: a+[comma];

        terminals
        a: "a";
        comma: ",";

    is equivalent to:

        S: a_1_comma;
        @collect_sep
        a_1_comma: a_1_comma comma a | a;

        terminals
        a: "a";
        comma: ",";

    Making the name of the separator rule a suffix of the additional rule
    name makes sure that only one additional rule will be added to the
    grammar for all instances of `a+[comma]`, i.e. same base rule with the
    same separator.


### Zero or more

`Zero or more` match is specified using `*` operator. For example:

```nohighlight
S: "2" c*;

terminals
c: "c";
```

This syntactic addition is similar to `+` except that it doesn't require rule to
match at least once. If there is no match, resulting sub-expression will be an
empty list. For example:

```python
g = Grammar.from_string(grammar)
p = Parser(g)

input_str = '2 c c c'
result = p.parse(input_str)
assert result == ["2", ["c", "c", "c"]]

input_str = '2'
result = p.parse(input_str)
assert result == ["2", []]
```


!!! note

    Syntax equivalence `zero or more`:

        S: a*;

        terminals
        a: "a";

    is equivalent to:

        S: a_0;
        a_0: a_1 {nops} | EMPTY;
        @collect
        a_1: a_1 a | a;

        terminals
        a: "a";

    So using of `*` creates both `a_0` and `a_1` rules. Action attached to `a_0`
    returns a list of matched `a` and empty list if no match is found. Please note
    the [usage of `nops`](./disambiguation.md#nops-and-nopse). In case if
    `prefer_shift` strategy is used using `nops` will perform both REDUCE and
    SHIFT during GLR parsing in case what follows zero or more might be another
    element in the sequence. This is most of the time what you need.

Same as `one or more` this operator may use separator modifiers.

!!! note

    Syntax equivalence `zero or more with separator `:

        S: a*[comma];

        terminals
        a: "a";
        comma: ",";

    is equivalent to:

        S: a_0_comma;
        a_0_comma: a_1_comma {nops} | EMPTY;
        @collect_sep
        a_1_comma: a_1_comma comma a | a;

        terminals
        a: "a";

    where action is attached to `a_0_comma` to provide returning a list of
    matched `a` and empty list if no match is found.


### Parenthesized groups

You can use parenthesized groups at any place you can use a rule reference. For example:

```nohighlight
S: a (b* a {left} | b);
terminals
a: "a";
b: "b";
```

Here, you can see that `S` will match `a` and then either `b* a` or `b`. You can
also see that [meta-data](#user-meta-data) can be applied at a per-sequence
level (in this case `{left}` applies to sequence `b* a`).

Here is a more complex example which uses repetitions, separators, assignments
and nested groups.

```nohighlight
S: (b c)*[comma];
S: (b c)*[comma] a=(a+ (b | c)*)+[comma];
terminals
a: "a";
b: "b";
c: "c";
comma: ",";
```

!!! note

    Syntax equivalence `parenthesized groups`:

        S: c (b* c {left} | b);
        terminals
        c: "c";
        b: "b";

    is equivalent to:

        S: c S_g1;
        S_g1: b_0 c {left} | b;
        b_0: b_1 | EMPTY;
        b_1: b_1 b | b;
        terminals
        c: "c";
        b: "b";

    So using parenthesized groups creates additional `_g<n>` rules (`S_g1` in the
    example), where `n` is a unique number per rule starting from `1`. All other
    syntactic sugar elements applied to groups behave as expected.


## `EMPTY` built-in rule

There is a special `EMPTY` rule you can reference in your grammars. `EMPTY` rule
will reduce without consuming any input and will always succeed, i.e. it is
empty recognition.


## Named matches (*assignments*)

In section on [actions](./actions.md) you can see that semantic action (Python
callable) connected to a rule will be called with two parameters: a context and
a list of sub-expressions evaluation results. This require you to use positional
access in the list of sub-expressions.

`Named matches` (a.k.a `assignments`) enable giving a name to the sub-expression
directly in the grammar.

For example:

```nohighlight
S: first=a second=digit+[comma];

terminals
a: "a";
digit: /\d+/;
```

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

!!! tip

    You can, of course, override default action either in the grammar
    using `@` syntax or using `actions` dict given to the parser.
    See the next section.


## Referencing semantic actions from a grammar

By default [action](./actions.md) with the name same as the rule name will be
searched in the acommpanying `<grammar>_actions.py` file or [`actions`
dict](./parser.md#actions). You can override this by specifying action name for
the rule directly in the grammar using `@` syntax. In that case a name given
after `@` will be used instead of a rule name.

For example:

```nohighlight
@myaction
some_rule: first second;
```

For rule `some_rule` action with the name `myaction` will be searched in the
`<grammar>_actions.py` module, `actions` dict or [built-in
actions](./actions.md/#built-in-actions) provided by the `parglare.actions` module. This is
helpful if you have some common action that can be used for multiple rules in
your grammar. Also this can be used to specify built-in action to be used for a
rule directly in the grammar.


## User meta-data

You can supply arbitrary meta-data for the productions and terminals in the
grammar in the form of key-value pairs. This can be used to augment dynamic
disambiguation strategies, error reporting etc.

To define meta-data put it inside the `{}` block of either rule, production or
terminal in the form of `name: value`, where `name` is a valid ID and `value` is
integer, float, bool (`true` or `false`) or string in single quotes.

For example:

```python
grammar_str = r'''
MyRule: 'a' {left, 1, dynamic, nops,
              some_string:'My Label',
              some_bool: true,
              some_int: 3,
              some_float: 4.5};
'''

grammar = Grammar.from_string(grammar_str)
my_rule = grammar.get_nonterminal('MyRule')

prod = my_rule.productions[0]
assert prod.some_string == 'My Label'
assert prod.some_bool is True
assert prod.some_int == 3
assert prod.some_float == 4.5
```

In this example, user meta-data `some_string` with value `My Label` is defined
on the first production of rule `MyRule`. Please note that user defined
meta-data is accessed as an ordinary Python attribute. In the example you can
also see the definition of meta-data of various supported types.

User meta-data can be defined at the rule level in which case all production for
the given rule inherit the meta-data.

For example:

```python
grammar_str = r'''
MyRule {label: 'My Label', nops}: 'a' {left, 1, dynamic};
'''

grammar = Grammar.from_string(grammar_str)
my_rule = grammar.get_nonterminal('MyRule')

# User meta-data is accessible on the non-terminal
assert my_rule.label == 'My Label'

# The production has its own meta-data
prod = my_rule.productions[0]
assert prod.assoc == ASSOC_LEFT
assert prod.prior == 1
assert prod.dynamic

# Rule-level meta-data are propagated to productions
assert prod.label == 'My Label'
```

Meta-data defined on the rule level can be overriden on the production level.
Also, rule can be specified multiple times. Propagation of each rule meta-data
is done only to the productions specified in the rule.

For example:

```python
grammar_str = r'''
MyRule {label: 'My Label', left}: 'first' {right,
                                            label: 'My overriden label'}
                                | 'second';

MyRule {label: 'Other rule'}: 'third' {left}
                            | 'fourth' {label: 'Fourth prod'};
'''

grammar = Grammar.from_string(grammar_str)
my_rule = grammar.get_nonterminal('MyRule')

# User meta-data is accessible on the non-terminal
# Rule level meta-data are only those defined on the
# first rule in the order of the definition.
assert my_rule.label == 'My Label'

prod1 = my_rule.productions[0]
# First production overrides meta-data
assert prod1.label == 'My overriden label'
assert prod1.assoc == ASSOC_RIGHT

# If not overriden it uses meta-data from the rule.
prod2 = my_rule.productions[1]
assert prod2.label == 'My Label'
assert prod2.assoc == ASSOC_LEFT

# Third and fourth production belongs to the second rule so they
# inherits its meta-data.
prod3 = my_rule.productions[2]
assert prod3.label == 'Other rule'
assert prod3.assoc == ASSOC_LEFT

prod4 = my_rule.productions[3]
assert prod4.label == 'Fourth prod'
assert prod4.assoc == ASSOC_NONE
```



## Grammar comments

In parglare grammar, comments are available as both line comments and block
comments:

```nohighlight
// This is a line comment. Everything from the '//' to the end of line is a comment.

/*
  This is a block comment.
  Everything in between `/*`  and '*/' is a comment.
*/
```


## Handling whitespaces and comments in your language

By default parser will skip whitespaces. Whitespace skipping is controlled
by [`ws` parameter to the parser](./parser.md#ws) which is by default set to
`'\n\t '`.

If you need more control of the layout, i.e. handling of not only whitespaces
but comments also, you can use a special rule `LAYOUT`:


```nohighlight
LAYOUT: LayoutItem | LAYOUT LayoutItem | EMPTY;
LayoutItem: WS | Comment;

terminals
WS: /\s+/;
Comment: /\/\/.*/;
```

This will form a separate layout parser that will parse in-between each matched
tokens. In this example whitespaces and line-comments will be consumed by the
layout parser.

If this special rule is found in the grammar `ws` parser parameter is ignored.

Here is another example that gives support for both line comments and block
comments like the one used in the grammar language itself:

```nohighlight
LAYOUT: LayoutItem | LAYOUT LayoutItem | EMPTY;
LayoutItem: WS | Comment;
Comment: '/*' CorNCs '*/' | LineComment;
CorNCs: CorNC | CorNCs CorNC | EMPTY;
CorNC: Comment | NotComment | WS;

terminals
WS: /\s+/;
LineComment: /\/\/.*/;
NotComment: /((\*[^\/])|[^\s*\/]|\/[^\*])+/;
```


!!! tip

    If `LAYOUT` is provided it *must* match before the first token, between any
    two tokens in the input, and after the last token. If layout cannot be
    empty, the input cannot start or end with a token. If this is not desired,
    make sure to include `EMPTY` in the layout as one of its alternatives like
    in the previous examples.


## Handling keywords in your language

By default parser will match given string recognizer even if it is part of some
larger word, i.e. it will not require matching on the word boundary. This is not
the desired behaviour for language keywords.

For example, lets examine this little grammar:

```nohighlight
S: "for" name=ID "=" from=INT "to" to=INT;

terminals
ID: /\w+/;
INT: /\d+/;
```


This grammar is intended to match statement like this one:

```nohighlight
for a=10 to 20
```

But it will also match:

```nohighlight
fora=10 to20
```

which is not what we wanted.

parglare allows the definition of a special terminal rule `KEYWORD`. This rule
must define a [regular expression recognizer](#regular-expression-recognizer).
Any string recognizer in the grammar that can be also recognized by the `KEYWORD`
recognizer is treated as a keyword and is changed during grammar construction to
match only on word boundary.

For example:

```nohighlight
S: "for" name=ID "=" from=INT "to" to=INT;

terminals
ID: /\w+/;
INT: /\d+/;
KEYWORD: /\w+/;
```


Now,

```nohighlight
fora=10 to20
```

will not be recognized as the words `for` and `to` are recognized to be keywords
(they can be matched by the `KEYWORD` rule).

This will be parsed correctly:

```nohighlight
for a=10 to 20
```

As `=` is not matched by the `KEYWORD` rule and thus doesn't require to be
separated from the surrounding tokens.


!!! note

    parglare uses integrated scanner so this example:

        for for=10 to 20

    will be correctly parsed. `for` in `for=10` will be recognized as `ID` and
    not as a keyword `for`, i.e. there is no lexical ambiguity due to tokenizer
    separation.
