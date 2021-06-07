import os
import re
from parglare import Grammar, GLRParser


def main(debug=False):
    this_folder = os.path.dirname(__file__)
    g = Grammar.from_file(os.path.join(this_folder, 'c.pg'),
                          re_flags=re.MULTILINE | re.VERBOSE)
    parser = GLRParser(g, debug=debug, debug_colors=True)

    # The input is C code after preprocessing
    forest = parser.parse_file(os.path.join(this_folder, f'f_drawgraph.i'))

    # print('Solutions: ', len(forest))
    print('Ambiguities: ', forest.ambiguities)
    import pudb; pudb.set_trace()

if __name__ == "__main__":
    main(debug=False)
