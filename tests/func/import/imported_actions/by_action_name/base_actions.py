from parglare import get_collector

action = get_collector()


@action
def number(_, value):
    return float(value)
