from os.path import dirname, join

from parglare import GLRParser, Grammar


def test_import_plus_raises_keyerror():

    this_folder = dirname(__file__)
    grammar = Grammar.from_file(join(this_folder, 'base.pg'))
    GLRParser(grammar)

    grammar = Grammar.from_file(join(this_folder, 'overrider.pg'))
    GLRParser(grammar)
