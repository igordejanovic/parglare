#!/usr/bin/env python
from __future__ import unicode_literals, print_function
import sys
import click
from parglare import Grammar, ParseError, GrammarError, GLRParser
from parglare.export import grammar_pda_export
from parglare.tables import create_table
from parglare.termui import prints, a_print, h_print
import parglare.termui as t


@click.group()
@click.option('--debug/--no-debug', default=False, help="Debug/trace output")
@click.option('--colors/--no-colors', default=True, help="Output coloring")
@click.pass_context
def pglr(ctx, debug, colors):
    """
    Command line interface for working with parglare grammars.
    """
    ctx.obj = {'debug': debug, 'colors': colors}


@pglr.command()
@click.argument('grammar_file', type=click.Path())
@click.pass_context
def check(ctx, grammar_file):
    debug = ctx.obj['debug']
    colors = ctx.obj['colors']
    check_get_grammar_table(grammar_file, debug, colors)


@pglr.command()
@click.argument('grammar_file', type=click.Path())
@click.pass_context
def viz(ctx, grammar_file):
    debug = ctx.obj['debug']
    colors = ctx.obj['colors']
    t.colors = colors
    grammar, table = check_get_grammar_table(grammar_file, debug, colors)
    prints("Generating '%s.dot' file for the grammar PDA." % grammar_file)
    prints("Use dot viewer (e.g. xdot) "
           "or convert to pdf by running 'dot -Tpdf -O %s.dot'" % grammar_file)
    t.colors = False
    grammar_pda_export(table, "%s.dot" % grammar_file)


@pglr.command()
@click.argument('grammar_file', type=click.Path())
@click.option('--input-file', '-f', type=click.Path(),
              help="Input file for tracing")
@click.option('--expression', '-e', help="Expression for tracing")
@click.pass_context
def trace(ctx, grammar_file, input_file, expression):
    if not (input_file or expression):
        prints('Expected either input_file or expression.')
        sys.exit(1)
    debug = ctx.obj['debug']
    colors = ctx.obj['colors']
    grammar, table = check_get_grammar_table(grammar_file, debug, colors)
    parser = GLRParser(grammar, debug=debug, debug_trace=debug,
                       debug_colors=colors)
    if expression:
        parser.parse(expression)
    else:
        parser.parse_file(input_file)


def check_get_grammar_table(grammar_file, debug, colors):
    try:
        g = Grammar.from_file(grammar_file, _no_check_recognizers=True,
                              debug_colors=colors)
        if debug:
            g.print_debug()
        table = create_table(g)
        if debug:
            table.print_debug()

        h_print("Grammar OK.")
        if table.sr_conflicts:
            a_print("There are {} Shift/Reduce conflicts."
                    .format(len(table.sr_conflicts)))
            prints("Either use 'prefer_shifts' parser mode, try to resolve "
                   "manually or use GLR parsing.".format(
                       len(table.sr_conflicts)))
        if table.rr_conflicts:
            a_print("There are {} Reduce/Reduce conflicts."
                    .format(len(table.rr_conflicts)))
            prints("Try to resolve manually or use GLR parsing.")

        if (table.sr_conflicts or table.rr_conflicts) and not debug:
            prints("Run in debug mode to print all the states.")

    except (GrammarError, ParseError) as e:
        print("Error in the grammar file.")
        print(e)
        sys.exit(1)

    return g, table


if __name__ == '__main__':
    pglr()
