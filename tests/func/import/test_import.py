import os
from parglare import Grammar

this_folder = os.path.dirname(__file__)


def test_import():
    g = Grammar.from_file(os.path.join(this_folder, 'first.pg'))
    assert g
