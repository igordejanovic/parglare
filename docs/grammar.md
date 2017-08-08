# The parglare grammar language

The parglare grammar specification language is based
on [BNF](https://en.wikipedia.org/wiki/Backus%E2%80%93Naur_form). parglare is
based
on
[Context-Free Grammars (CFGs)](https://en.wikipedia.org/wiki/Context-free_grammar) and
a grammar is written declaratively. You don't have to think about the parsing
process like in
e.g. [PEGs](https://en.wikipedia.org/wiki/Parsing_expression_grammar).
Ambiguities are dealt with explicitely (see section on conflicts...).

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

!!! note

    If you got use to various BNF extensions
    (like [Kleene star](https://en.wikipedia.org/wiki/Kleene_star)) you might find
    this awkward because you must build `zero or more` or `one or more` pattern from
    scratch using just a sequence, choice and recursion. The grammars are indeed
    more verbose but, on the other hand, actions are much easier to write and you
    have full control over tree construction process. parglare might provide some
    syntactic sugar later that would make some constructs shorter to write.

## Terminals

Terminal symbols of the grammar define the fundamental or atomic elements of
your language -- tokens or lexemes (e.g. keywords, numbers). In parglare
terminal is connected to recognizer which is an object used to recognize token
of particular type in the input. Most of the time you will do parsing of textual
content and you will need textual recognizers. These recognizers are built-in
and there are two type of textual recognizers:

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

Either way it will be the same terminal. You will usually write as a separate
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
recognizers. In the grammar, you just have to reference your terminal symbol but
you don't have to provide the definition. You will provide missing recognizers
during grammar instantiation from Python.

Lets say that we have a list of integers (real list of Python ints, not a text
with numbers) and we have some weird requirement to break those numbers
according to the following grammar:

      Numbers: all_less_than_five  ascending  all_less_than_five EOF;
      all_less_than_five: all_less_than_five  int_less_than_five
                        | int_less_than_five;


So, we should first match all numbers less than five and collect those, than we
should match a list of ascending numbers and than list of less than five again.
`int_less_than_five` and `ascending` are terminals/recognizers that will be
defined in Python and passed to grammar construction. `int_less_than_five` will
recognize Python integer that is less than five. `ascending` will recognize a
sublist of integers in ascending order.

For more details on the usage see [this test](https://github.com/igordejanovic/parglare/blob/master/tests/func/test_parse_list_of_objects.py).

More on this topic will be written in a separate section.

!!! note
    You can directly write regex or string recognizer at the place of terminal:

        some_rule: "a" aterm "a";
        aterm: "a";

    Writting `"a"` in `some_rule` is equivalent to writing terminal reference
    `aterm`. Rule `aterm` is terminal definition rule. All occurences of `"a"`
    as well as `aterm` will result in the same terminal in the grammar.


## Usual patterns

### One or more

    document: sections;
    // sections rule bellow will match one or more section.
    sections: sections section | section;

In this example `sections` will match one or more `section`. Notice the
recursive definition of the rule. You can read this as _`sections` consist of
sections and a section at the end or `sections` is just a single section_.

!!! note

    Please note that you could do the same with this rule:

        sections: section sections | section;

    which will give you similar result but the resulting tree will be different.
    Former example will reduce sections early and than add another section to it,
    thus the tree will be expanding to the left. The later example will collect all
    the sections and than start reducing from the end, thus building a tree
    expanding to the right. These are subtle differences that are important when you
    start writing your semantic actions. Most of the time you don't care about this
    so use the first version as it is slightly efficient and parglare provides
    common actions for these common cases.

### Zero or more

    document: sections;
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

## Grammar comments

In grammar comments are available as both line comments and block comments:


    // This is a line comment. Everything from the '//' to the end of line is a comment.

    /*
      This is a block comment.
      Everything in between `/*`  and '*/' is a comment.
    */


## Handling whitespaces and comments

By default parser will skip whitespaces. Whitespace skipping is controlled by
`ws` parameter to the parser which is by default set to `'\n\t '`.

If you need more control of the layout, i.e. handling of not only whitespaces by
comments also, you can use a special rule `LAYOUT`:


      LAYOUT: LayoutItem | LAYOUT LayoutItem;
      LayoutItem: WS | Comment | EMPTY;
      WS: /\s+/;
      Comment: /\/\/.*/;

This will form a separate layout parser that will parse in-between each matched
tokens. In this example spaces and line-comments will get consumed by the layout
parser.

If this special rule is found in the grammar `ws` parser parameter is ignored.

Another example that gives support for both line comments and block comments
like the one used in the grammar language itself:

      LAYOUT: LayoutItem | LAYOUT LayoutItem;
      LayoutItem: WS | Comment | EMPTY;
      WS: /\s+/;
      Comment: '/*' CorNCs '*/' | /\/\/.*/;
      CorNCs: CorNC | CorNCs CorNC | EMPTY;
      CorNC: Comment | NotComment | WS;
      NotComment: /((\*[^\/])|[^\s*\/]|\/[^\*])+/;
