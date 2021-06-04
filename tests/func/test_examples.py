import pytest   # noqa
import os
import sys
import glob
import importlib


def test_examples():

    examples_pat = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                                '../../examples/*/*.py')

    # Filter out __init__.py
    examples = [f for f in glob.glob(examples_pat)
                if not any([x in f for x in ['__init__.py',
                                             'molecular',
                                             'custom_table_caching']])]
    for e in examples:
        example_dir = os.path.dirname(e)
        sys.path.insert(0, example_dir)
        (module_name, _) = os.path.splitext(os.path.basename(e))
        m = importlib.import_module(module_name)

        if hasattr(m, 'main'):
            m.main(debug=False)
