from __future__ import unicode_literals
from parglare import Grammar, Parser
from parglare.actions import pass_inner, pass_nochange, pass_single, \
    collect_sep

grammar = r"""
CSVFile: OptionalNewLines Records OptionalNewLines;
Records: Records OptionalNewLines Record| Record;
Record: Fields NewLine;
Fields: Fields "," Field | Field;
Field: QuotedField | FieldContent;
NewLines: NewLine | NewLines NewLine;
OptionalNewLines: NewLines | EMPTY;
QuotedField: "\"" FieldContentQuoted "\"";
FieldContent: /[^,\n]+/;
FieldContentQuoted: /(("")|([^"]))+/;
NewLine: "\n";
"""


# Semantic Actions
actions = {
    "CSVFile": pass_inner,
    "Records": collect_sep,
    "Record": pass_single,
    "Fields": collect_sep,
    "Field": pass_single,
    "QuotedField": pass_inner,
    "FieldContent": pass_nochange,
    "FieldContentQuoted": pass_nochange,
}


def main(debug=False):
    g = Grammar.from_string(grammar)
    parser = Parser(g, ws='\t ', actions=actions, debug=debug)

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
