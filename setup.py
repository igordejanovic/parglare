#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import os
from setuptools import setup
from pathlib import Path
this_dir = Path(__file__).absolute().parent

if sys.argv[-1].startswith('publish'):
    if os.system("pip list | grep wheel"):
        print("wheel not installed.\nUse `pip install wheel`.\nExiting.")
        sys.exit()
    if os.system("pip list | grep twine"):
        print("twine not installed.\nUse `pip install twine`.\nExiting.")
        sys.exit()
    os.system("python setup.py sdist bdist_wheel")
    if sys.argv[-1] == 'publishtest':
        os.system("twine upload -r test dist/*")
    else:
        os.system("twine upload dist/*")
    sys.exit()

if __name__ == "__main__":
    setup(use_scm_version={
        "write_to": str(this_dir / "parglare" / "version.py"),
        "write_to_template": '__version__ = "{version}"\n',
    })
