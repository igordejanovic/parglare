import os
from parglare import Grammar, Parser


def main(debug=False):

    this_folder = os.path.dirname(__file__)
    grammar_file = os.path.join(this_folder, 'rhapsody.pg')
    g = Grammar.from_file(grammar_file, debug=debug, debug_colors=True)
    parser = Parser(g, build_tree=True, debug=debug, debug_colors=True)

    with open(os.path.join(this_folder, 'LightSwitch.rpy'), 'r') as f:
        result = parser.parse(f.read())
        print(result.to_str())


if __name__ == '__main__':
    main(debug=True)
