# The grammar object and related APIs

After you write your grammar either as a Python string or as a separate file the
next step is to instantiate the grammar object that will be used to create the
parser.

There are two factory methods defined on `Grammar` class for creating the
`Grammar` instance:

- `Grammar.from_string(grammar)` - if your grammar is given as a Python string,
- `Grammar.from_file(file_path)` - if the grammar is given as a separate file.

Both methods return initialized `Grammar` object that is passed as the first and
the only mandatory parameter to the `Parser/GLRParser` constructor.


## Grammar factory methods additional parameters

Both methods `from_string` and `from_file` accept additional optional
parameters:

- `recognizers` - a dict of custom recognizers. These recognizers are mandatory
  if a non-textual content is being parsed and the grammar terminals don't
  provide recognizers. See [recognizers section](./recognizers.md) for more
  information.

- `debug` - set to `True` to put the grammar in debug/trace mode. `False` by
  default. See [debugging section](./debugging.md) for more information.

- `debug_parse` - set to `True` to debug/trace grammar file/string parsing.
  `False` by default.

- `debug_colors` - set to `True` to use colorized debug/trace output. `False` by
  default.


## Grammar object API

### Attributes

- **terminals** - a set of terminals (instances of `Terminal`);

- **nonterminals** - a set of non-terminal (instances of `NonTerminal`);

- **root_symbol** - grammar symbol of the start/root rule. By default this is
  the first rule in the grammar;

- **productions** - a list of productions (`Production` instances);

- **recognizers** - a dict of user supplied recognizers keyed by the terminal
  rule name;

- **classes** - a dict of Python classes dynamically created for rules
  using [named matches](./grammar_language.md#named-matches) keyed by the rule
  name.

### Methods

- **print_debug()** - prints detailed debug/trace info;

- **get_terminal(name)** - gets the terminal by the given name or `None` if
  not found;

- **get_nonterminal(name)** - gets the non-terminal by the given name or `None`
  if not found;

- **get_symbol(name)** - gets either a terminal or non-terminal by the given
  name or `None` if not found.


## GrammarSymbol

This is a base class for `Terminal` and `NonTerminal`.

### Attributes

- **name** - the name of the grammar symbol,

- **action_name** - the action name assigned for the symbol. This is given in
  the grammar using the `@` syntax.

- **action** - resolved reference to the action given by the user using
  `actions` parameter of the parser. Overrides grammar action if provided. If
  not given will be the same as `grammar_action`.

- **grammar_action** - resolved reference to the action given in the grammar.



## Terminal

## NonTerminal

## Production
