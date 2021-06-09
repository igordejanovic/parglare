import os
from parglare import Grammar, Parser


def main(debug=False):
    this_folder = os.path.dirname(__file__)
    g = Grammar.from_file(os.path.join(this_folder, 'json.pg'))
    parser = Parser(g, debug=debug, debug_colors=True)

    for i in range(5):
        result = parser.parse_file(os.path.join(this_folder, f'example{i+1}.json'))
        print(result)


if __name__ == "__main__":
    main(debug=True)
