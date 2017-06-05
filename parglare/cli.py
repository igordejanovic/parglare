#!/usr/bin/env python
import sys
import argparse
from parglare import Grammar, ParseError, GrammarError
from parglare.export import grammar_pda_export
from parglare.tables import create_table, check_table
from parglare.closure import LR_1
from parglare.parser import first, follow


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

    commands = ['viz', 'check']
    commands_str = "'{}'".format("' or '".join(commands))

    parser = MyParser(description='parglare checker and PDA visualizer')
    parser.add_argument('cmd', help='Command - {}'.format(commands_str))
    parser.add_argument('grammar', help='parglare grammar file')
    parser.add_argument('-d', help='run in debug mode',
                        action='store_true')

    args = parser.parse_args()

    if args.cmd not in commands:
        print("Unknown command {}. Command must be one of"
              " {}.".format(args.cmd, commands_str))
        sys.exit(1)

    try:
        g = Grammar.from_file(args.grammar, debug=args.d)
        states, all_actions, all_goto = create_table(g)
    except (GrammarError, ParseError) as e:
        print("Error in grammar file.")
        print(e)
        sys.exit(1)

    if args.cmd == "viz":
        print("Generating '%s.dot' file for the grammar PDA." % args.grammar)
        print("To convert to png run 'dot -Tpng -O %s.dot'" % args.grammar)
        grammar_pda_export(states, all_actions, all_goto, "%s.dot" % args.grammar)
