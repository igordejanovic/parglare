def act_assignment(context, nodes):
    name = nodes[0]
    number = nodes[2]

    # Use context.extra to collect variables
    if context.extra is None:
        context.extra = {}

    context.extra[name] = number


actions = {
    "Calc": lambda _, nodes: nodes[1],
    "Assignment": act_assignment,
    "E": [lambda _, nodes: nodes[0] + nodes[2],
          lambda _, nodes: nodes[0] - nodes[2],
          lambda _, nodes: nodes[0] * nodes[2],
          lambda _, nodes: nodes[0] / nodes[2],
          lambda _, nodes: nodes[1],
          lambda _, nodes: nodes[0],
          lambda _, nodes: nodes[0]],
    "Number": lambda _, value: float(value),
    "VariableName": lambda _, value: value,
    "VariableRef": lambda context, nodes: context.extra[nodes[0]],
}
