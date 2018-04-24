from parglare.actions import get_action_decorator

action = get_action_decorator()


@action
def number(_, value):
    return float(value)
