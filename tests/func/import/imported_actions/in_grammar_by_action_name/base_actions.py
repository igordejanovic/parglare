from parglare import get_collector

action = get_collector()


@action('numeric')
def NUMERIC_ID(_, value):
    return float(value)
