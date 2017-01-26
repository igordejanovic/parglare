===============================
parglare
===============================


.. image:: https://img.shields.io/pypi/v/parglare.svg
        :target: https://pypi.python.org/pypi/parglare

.. image:: https://img.shields.io/travis/igordejanovic/parglare.svg
        :target: https://travis-ci.org/igordejanovic/parglare

.. image:: https://readthedocs.org/projects/parglare/badge/?version=latest
        :target: https://parglare.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status

.. image:: https://pyup.io/repos/github/igordejanovic/parglare/shield.svg
     :target: https://pyup.io/repos/github/igordejanovic/parglare/
     :alt: Updates


A pure Python Scannerless LR parser (will be GLR soon) with LALR and SLR tables.

* Free software: MIT license
* Documentation: TODO


What is done
------------

* SLR and LALR tables calculation (LALR is the default)
* Scannerless LR(1) parsing
* Declarative associativity and priority based conflict resolution for productions
* Lexical disambiguation strategy
* Priority resolution for terminals
* Semantic actions and default actions which builds the parse tree (controlled
  by ``actions`` and ``default_actions`` parameters for the ``Parser`` class).
* Debug print/tracing (set ``debug=True`` to the ``Parser`` instantiation).
* Tests
* Few examples (see ``examples`` folder)

TODO
----

* Docs
* Tables caching/loading
* Support for language comments
* GLR parsing
* Error recovery

Quick intro
-----------

This is just a small example to get the general idea. Until docs is done see
the ``example`` folder and ``tests` for more.

.. code-block:: python

    from parglare import Parser, Grammar

    grammar = r"""
    E = E '+' E  {left, 1}
      | E '-' E  {left, 1}
      | E '*' E  {left, 2}
      | E '/' E  {left, 2}
      | E '^' E  {right, 3}
      | '(' E ')';
    E = number;
    number = /\d+(\.\d+)?/;
    """

    actions = {
        "E:0": lambda _, nodes: nodes[0] + nodes[2],
        "E:1": lambda _, nodes: nodes[0] - nodes[2],
        "E:2": lambda _, nodes: nodes[0] * nodes[2],
        "E:3": lambda _, nodes: nodes[0] / nodes[2],
        "E:4": lambda _, nodes: nodes[0] ** nodes[2],
        "E:5": lambda _, nodes: nodes[1],
        "E:6": lambda _, nodes: nodes[0],
        "number": lambda _, value: float(value),
    }

    g = Grammar.from_string(grammar)
    parser = Parser(g, debug=True, actions=actions)

    result = parser.parse("34 + 4.6 / 2 * 4^2^2 + 78")

    print("Result = ", result)

    # Output
    # -- Debuging/tracing output with detailed info about grammar, productions,
    # -- terminals and nonterminals, DFA states, parsing progress,
    # -- and at the end of the output:
    # Result = 700.8


Credits
---------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage

