import contextlib
from pathlib import Path

import pytest  # noqa

from parglare import GLRParser, Grammar, Parser, SyntaxError

from ....utils import output_cmp

inputs = pytest.mark.parametrize("name, input", [
    ('expected_expression', '2 + * 4'),
    ('expected_operator', '2 + 3 4 * 7'),
    ('unexpected_closing_parent', '2 + 3) * 4'),
    ('missing_closing_parent', '(2 + 3'),
])

grammar_file = Path(Path(__file__).parent, 'expressions.pg')


@inputs
def test_custom_hints_lr(name, input):

    # Make sure all compiled files are deleted.
    with contextlib.suppress(FileNotFoundError):
        grammar_file.with_suffix('.pgc').unlink()
    with contextlib.suppress(FileNotFoundError):
        grammar_file.with_suffix('.pgec').unlink()

    grammar = Grammar.from_file(grammar_file)
    parser = Parser(grammar)

    err_file = Path(Path(__file__).parent, f'{name}_lr.err')

    with pytest.raises(SyntaxError) as e:
        parser.parse(input)

    output_cmp(err_file, str(e.value))
    

@inputs
def test_custom_hints_glr(name, input):

    # Make sure all compiled files are deleted.
    with contextlib.suppress(FileNotFoundError):
        grammar_file.with_suffix('.pgc').unlink()
    with contextlib.suppress(FileNotFoundError):
        grammar_file.with_suffix('.pgec').unlink()

    grammar = Grammar.from_file(Path(Path(__file__).parent, 'expressions.pg'))
    parser = GLRParser(grammar)

    err_file = Path(Path(__file__).parent, f'{name}_glr.err')

    with pytest.raises(SyntaxError) as e:
        parser.parse(input)

    output_cmp(err_file, str(e.value))
