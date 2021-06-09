"""
This is work in progress
"""
import os
import re
from parglare import Grammar, GLRParser


def main(debug=False):
    this_folder = os.path.dirname(__file__)
    g = Grammar.from_file(os.path.join(this_folder, 'c.pg'),
                          re_flags=re.MULTILINE | re.VERBOSE)
    parser = GLRParser(g, debug=debug, debug_colors=True)

    # The input is C code after preprocessing
    forest = parser.parse_file(os.path.join(this_folder, 'example.c'))

    print('Solutions: ', len(forest))
    print('Ambiguities: ', forest.ambiguities)


if __name__ == "__main__":
    main(debug=False)
