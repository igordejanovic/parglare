#!/usr/bin/env python3
from os.path import dirname, join
from parglare import Grammar, GLRParser
from tests import TESTS


class Result:
    def __init__(self, name, productions, nonterminals, lr_states):
        self.name = name
        self.productions = productions
        self.nonterminals = nonterminals
        self.lr_states = lr_states


def grammar_sizes():
    results = []
    for test_idx, test in enumerate(TESTS):
        test_root = join(dirname(__file__), f'test{test_idx+1}')
        g = Grammar.from_file(join(test_root, 'g.pg'))
        parser = GLRParser(g)
        productions = len(g.productions)
        nonterminals = len(g.nonterminals)
        states = len(parser.table.states)

        results.append(Result(test.name, productions, nonterminals, states))

    with open(join(dirname(__file__), 'reports', 'grammar-sizes.txt'), 'w') as f:
        f.write('|  Grammar  | productions | non-terminals | LALR automaton size |\n')
        for result in results:
            sizes_str = f'{result.productions:^13,d}|'\
                        f'{result.nonterminals:^15,d}|{result.lr_states:^21,d}'
            title = f'{result.name:^11s}'
            f.write(f'|{title}|{sizes_str}|\n')


if __name__ == '__main__':
    grammar_sizes()
