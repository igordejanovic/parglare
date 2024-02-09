from os.path import dirname, join

from parglare import GLRParser, Grammar


def main(debug=False):
    THIS_DIR = dirname(__file__)
    g = Grammar.from_file(join(THIS_DIR, 'bibtex.pg'))

    parser = GLRParser(g)

    forest = parser.parse_file(join(THIS_DIR, 'test.bib'))
    print(f'Solutions: {len(forest)}')
    print(f'Ambiguities: {forest.ambiguities}')
    if debug:
        with open('forest.txt', 'w') as f:
            f.write(forest.to_str())
        print('See forest.txt')


if __name__ == "__main__":
    main(debug=True)
