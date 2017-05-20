def act_assignment(context, nodes):
    name = nodes[0]
    number = nodes[2]

    if not hasattr(context, 'variables'):
        context.variables = {}

    context.variables[name] = number


actions = {
    "Calc": lambda _, nodes: nodes[1],
    "Assignment": act_assignment,
    "E:1": lambda _, nodes: nodes[0] + nodes[2],
    "E:2": lambda _, nodes: nodes[0] - nodes[2],
    "E:3": lambda _, nodes: nodes[0] * nodes[2],
    "E:4": lambda _, nodes: nodes[0] / nodes[2],
    "E:5": lambda _, nodes: nodes[1],
    "E:6": lambda _, nodes: nodes[0],
    "E:7": lambda _, nodes: nodes[0],
    "Number": lambda _, value: float(value),
    "VariableName": lambda _, value: value,
    "VariableRef": lambda context, nodes: context.variables[nodes[0]],
}
