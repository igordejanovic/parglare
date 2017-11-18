# -*- coding: utf-8 -*-
#######################################################################
# Testing parsing speed. This is used for the purpose of testing
#   of performance gains/loses for various approaches.
# Author: Igor R. Dejanovic <igor DOT dejanovic AT gmail DOT com>
# Copyright: (c) 2017 Igor R. Dejanovic <igor DOT dejanovic AT gmail DOT com>
# License: MIT License
#######################################################################
from __future__ import print_function, unicode_literals

import time
from os.path import dirname, join, getsize
from parglare import Grammar


def timeit(parser_class, file_name, message, **kwargs):
    print(message, 'File:', file_name)
    file_name = join(dirname(__file__), 'test_inputs', file_name)
    file_size = getsize(file_name)
    print('File size: {:.2f}'.format(file_size/1000), 'KB')

    this_folder = dirname(__file__)
    g = Grammar.from_file(join(this_folder, 'rhapsody.pg'))
    parser = parser_class(g, **kwargs)

    t_start = time.time()
    with open(file_name) as f:
        parser.parse(f.read())
    t_end = time.time()

    print('Elapsed time: {:.2f}'.format(t_end - t_start), 'sec')
    print('Speed = {:.2f}'.format(file_size/1000/(t_end - t_start)),
          'KB/sec\n')


def run_tests(parser_class, **kwargs):

    # Small file
    file_name_small = 'LightSwitch.rpy'
    # Large file
    file_name_large = 'LightSwitchDouble.rpy'

    # Without semantic actions
    for i in range(3):
        timeit(parser_class, file_name_small,
               '{}. Small file without tree building.'.format(i + 1), **kwargs)
        timeit(parser_class, file_name_large,
               '{}. Large file without tree building.'.format(i + 1), **kwargs)

    # With tree building.
    for i in range(3):
        timeit(parser_class, file_name_small,
               '{}. Small file with tree building.'.format(i + 1),
               build_tree=True, **kwargs)
        timeit(parser_class, file_name_large,
               '{}. Large file with tree building.'.format(i + 1),
               build_tree=True, **kwargs)
