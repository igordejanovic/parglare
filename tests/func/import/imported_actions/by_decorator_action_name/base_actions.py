from __future__ import unicode_literals
from parglare.actions import get_action_decorator

action = get_action_decorator()


@action('number')
def NUMERIC(_, value):
    return float(value)
