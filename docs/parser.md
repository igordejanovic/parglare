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

This parameter is used to specify actions called when the rules
of
[layout sub-grammar](./grammar_language.md#handling-whitespaces-and-comments-in-your-language) are
reduced. This is rarely needed but there are times when you would like to
process matched layout (e.g. whitespaces, comments).

It is given in the same format as `actions` parameter, a dict of callables keyed
by grammar rule names.

## ws

This parameter specifies a string whose characters are considered to be
whitespace. By default its value is `'\n\r\t '`. It is used
if
[layout sub-grammar](./grammar_language.md#handling-whitespaces-and-comments-in-your-language) (`LAYOUT`
grammar rule) is not defined. If `LAYOUT` rule is given in the grammar it is
used instead and this parameter is ignored.

## build_tree

A boolean whose default value is `False`. If set to `True` parser will call
actions that will build the [parse tree](./parse_trees.md).

## prefer_shifts

By default set to `True` for LR parser and to `False` for GLR parser. In case
of [shift/reduce conflicts](./lr_parsing.md) this strategy would favor shift
over reduce. You can still
use [associativity rules](./disambiguation.md#associativity) to decide per
production.

You can disable this rule on per-production basis by using `nops` on the
production.

!!! note

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

!!! note

    Do not use `prefer_shifts_over_empty` if you don't understand the
    implications. Try to understand [conflicts](./lr_parsing.md) and
    [resolution strategies](./disambiguation.md).


## error_recovery

By default set to `False`. If set to `True` default error recovery will be used.
If set to a Python function, the function will be called to recover from errors.
For more information see [Error recovery](./handling_errors.md#error-recovery).

## start_production

By default the first rule of the grammar is the start rule. If you want to
change this default behavior — for example you want to create multiple parsers
from the same grammar with different start production — you can use this
parameter. The parameter accepts the `id` of the grammar production. To get the
`id` from the rule name use the `get_production_id(rule_name)` method of the
grammar.


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
is used to chose the type of LR tables to create. By default `LALR` tables are
used with a slight twist to avoid Reduce/Reduce conflicts that may happen with
pure LALR tables. This parameter should not be used in normal circumstances but
is provided more for experimentation purposes.


# `parse` and `parse_file` calls

`parse` call is used to parse input string or list of objects. For parsing of
textual file `parse_file` is used.

These two calls accepts the following parameters:

- **input_str** - first positional and mandatory parameter only for `parse` call -
  the input string/list of objects.

- **position** - the start position to parse from. By default 0.

- **context** - the [context object](./actions.md#the-context-object) to use. By
  default `None` - context object is created by the parser.

- **file_name** - first positional and mandatory parameter only for `parse_file`
  call - the name/path of the file to parse.


# Token

This class from `parglare.parser` is used to represent lookahead tokens. Token
is a concrete matched terminal from the input stream.

## Attributes

- **symbol** (`Terminal`) - terminal grammar symbol represented by this token,

- **value** (`list` or `str`) - matched part of input stream,

- **length** (`int`) - length of matched input.
