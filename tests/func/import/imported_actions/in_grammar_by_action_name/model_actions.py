from __future__ import unicode_literals
from parglare import get_collector

action = get_collector()


@action('base.numeric')
def number(_, value):
    "This action is overriding by action name in 'base' module."
    return 43
