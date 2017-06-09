#!/usr/bin/env python
import sys
import argparse
from parglare import Grammar, ParseError, GrammarError, GLRParser
from parglare.export import grammar_pda_export
from parglare.tables import create_table


def pglr():
    """
    pglr console command.
    """

    class MyParser(argparse.ArgumentParser):
        """
        Custom argument parser for printing help message in case of an error.
        See http://stackoverflow.com/questions/4042452/display-help-message-with-python-argparse-when-script-is-called-without-any-argu
        """
        def error(self, message):
            sys.stderr.write('error: %s\n' % message)
            self.print_help()
            sys.exit(2)

    commands = ['viz', 'check', 'trace']
    commands_str = "'{}'".format("' or '".join(commands))

    parser = MyParser(description='parglare checker and visualizer')
    parser.add_argument('cmd', help='Command - {}'.format(commands_str))
    parser.add_argument('grammar', help='parglare grammar file')
    parser.add_argument('input_file',
                        help='input file for GLR trace subcommand.',
                        nargs='?')
    parser.add_argument('-d', help='run in debug mode',
                        action='store_true')
    parser.add_argument('-i',
                        help='input_file for trace is input string, not file.',
                        action='store_true')

    args = parser.parse_args()

    if args.cmd not in commands:
        print("Unknown command {}. Command must be one of"
              " {}.".format(args.cmd, commands_str))
        sys.exit(1)

    try:
        g = Grammar.from_file(args.grammar)
        if args.d:
            g.print_debug()
        table = create_table(g)
        if args.d:
            table.print_debug()

        print("Grammar OK.")
    except (GrammarError, ParseError) as e:
        print("Error in grammar file.")
        print(e)
        sys.exit(1)

    if args.cmd == "viz":
        print("Generating '%s.dot' file for the grammar PDA." % args.grammar)
        print("Use dot viewer (e.g. xdot)")
        print("or convert to pdf by running 'dot -Tpdf -O %s.dot'"
              % args.grammar)
        grammar_pda_export(table, "%s.dot" % args.grammar)

    elif args.cmd == "trace":
        if not args.input_file:
            print("input_file is mandatory for trace command.")
            sys.exit(1)
        parser = GLRParser(g, debug=True)
        if args.i:
            parser.parse(args.input_file)
        else:
            parser.parse_file(args.input_file)
