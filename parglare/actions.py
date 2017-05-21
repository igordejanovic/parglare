"""
Common parsing actions.
"""


def pass_none(_, value):
    """
    Used to suppress terminals.
    """
    return None


def pass_nochange(_, value):
    return value


def pass_single(_, nodes):
    """
    Unpack single value and pass up.
    """
    return nodes[0]


def pass_single_value(_, nodes):
    """
    Used for productions which represent alternatives of terminals:
    Element = "a" | "b";
    And a matched string value is needed upstream.
    """
    return nodes[0].value


def collect_single(_, nodes):
    """
    Used for productions which represent alternatives of terminals:
    Element = "a" | "b";
    And a matched string value packed in list is needed upstream.
    """
    return [nodes[0].value]


def pass_empty_list(_, value):
    """
    Used to suppress EMPTY match in collect actions.
    """
    return []


def collect_first(_, nodes):
    """
    Elements = Elements Element;
    or:
    Elements = Element Elements;
    """
    e1, e2 = nodes
    e1.extend(e2)
    return e1


def collect_first_sep(_, nodes):
    """
    Elements = Elements "," Element;
    or:
    Elements = Element "," Elements;
    """
    e1, _, e2 = nodes
    e1.extend(e2)
    return e1


# Used for productions of the form - one or more elements:
# Elements = Elements Element | Element;
collect = [
    collect_first,
    pass_single
]

# Used for productions of the form - one or more elements:
# Elements = Elements "," Element | Element;
collect_sep = [
    collect_first_sep,
    pass_single
]

# Used for productions of the form - zero or more elements:
# Elements = Elements Element | Element | EMPTY;
collect_optional = [
    collect_first,
    pass_single,
    pass_empty_list
]

# Used for productions of the form - zero or more elements:
# Elements = Elements "," Element | Element | EMPTY;
collect_sep_optional = [
    collect_first_sep,
    pass_single,
    pass_empty_list
]
