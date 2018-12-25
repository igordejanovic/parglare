from parglare import get_collector

recognizer = get_collector()


@recognizer
def A(input, pos):
    return [input[pos]]


# This should raise an exception as there is no `B` terminal in the grammar
@recognizer
def B(input, pos):
    return [input[pos]]
