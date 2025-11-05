# Contributing

Contributions are welcome, and they are greatly appreciated! Every little bit
helps, and credit will always be given.

You can contribute in many ways:


## Types of Contributions

### Report Bugs

Report bugs at https://github.com/igordejanovic/parglare/issues.

If you are reporting a bug, please include:

- Your operating system name and version.
- Any details about your local setup that might be helpful in troubleshooting.
- Detailed steps to reproduce the bug.


### Fix Bugs

Look through the GitHub issues for bugs. Anything tagged with "bug" and "help
wanted" is open to whoever wants to implement it.


### Implement Features

Look through the GitHub issues for features. Anything tagged with "enhancement"
and "help wanted" is open to whoever wants to implement it. Please, discuss
about your plans before implementation.


### Write Documentation

parglare could always use more documentation, whether as part of the official
parglare docs, in docstrings, or even on the web in blog posts, articles, and
such.


### Submit Feedback

The best way to send feedback is to file an issue at
https://github.com/igordejanovic/parglare/issues.

If you are proposing a feature:

- Explain in detail how it would work.
- Keep the scope as narrow as possible, to make it easier to implement.
- Remember that this is a volunteer-driven project, and that contributions are
  welcome :)


## Get Started!

Ready to contribute? Here's how to set up `parglare` for local development.

1. [Install uv](https://docs.astral.sh/uv/getting-started/installation/) Python
   package/project manager.

2. Fork the `parglare` repo on GitHub.

3. Clone your fork locally:

        $ git clone git@github.com:your_name_here/parglare.git
        

4. Install your local copy into a virtual environment. This is how you set up
   your fork for local development:

        $ cd parglare/
        $ uv venv 
        $ source .venv/bin/activate
        $ uv sync

   This is needed just the first time. To work on parglare later you just need
   to activate the virtual environment for each new terminal session:

        $ cd parglare/
        $ source .venv/bin/activate

5. Create a branch for local development::

        $ git checkout -b name-of-your-bugfix-or-feature

   Now you can make your changes locally.

6. When you're done making changes, run tests:

        $ ./runtests.sh

   and verify that all tests pass.

7. Commit your changes and push your branch to GitHub:

        $ git add .
        $ git commit -m "Your detailed description of your changes."
        $ git push origin name-of-your-bugfix-or-feature

   Check [this](https://chris.beams.io/posts/git-commit/) on how to write nice
   git log messages.

8. Submit a pull request through the GitHub website. CI will run the tests for
   all supported Python versions. Check in the GitHub UI that all pipelines pass.


## Pull Request Guidelines

Before you submit a pull request, check that it meets these guidelines:

1. The pull request should include tests.
2. If the pull request adds/changes functionality, the docs should be updated.
3. The pull request should work for Python 3.8-3.14. Check
   https://travis-ci.org/igordejanovic/parglare/pull_requests and make sure that
   the tests pass for all supported Python versions.


## Tips

To run a subset of tests:

```
$ pytest tests/func/mytest.py
```

or a single test:

```
$ pytest tests/func/mytest.py::some_test
```
