from parglare import GLRParser
from parglare.tables.persist import table_from_serializable

from _table import table
from grammar import grammar


table = table_from_serializable(table, grammar)
parser = GLRParser(grammar, table=table)

print(parser.parse('aaabbb'))
