#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup
try:
    import pypandoc
    readme = pypandoc.convert('README.md', 'rst')
    history = pypandoc.convert('HISTORY.md', 'rst')
except(IOError, ImportError):
    readme = open('README.md').read()
    history = open('HISTORY.md').read()

requirements = [
    # TODO: put package requirements here
]

test_requirements = [
    # TODO: put package test requirements here
]

setup(
    name='parglare',
    version='0.1.0',
    description="A pure Python Scannerless LR (soon GLR) parser ",
    long_description=readme + '\n\n' + history,
    author="Igor R. Dejanovic",
    author_email='igor DOT dejanovic AT gmail DOT com',
    url='https://github.com/igordejanovic/parglare',
    packages=[
        'parglare',
    ],
    package_dir={'parglare':
                 'parglare'},
    include_package_data=True,
    install_requires=requirements,
    license="MIT license",
    zip_safe=False,
    keywords='parglare',
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
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Operating System :: OS Independent',
    ],
    test_suite='tests',
    tests_require=test_requirements
)
