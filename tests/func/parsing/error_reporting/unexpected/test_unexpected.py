import pytest  # noqa
from pathlib import Path
from parglare import Grammar, Parser, GLRParser, SyntaxError
from ....utils import output_cmp

parsers = pytest.mark.parametrize("parser_class", [Parser, GLRParser])


@parsers
def test_unexpected_token(parser_class):
    """Test disabling of ambiguous token error reporting"""
    grammar = Grammar.from_file(Path(Path(__file__).parent, "lex_ambiguous.pg"))
    parser = parser_class(grammar)

    input_file = Path(Path(__file__).parent, "unexpected_token.input")

    err_file = Path(Path(__file__).parent, "no_unexpected_token.err")

    with pytest.raises(SyntaxError) as e:
        parser.parse_file(input_file)

    output_cmp(err_file, str(e.value))

    grammar = Grammar.from_file(
        Path(Path(__file__).parent, "lex_ambiguous_unexpected.pg")
    )
    parser = parser_class(grammar)

    err_file = Path(Path(__file__).parent, "unexpected_token.err")

    with pytest.raises(SyntaxError) as e:
        parser.parse_file(input_file)

    output_cmp(err_file, str(e.value))
