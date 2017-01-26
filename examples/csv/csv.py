from __future__ import unicode_literals
from parglare import Grammar, Parser

grammar = r"""
CSVFile = OptionalNewLines Records OptionalNewLines;
Records = Record | Records OptionalNewLines Record;
Record = Fields NewLine;
Fields = Fields "," Field | Field;
Field = QuotedField | FieldContent;
NewLines = NewLine | NewLines NewLine;
OptionalNewLines = NewLines | EMPTY;
QuotedField = "\"" FieldContentQuoted "\"";
FieldContent = /[^,\n]+/;
FieldContentQuoted = /(("")|([^"]))+/;
NewLine = "\n";
"""


def list_one_or_more_sep(_, nodes):
    if len(nodes) == 1:
        res = [nodes[0]]
    else:
        res = nodes[0]
        res.append(nodes[2])
    return res


def list_one_or_more(_, nodes):
    if len(nodes) == 1:
        res = [nodes[0]]
    else:
        res = nodes[0]
        res.append(nodes[1])
    return res


def pass_value(_, value):
    return value


def pass_single_node(_, nodes):
    return nodes[0]


def pass_none(_, n):
    return None


# Semantic Actions
actions = {
    "CSVFile": lambda _, nodes: nodes[1],
    "Records": list_one_or_more_sep,
    "Record": lambda _, nodes: nodes[0],
    "Fields": list_one_or_more_sep,
    "Field": pass_single_node,
    "QuotedField": lambda _, nodes: nodes[1],
    "FieldContent": pass_value,
    "FieldContentQuoted": lambda _, value: value[3:],
    "NewLines": pass_none,
    "NewLine": pass_none,
    "OptionalNewLines": pass_none,
}


def main(debug=False):
    g = Grammar.from_string(grammar)
    parser = Parser(g, ws='\t ', actions=actions, debug=debug)

    input_str = """
    First, Second with multiple words, "Third quoted"


    Next line, Previous line has newlines, 2
    Another Line, 34.45, "Quoted", field


    """

    res = parser.parse(input_str)

    print("Input:\n", input_str)
    print("Result = ", res)


if __name__ == "__main__":
    main(debug=True)
