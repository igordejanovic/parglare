#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
import codecs
from setuptools import setup

VERSIONFILE = "parglare/__init__.py"
VERSION = None
for line in open(VERSIONFILE, "r").readlines():
    if line.startswith('__version__'):
        VERSION = line.split('"')[1]

if not VERSION:
    raise RuntimeError('No version defined in parglare.__init__.py')


README = codecs.open(os.path.join(os.path.dirname(__file__), 'README.rst'),
                     'r', encoding='utf-8').read()

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
        print("You probably want to also tag the version now:")
        print("  git tag -a {0} -m 'version {0}'".format(VERSION))
        print("  git push --tags")
    sys.exit()


setup(
    name='parglare',
    version=VERSION,
    description="A pure Python Scannerless LR/GLR parser",
    long_description=README,
    author="Igor R. Dejanovic",
    author_email='igorREPLACEWITHDOTdejanovic@gmail.com',
    url='https://github.com/igordejanovic/parglare',
    packages=[
        'parglare',
        'parglare.tables'
    ],
    package_dir={'parglare':
                 'parglare'},
    include_package_data=True,
    install_requires=['click'],
    tests_require=[
        'flake8',
        'tox',
        'coverage',
        'coveralls',
        'pytest',
    ],
    test_suite='tests',
    license="MIT license",
    zip_safe=False,
    keywords='parglare',
    entry_points={
        'console_scripts': [
            'pglr = parglare.cli:pglr'
        ]
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'Intended Audience :: Science/Research',
        'Topic :: Software Development :: Interpreters',
        'Topic :: Software Development :: Compilers',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Operating System :: OS Independent',
    ]
)
