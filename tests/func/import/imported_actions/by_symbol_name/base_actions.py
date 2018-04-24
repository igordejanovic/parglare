from parglare.actions import get_action_decorator

action = get_action_decorator()


@action
def NUMERIC_ID(_, value):
    return float(value)
