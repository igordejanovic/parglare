# Define a variable with the python command to open a browser.
BROWSER := "uv run python -c 'import webbrowser, sys; webbrowser.open(sys.argv[1])'"
VERSION := `awk -F'"' '/^version/ {print $2}' pyproject.toml`

# Show all available recipes
[default]
help:
    @just --list --unsorted --list-prefix '📜   '

# remove all build, test, coverage and Python artifacts
clean: clean-build clean-pyc clean-test

# remove build artifacts
[private]
clean-build:
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -f {} +

# remove Python file artifacts
[private]
clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

# remove test and coverage artifacts
[private]
clean-test:
	rm -f .coverage
	rm -fr htmlcov/

# check style with ruff
lint flags="":
	uv run --no-default-groups --group test ruff check {{ flags }} parglare/ tests/func examples/

# run tests quickly with the default Python
test:  
	uv run --no-default-groups --group test pytest tests/func

# Run static type checks
types:  
	uv run --no-default-groups --group test mypy parglare

# check code coverage quickly with the default Python
coverage:  
	uv run --no-default-groups --group test coverage run --omit parglare/cli.py --source parglare -m pytest tests/func
	uv run --no-default-groups --group test coverage report --fail-under 90
	uv run --no-default-groups --group test coverage html
	{{BROWSER}} "htmlcov/index.html"

# Run all checks
check: check-format lint types coverage

# Format code with ruff
[no-cd]
format *paths=".":
    uv run ruff format {{ paths }}

[private]
check-format:
    uv run ruff format --check

# generate MkDocs HTML documentation
docs:  
	uv run --group docs mkdocs build
	{{BROWSER}} site/index.html

# compile the docs watching for changes
servedocs:  
	{{BROWSER}} "http://localhost:8000/"
	uv run --group docs mkdocs serve

# Publish latest docs
publish-docs-latest:
     uv run mike deploy latest -p

# Publish stable docs for major/minor versions
publish-docs-stable: publish-docs-latest
    uv run mike delete stable
    uv run mike deploy {{VERSION}} stable -p

# release package to PyPI test server
release-test: dist  
	uv run flit publish --repository test

# release package to PyPI
release: dist  
	uv run flit publish

# builds source and wheel package
dist: clean  
	uv run flit build
	gpg --armor --detach-sign dist/*.whl
	gpg --armor --detach-sign dist/*.tar.gz
	ls -l dist

# install the package to the active Python's site-packages
install: clean  
	uv pip install .

# Setup development environment
dev: clean  
	uv sync
