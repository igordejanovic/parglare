from __future__ import unicode_literals
from parglare import Grammar, Parser

grammar = r"""
@pass_inner
CSVFile: OptionalNewLines Records OptionalNewLines;
@collect_sep
Records: Records OptionalNewLines Record| Record;
@pass_single
Record: Fields NewLine;
@collect_sep
Fields: Fields "," Field | Field;
Field: QuotedField | FieldContent;
NewLines: NewLine | NewLines NewLine;
OptionalNewLines: NewLines | EMPTY;
@pass_inner
QuotedField: "\"" FieldContentQuoted "\"";

terminals
FieldContent: /[^,\n]+/;
FieldContentQuoted: /(("")|([^"]))+/;
NewLine: "\n";
"""


def main(debug=False):
    g = Grammar.from_string(grammar)
    parser = Parser(g, ws='\t ', debug=debug, debug_colors=True)

    input_str = """
    First, Second with multiple words, "Third, quoted with comma"


    Next line, Previous line has newlines, 2
    Another Line, 34.45, "Quoted", field


    """

    res = parser.parse(input_str)

    print("Input:\n", input_str)
    print("Result = ", res)


if __name__ == "__main__":
    main(debug=True)
