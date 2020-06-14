from parglare import get_collector

action = get_collector()


@action('base.NUMERIC_ID')
def numeric(_, value):
    return 43
