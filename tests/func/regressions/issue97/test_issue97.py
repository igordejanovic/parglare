from os.path import dirname, join
from parglare import Grammar, GLRParser


def test_import_plus_raises_keyerror():

    this_folder = dirname(__file__)
    grammar = Grammar.from_file(join(this_folder, 'first.pg'))
    GLRParser(grammar)
