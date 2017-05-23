"""
Common parsing actions.
"""


def pass_none(_, value):
    return None


def pass_nochange(_, value):
    return value


def pass_empty(_, value):
    """
    Used for EMPTY production alternative in collect.
    """
    return []


def pass_single(_, nodes):
    """
    Unpack single value and pass up.
    """
    return nodes[0]


def pass_value(_, nodes):
    """
    Used for productions which represent alternatives of terminals:
    Element = "a" | "b";
    If this action is attached to `Element` production it will be called
    with a list of `NodeTerm` instance and will return list with the matched
    string. This is used in conjuction with collect_* actions.
    """
    return nodes[0].value


def collect_single(_, nodes):
    return [nodes[0].value]


def collect_first(_, nodes):
    """
    Elements = Elements Element;
    or:
    Elements = Element Elements;
    """
    e1, e2 = nodes
    if e2 is not None:
        e1.append(e2)
    return e1


def collect_first_sep(_, nodes):
    """
    Elements = Elements "," Element;
    or:
    Elements = Element "," Elements;
    """
    e1, _, e2 = nodes
    if e2 is not None:
        e1.append(e2)
    return e1


# Used for productions of the form - one or more elements:
# Elements = Elements Element | Element;
collect = [
    collect_first,
    pass_nochange
]

# Used for productions of the form - one or more elements:
# Elements = Elements "," Element | Element;
collect_sep = [
    collect_first_sep,
    pass_nochange
]

# Used for productions of the form - zero or more elements:
# Elements = Elements Element | Element | EMPTY;
collect_optional = [
    collect_first,
    pass_nochange,
    pass_empty
]

# Used for productions of the form - zero or more elements:
# Elements = Elements "," Element | Element | EMPTY;
collect_sep_optional = [
    collect_first_sep,
    pass_nochange,
    pass_empty
]
