from parglare import get_collector

action = get_collector()


@action
def Calc(_, nodes):
    return nodes[-1]


@action
def Assignment(context, nodes):
    var_name, _, value = nodes
    context.extra[var_name] = float(value)


E = [
    lambda _, n: n[0] + n[2],
    lambda _, n: n[0] - n[2],
    lambda _, n: n[0] * n[2],
    lambda _, n: n[0] / n[2],
    lambda _, n: n[1],
    lambda context, n: context.extra[n[0]],
    lambda _, n: float(n[0])
]
action('E')(E)
