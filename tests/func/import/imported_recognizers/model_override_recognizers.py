from parglare import get_collector

recognizer = get_collector()


@recognizer('base.NUMERIC_ID')
def number(input, pos):
    '''Check override'''
    pass


@recognizer('base.COMMA')
def comma_recognizer(input, pos):
    if input[pos] == ',':
        return input[pos:pos + 1]
