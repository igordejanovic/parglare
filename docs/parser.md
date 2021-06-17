# Parser parameters

There are several parameters you can pass during the parser construction. The
mandatory first parameter is the `Grammar` instance. Other parameters are
explained in the rest of this section.

All parameters described here work for both `parglare.Parser` and
`parglare.GLRParser` classes.


## actions

This parameters is a dict of [actions](./actions.md) keyed by the name of the
grammar rule.

## layout_actions

This parameter is used to specify actions called when the rules of [layout
sub-grammar](./grammar_language.md#handling-whitespaces-and-comments-in-your-language)
are reduced. This is rarely needed but there are times when you would like to
process matched layout (e.g. whitespaces, comments).

It is given in the same format as `actions` parameter, a dict of callables keyed
by grammar rule names.

## ws

This parameter specifies a string whose characters are considered to be
whitespace. By default its value is `'\n\r\t '`. It is used if [layout
sub-grammar](./grammar_language.md#handling-whitespaces-and-comments-in-your-language)
(`LAYOUT` grammar rule) is not defined. If `LAYOUT` rule is given in the grammar
it is used instead and this parameter is ignored.

## build_tree

A boolean whose default value is `False`. If set to `True` parser will call
implicit actions that will build the [parse tree](./parse_forest_trees.md).

## call_actions_during_tree_build

By default, this parameter is set to `False`. If set to `True`, parser will call
actions during the parse tree [parse tree](./parse_forest_trees.md) building
process. The return value of each action will be discarded, since they directly
affect the parse tree building process.


!!! warning

    Use this parameter with a special care when GLR is used, since actions will
    be called even on trees that can't be completed (unsuccessful parses).

## consume_input

A boolean whose value is `True` by default. If `True` the whole input must be
consumed for the parse to be considered successful. This is most of the time
what you want. If set to `False` then LR parser will parse as much as possible
and leave the rest of the input unconsumed while GLR parser will produce all
possible parses with both completely and incompletely consumed input.

!!! warning

    Be aware that setting this option to `False` for GLR usually leads to high
    level of ambiguity and multiple parses as any substring from beginning of
    the input that parses will be considered a valid parse.

## prefer_shifts

By default set to `True` for LR parser and to `False` for GLR parser. In case of
[shift/reduce conflicts](./lr_parsing.md) this strategy would favor shift over
reduce. You can still use [associativity
rules](./disambiguation.md#associativity) to decide per production.

You can disable this rule on per-production basis by using `nops` on the
production.


!!! warning

    Do not use `prefer_shifts` if you don't understand the implications. Try to
    understand [conflicts](./lr_parsing.md) and
    [resolution strategies](./disambiguation.md).


## prefer_shifts_over_empty

By default set to `True` for LR parser and to `False` for GLR parser. In case
of [shift/reduce conflicts](./lr_parsing.md) on empty reductions this strategy
would favor shift over reduce. You can still
use [associativity rules](./disambiguation.md#associativity) to decide per
production.

You can disable this rule on per-production basis by using `nopse` on the
production.

!!! warning

    Do not use `prefer_shifts_over_empty` if you don't understand the
    implications. Try to understand [conflicts](./lr_parsing.md) and
    [resolution strategies](./disambiguation.md).


## error_recovery

By default set to `False`. If set to `True` default error recovery will be used.
If set to a Python function, the function will be called to recover from errors.
For more information see [Error recovery](./handling_errors.md#error-recovery).

## debug/debug_layout

This parameter if set to `True` will put the parser in debug mode. In this mode
parser will print a detailed information of its actions to the standard output.
To put layout subparser in the debug mode use the `debug_layout` parameter. Both
parameters are set to `False` by default.

For more information see [Debugging](./debugging.md)


## debug_colors

Set this to `True` to enable terminal colors in debug/trace output. `False` by
default.

## tables

The value of this parameter is either `parglare.LALR` or `parglare.SLR` and it
is used to choose the type of LR tables to create. By default `LALR` tables are
used with a slight twist to avoid Reduce/Reduce conflicts that may happen with
pure LALR tables. This parameter should not be used in normal circumstances and
is provided more for experimentation purposes.

## force_load_table

LR table is loaded from `<grammar_file_name>.pgt` file if the file exists and is
newer than all of the grammar files, root and imported. If any of the grammar
file modification time is greater than the modification time of the cached LR
table file, table is recalculated and persisted. If you are deploying the parser
in a way that will change file modification times which would trigger table
calculation you can set `force_load_table` to `True`. If this flag is set no
modification check will be performed and table calculation will happen only if
`.pgt` file doesn't exist.

## table

You can pass precomputed parsing table here. This is useful for implementing
custom parse table caching. `None` value for this parameter (the default)
instructs parser to build (or fetch from cache) it's own tables internally.

Example flow for custom caching is shown in
[an example](https://github.com/igordejanovic/parglare/tree/master/examples/custom_table_caching).

!!! warning

    Be careful to provide parse tables compatibile with parser type. Passing
    tables containing conflicts to `Parser` class will propably result in an
    error, but passing tables with automatically resolved conflicts
    (`prefer_shifts=True`) to `GLRParser` will result in parser which may skip
    proper parses.

# `parse` and `parse_file` calls

`parse` call is used to parse input string or list of objects. For parsing of
textual file `parse_file` is used.

These two calls accepts the following parameters:

- `input_str` - first positional and mandatory parameter only for `parse` call -
  the input string/list of objects.

- `position` - the start position to parse from. By default 0.

- `extra` - an object used for arbitrary user state kept during parsing. It will
  be accessible on context-like objects. If not given an instance of `dict` will
  be created.

- `file_name` - first positional and mandatory parameter only for `parse_file`
  call - the name/path of the file to parse.


# `Token` class

This class from `parglare.parser` is used to represent lookahead tokens. Token
is a concrete matched terminal from the input stream.

Attributes:

- `symbol` (`Terminal`) - terminal grammar symbol represented by this token,

- `value` (`list` or `str`) - matched part of the input stream,

- `additional_data` (`list`) - additional information returned by a custom
  recognizer.

- `length` (`int`) - length of the matched input.
