from parglare import get_collector

action = get_collector()


@action
def NUMERIC_ID(_, value):
    return float(value)
