from parglare import get_collector


def test_collector_can_use_unicode_in_python_2():

    action = get_collector()

    def f(context, node):
        return node

    action('f_action')(f)
