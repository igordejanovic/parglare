from parglare import Grammar


grammar = Grammar.from_string("""
    start: ab;
    ab: "a" ab "b" | EMPTY;
""")

start_symbol = 'start'
