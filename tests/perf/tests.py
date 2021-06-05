from collections import namedtuple

Test = namedtuple('Test', 'name lr glr')

TESTS = [
    # Name, LR, GLR
    Test('JSON', True, True),
    Test('BibTeX', True, True),
    Test('Java', False, True)
]
