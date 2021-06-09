import pytest   # noqa
import os
import sys
import glob
import importlib
from itertools import chain


skip_examples = [
    'molecular_formulas',
    'custom_table_caching',
    'c/'
]

examples_pat = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                            '../../examples/*/*.py')
examples = [f for f in glob.glob(examples_pat)
            if not any([x in f
                        for x in chain(['__init__.py'],
                                       (f'examples/{example}'
                                        for example in skip_examples))])]


@pytest.mark.parametrize("example", examples)
def test_examples(example):
    example_dir = os.path.dirname(example)
    sys.path.insert(0, example_dir)
    (module_name, _) = os.path.splitext(os.path.basename(example))
    m = importlib.import_module(module_name)

    if hasattr(m, 'main'):
        m.main(debug=False)
