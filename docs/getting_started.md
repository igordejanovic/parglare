# Getting started

The first thing to do is to write your language grammar using
the [parglare grammar language](./grammar_language.md). You write the grammar
either as a Python string in your source code or as a separate file. In case you
are writing a grammar of a complex language I would suggest the separate file
approach. Although not mandatory, the convention is that parglare grammar files
have `.pg` extension.

The next step is to create the instance of the `Grammar` class. This is achieved
by importing the `Grammar` class and calling either `from_file` or `from_str`
methods supplying the file name for the former and the Python string for the
later call.

```python
from parglare import Grammar

file_name = .....
grammar = Grammar.from_file(file_name)
```

If there is no errors in the grammar you now have the grammar instance. For more
information see the [section about `Grammar` class](./grammar.md).


!!! tip

    There is also a handy [pglr command line tool](./pglr.md) that can be
    used for grammar checking, visualization and debugging.

The next step is to create an instance of the parser. There are two options. If
you want to use LR parser instantiate `Parser` class. For GLR instantiate
`GLRParser` class.


```python
from parglare import Parser
parser = Parser(grammar)
```

or

```python
from parglare import GLRParser
parser = GLRParser(grammar)
```

You can provide additional [parser parameters](./parser.md) during instantiation.

!!! note

    LR parser is faster as the GLR machinery brings a significant overhead. So,
    the general advice is to stick to the LR parsing until you are sure that you
    need additional power of GLR, i.e. either you need more than one token of
    lookahead or your language is inherently ambiguous. pglr tool will help you in
    investigating why you have LR conflicts in your grammar and there are some
    nice [disambiguation features](./lr_parsing.md#resolving-conflicts) in parglare
    that will help you resolve some of those conflicts.

Now parse your input calling `parse` method on the parser instance.

```python
result = parser.parse(input_str)
```

Depending on whether you have configured [actions](./actions.md) and what
parameters you used for parser instance you will
get either:

- a nested lists if no actions are used,
- a parse tree if [`build_tree` parser param](./parser.md#build_tree) is set to
  `True`,
- some other representation of your input if custom actions are used.

In case of the GLR parser you will get a list of all possible results (a.k.a.
_the parse forest_).

## Where to go next?

You can investigate various topics in the docs.
The [examples](https://github.com/igordejanovic/parglare/tree/master/examples)
and
the [tests](https://github.com/igordejanovic/parglare/tree/master/tests/func)
are also a good source of information.
