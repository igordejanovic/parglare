from parglare.tables import create_table, LALR
from parglare.tables.persist import table_to_serializable

from grammar import grammar, start_symbol


table = create_table(
    grammar,
    start_production=grammar.get_production_id(start_symbol),
    itemset_type=LALR,
    prefer_shifts=False,
    prefer_shifts_over_empty=False,
)
serializable_table = table_to_serializable(table)

with open('_table.py', 'w') as f:
    f.write('table = ')
    f.write(repr(serializable_table))
