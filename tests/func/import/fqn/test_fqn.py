import os
from parglare import Grammar

this_folder = os.path.dirname(__file__)


def test_fqn_constructed_by_first_import_path():

    g = Grammar.from_file(os.path.join(this_folder, 'A.pg'))

    assert g.get_terminal('B.C.CTerm')
    assert not g.get_terminal('C.CTerm')
    assert g.get_nonterminal('B.C.CRule')
    assert not g.get_nonterminal('C.CRule')
