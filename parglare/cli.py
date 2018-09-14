#!/usr/bin/env python
from __future__ import unicode_literals, print_function
import sys
import click
from parglare import Grammar, ParseError, GrammarError, GLRParser
from parglare.export import grammar_pda_export
from parglare.tables import create_load_table
from parglare.termui import prints, a_print, h_print
import parglare.termui as t


@click.group()
@click.option('--debug/--no-debug', default=False, help="Debug/trace output")
@click.option('--colors/--no-colors', default=True, help="Output coloring")
@click.option('--prefer-shifts/--no-prefer-shifts', default=False,
              help="Prefer shifts over reductions.")
@click.option('--prefer-shifts-over-empty/--no-prefer-shifts-over-empty',
              default=True,
              help="Prefer shifts over empty reductions.")
@click.pass_context
def pglr(ctx, debug, colors, prefer_shifts, prefer_shifts_over_empty):
    """
    Command line interface for working with parglare grammars.
    """
    ctx.obj = {'debug': debug, 'colors': colors,
               'prefer_shifts': prefer_shifts,
               'prefer_shifts_over_empty': prefer_shifts_over_empty}


@pglr.command()
@click.argument('grammar_file', type=click.Path())
@click.pass_context
def compile(ctx, grammar_file):
    debug = ctx.obj['debug']
    colors = ctx.obj['colors']
    prefer_shifts = ctx.obj['prefer_shifts']
    prefer_shifts_over_empty = ctx.obj['prefer_shifts_over_empty']
    h_print('Compiling...')
    compile_get_grammar_table(grammar_file, debug, colors, prefer_shifts,
                              prefer_shifts_over_empty)


@pglr.command()
@click.argument('grammar_file', type=click.Path())
@click.pass_context
def viz(ctx, grammar_file):
    debug = ctx.obj['debug']
    colors = ctx.obj['colors']
    prefer_shifts = ctx.obj['prefer_shifts']
    prefer_shifts_over_empty = ctx.obj['prefer_shifts_over_empty']
    t.colors = colors
    grammar, table = compile_get_grammar_table(grammar_file, debug, colors,
                                               prefer_shifts,
                                               prefer_shifts_over_empty)
    prints("Generating '%s.dot' file for the grammar PDA." % grammar_file)
    prints("Use dot viewer (e.g. xdot) "
           "or convert to pdf by running 'dot -Tpdf -O %s.dot'" % grammar_file)
    t.colors = False
    grammar_pda_export(table, "%s.dot" % grammar_file)


@pglr.command()
@click.argument('grammar_file', type=click.Path())
@click.option('--input-file', '-f', type=click.Path(),
              help="Input file for tracing")
@click.option('--input', '-i', help="Input string for tracing")
@click.pass_context
def trace(ctx, grammar_file, input_file, input):
    if not (input_file or input):
        prints('Expected either input_file or input string.')
        sys.exit(1)
    colors = ctx.obj['colors']
    prefer_shifts = ctx.obj['prefer_shifts']
    prefer_shifts_over_empty = ctx.obj['prefer_shifts_over_empty']
    grammar, table = compile_get_grammar_table(grammar_file, True, colors,
                                               prefer_shifts,
                                               prefer_shifts_over_empty)
    parser = GLRParser(grammar, debug=True, debug_trace=True,
                       debug_colors=colors, prefer_shifts=prefer_shifts,
                       prefer_shifts_over_empty=prefer_shifts_over_empty)
    if input:
        parser.parse(input)
    else:
        parser.parse_file(input_file)


def compile_get_grammar_table(grammar_file, debug, colors, prefer_shifts,
                              prefer_shifts_over_empty):
    try:
        g = Grammar.from_file(grammar_file, _no_check_recognizers=True,
                              debug_colors=colors)
        if debug:
            g.print_debug()
        table = create_load_table(
            g, prefer_shifts=prefer_shifts,
            prefer_shifts_over_empty=prefer_shifts_over_empty,
            force_create=True)
        if debug or table.sr_conflicts or table.rr_conflicts:
            table.print_debug()

        if not table.sr_conflicts and not table.rr_conflicts:
            h_print("Grammar OK.")

        if table.sr_conflicts:
            if len(table.sr_conflicts) == 1:
                message = 'There is 1 Shift/Reduce conflict.'
            else:
                message = 'There are {} Shift/Reduce conflicts.'\
                          .format(len(table.sr_conflicts))
            a_print(message)
            prints("Either use 'prefer_shifts' parser mode, try to resolve "
                   "manually, or use GLR parsing.".format(
                       len(table.sr_conflicts)))
        if table.rr_conflicts:
            if len(table.rr_conflicts) == 1:
                message = 'There is 1 Reduce/Reduce conflict.'
            else:
                message = 'There are {} Reduce/Reduce conflicts.'\
                          .format(len(table.rr_conflicts))
            a_print(message)
            prints("Try to resolve manually or use GLR parsing.")

    except (GrammarError, ParseError) as e:
        print("Error in the grammar file.")
        print(e)
        sys.exit(1)

    return g, table


if __name__ == '__main__':
    pglr()
