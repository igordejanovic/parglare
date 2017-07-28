# The parglare grammar language

parglare grammar specification language is based
on [BNF](https://en.wikipedia.org/wiki/Backus%E2%80%93Naur_form). parglare is
based
on
[Context-Free Grammars (CFGs)](https://en.wikipedia.org/wiki/Context-free_grammar) and
grammar is given declaratively. You don't have to think about the parsing
process like in
e.g. [PEGs](https://en.wikipedia.org/wiki/Parsing_expression_grammar).
Ambiguities are dealt with explicitely (see section on conflicts...).

Grammar consists of a set of derivation rules where each rule is of the form:

```
<symbol> = <expression> ;
```

where `<symbol>` is grammar non-terminal and `<expression>` is a sequence of
terminals and non-terminals separated by choice operator `|`.

For example:

```
Fields = Field | Fields "," Field;
```

Here `Fields` is a non-terminal grammar symbol and it is defined as either a
single `Field` or, recursively, as `Fields` followed by a string terminal `,`
and than by another `Field`. It is not given here by `Field` might also be
defined as a non-terminal, for example:

```
Field = QuotedField | FieldContent;
```

or it could be defined as a terminal:

```
Field = /[A-Z]*/
```

This terminal definition uses regular expression.


If you got use to various BNF extensions
(like [Kleene star](https://en.wikipedia.org/wiki/Kleene_star)) you might find
this awkward because you must build `zero or more` or `one or more` pattern from
scratch using just a sequence, choice and recursion. The grammars are indeed
more verbose but, on the other hand, actions are much easier to write and you
have full control over tree construction process. parglare might provide some
syntactic sugar later that would make some constructs shorter to write.


## Usual patterns

### One or more

    document = sections;
    // sections rule bellow will match one or more section.
    sections = sections section | section;

In this example `sections` will match one or more `section`.

!!! note

    Be aware that you could do the same with this rule:

        sections = section sections | section;

    which will give you similar result but the resulting tree will be different.
    Former example will reduce sections early and than add another section to it,
    thus the tree will be expanding to the left. The later example will collect all
    the sections and than start reducing from the end, thus building a tree
    expanding to the right. These are subtle differences that are important when you
    start writing your semantic actions. Most of the time you don't care about this
    so use the first version as it is slightly efficient and parglare provides
    common actions for these common cases.

### Zero or more

    document = sections;
    // sections rule bellow will match zero or more section.
    sections = sections section | section | EMPTY;

In this example `sections` will match zero or more `section`. Notice the
addition of the `EMPTY` choice at the end. This means that matching nothing is a
valid `sections` non-terminal.

Same note from above applies here to.

### Optional

    document = optheader body;
    optheader = header | EMPTY;

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


      LAYOUT = LayoutItem | LAYOUT LayoutItem;
      LayoutItem = WS | Comment | EMPTY;
      WS = /\s+/;
      Comment = /\/\/.*/;

This will form a separate layout parser that will parse in-between each matched
tokens. In this example spaces and line-comments will get consumed by the layout
parser.

If this special rule is found in the grammar `ws` parser parameter is ignored.

Another example that gives support for both line comments and block comments
like the one used in the grammar language itself:

      LAYOUT = LayoutItem | LAYOUT LayoutItem;
      LayoutItem = WS | Comment | EMPTY;
      WS = /\s+/;
      Comment = '/*' CorNCs '*/' | /\/\/.*/;
      CorNCs = CorNC | CorNCs CorNC | EMPTY;
      CorNC = Comment | NotComment | WS;
      NotComment = /((\*[^\/])|[^\s*\/]|\/[^\*])+/;
