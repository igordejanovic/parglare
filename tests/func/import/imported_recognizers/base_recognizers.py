from __future__ import unicode_literals
import re
from parglare import get_collector

recognizer = get_collector()
number_re = re.compile(r'\d+(\.\d+)*')
fqn_re = re.compile(r'\w+(\.\w+)*')


@recognizer('NUMERIC_ID')
def number(input, pos):
    number_match = number_re.match(input[pos:])
    if number_match:
        return input[pos:pos + len(number_match.group())]


@recognizer
def FQN(input, pos):
    fqn_match = fqn_re.match(input[pos:])
    if fqn_match:
        return input[pos:pos + len(fqn_match.group())]
