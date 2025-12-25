import contextlib
from pathlib import Path

import pytest  # noqa

from parglare import GLRParser, Grammar, Parser, SyntaxError

from ....utils import output_cmp

parsers = pytest.mark.parametrize(
    "parser_class, suffix",
    [
        (Parser, "lr"),
        (GLRParser, "glr"),
    ],
)

inputs = pytest.mark.parametrize(
    "name, input",
    [
        ("expected_expression", "2 + * 4"),
        ("expected_operator", "2 + 3 4 * 7"),
        ("unexpected_closing_parent", "2 + 3) * 4"),
        ("missing_closing_parent", "(2 + 3"),
    ],
)

grammar_file = Path(Path(__file__).parent, "expressions.pg")


@parsers
@inputs
def test_custom_hints(parser_class, suffix, name, input):
    # Make sure all compiled files are deleted.
    with contextlib.suppress(FileNotFoundError):
        grammar_file.with_suffix(".pgc").unlink()
    with contextlib.suppress(FileNotFoundError):
        grammar_file.with_suffix(".pgec").unlink()

    grammar = Grammar.from_file(grammar_file)
    parser = parser_class(grammar)

    err_file = Path(Path(__file__).parent, f"{name}_{suffix}.err")

    with pytest.raises(SyntaxError) as e:
        parser.parse(input)

    assert e.value.message is not None
    assert e.value.context_message is not None
    assert e.value.hint is not None

    output_cmp(err_file, str(e.value))
