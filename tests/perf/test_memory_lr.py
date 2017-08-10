from os.path import dirname, join
from memory_profiler import profile
from parglare import Grammar, Parser


@profile
def run():
    g = Grammar.from_file('rhapsody.pg')

    this_folder = dirname(__file__)
    parser = Parser(g)

    # Small file
    parser.parse_file(join(this_folder, 'test_inputs', 'LightSwitch.rpy'))

    # Large file
    parser.parse_file(join(this_folder, 'test_inputs',
                           'LightSwitchDouble.rpy'))


if __name__ == '__main__':
    run()
