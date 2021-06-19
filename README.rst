.. image:: https://raw.githubusercontent.com/igordejanovic/parglare/master/docs/images/parglare-logo.png

|build-status| |coverage| |docs| |status| |license| |python-versions|


A pure Python scannerless LR/GLR parser.


For more information see `the docs <http://www.igordejanovic.net/parglare/>`_.


Quick intro
-----------

This is just a small example to get the general idea. This example shows how to
parse and evaluate expressions with 5 operations with different priority and
associativity. Evaluation is done using semantic/reduction actions.

The whole expression evaluator is done in under 30 lines of code!

.. code:: python

    from parglare import Parser, Grammar

    grammar = r"""
    E: E '+' E  {left, 1}
     | E '-' E  {left, 1}
     | E '*' E  {left, 2}
     | E '/' E  {left, 2}
     | E '^' E  {right, 3}
     | '(' E ')'
     | number;

    terminals
    number: /\d+(\.\d+)?/;
    """

    actions = {
        "E": [lambda _, n: n[0] + n[2],
              lambda _, n: n[0] - n[2],
              lambda _, n: n[0] * n[2],
              lambda _, n: n[0] / n[2],
              lambda _, n: n[0] ** n[2],
              lambda _, n: n[1],
              lambda _, n: n[0]],
        "number": lambda _, value: float(value),
    }

    g = Grammar.from_string(grammar)
    parser = Parser(g, debug=True, actions=actions)

    result = parser.parse("34 + 4.6 / 2 * 4^2^2 + 78")

    print("Result = ", result)

    # Output
    # -- Debugging/tracing output with detailed info about grammar, productions,
    # -- terminals and nonterminals, DFA states, parsing progress,
    # -- and at the end of the output:
    # Result = 700.8


Installation
------------

- Stable version:

.. code:: shell

    $ pip install parglare

- Development version:

.. code:: shell

    $ git clone git@github.com:igordejanovic/parglare.git
    $ pip install -e parglare


License
-------

MIT

Python versions
---------------

Tested with 3.6-3.9

Credits
-------

Initial layout/content of this package was created with `Cookiecutter
<https://github.com/audreyr/cookiecutter>`_ and the
`audreyr/cookiecutter-pypackage <https://github.com/audreyr/cookiecutter-pypackage>`_ project template.


.. |build-status| image:: https://github.com/igordejanovic/parglare/actions/workflows/ci-linux-ubuntu.yml/badge.svg
   :target: https://github.com/igordejanovic/parglare/actions

.. |coverage| image:: https://coveralls.io/repos/github/igordejanovic/parglare/badge.svg?branch=master
   :target: https://coveralls.io/github/igordejanovic/parglare?branch=master

.. |docs| image:: https://img.shields.io/badge/docs-latest-green.svg
   :target: http://igordejanovic.net/parglare/latest/

.. |status| image:: https://img.shields.io/pypi/status/parglare.svg

.. |license| image:: https://img.shields.io/badge/License-MIT-blue.svg
   :target: https://opensource.org/licenses/MIT

.. |python-versions| image:: https://img.shields.io/pypi/pyversions/parglare.svg
