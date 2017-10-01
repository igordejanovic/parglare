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


def pass_inner(_, nodes):
    """
    Pass inner value up, e.g. for parentheses '(' token ')'.
    """
    return nodes[1]


def pass_single_if_exists(_, nodes):
    """
    Unpack single value and pass up if value exists, if not return None.
    """
    if nodes:
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
    Used for:
    Elements = Elements Element;
    """
    e1, e2 = nodes
    if e2 is not None:
        e1.append(e2)
    return e1


def collect_first_sep(_, nodes):
    """
    Used for:
    Elements = Elements "," Element;
    """
    e1, _, e2 = nodes
    if e2 is not None:
        e1.append(e2)
    return e1


def collect_right_first(_, nodes):
    """
    Used for:
    Elements = Element Elements;
    """
    e1, e2 = [nodes[0]], nodes[1]
    e1.extend(e2)
    return e1


def collect_right_first_sep(_, nodes):
    """
    Used for:
    Elements = Element "," Elements;
    """
    e1, e2 = [nodes[0]], nodes[2]
    e1.extend(e2)
    return e1


# Used for productions of the form - one or more elements:
# Elements: Elements Element | Element;
collect = [
    collect_first,
    pass_nochange
]

# Used for productions of the form - one or more elements:
# Elements: Elements "," Element | Element;
collect_sep = [
    collect_first_sep,
    pass_nochange
]

# Used for productions of the form - zero or more elements:
# Elements: Elements Element | Element | EMPTY;
collect_optional = [
    collect_first,
    pass_nochange,
    pass_empty
]

# Used for productions of the form - zero or more elements:
# Elements: Elements "," Element | Element | EMPTY;
collect_sep_optional = [
    collect_first_sep,
    pass_nochange,
    pass_empty
]

# Used for productions of the form - one or more elements:
# Elements: Element Elements | Element;
collect_right = [
    collect_right_first,
    pass_nochange
]

# Used for productions of the form - one or more elements:
# Elements: Element "," Elements | Element;
collect_right_sep = [
    collect_right_first_sep,
    pass_nochange
]

# Used for productions of the form - zero or more elements:
# Elements: Element Elements | Element | EMPTY;
collect_right_optional = [
    collect_right_first,
    pass_nochange,
    pass_empty
]

# Used for productions of the form - zero or more elements:
# Elements: Element "," Elements | Element | EMPTY;
collect_right_sep_optional = [
    collect_right_first_sep,
    pass_nochange,
    pass_empty
]

# Used for the production of the form:
# OptionalElement: Element | EMTPY;
optional = [
    pass_single,
    pass_none
]


def obj(context, nodes, **attrs):
    """
    Creates Python object with the attributes created from named matches.
    This action is used as default action for rules with named matches.
    """
    grammar = context.parser.grammar
    rule_name = context.production.symbol.name

    cls = grammar.classes[rule_name]
    instance = cls(**attrs)

    return instance
