# The grammar class and related APIs

After you write your grammar either as a Python string or as a separate file the
next step is to instantiate the grammar object that will be used to create the
parser.

There are two factory methods defined on the `Grammar` class for creating the
`Grammar` instance:

- `Grammar.from_string(grammar_string)` - if your grammar is given as a Python
  string,
- `Grammar.from_file(file_path)` - if the grammar is given as a separate file.

Both methods return initialized `Grammar` object that is passed as the first and
the only mandatory parameter for the `Parser/GLRParser` constructor.


## Grammar factory methods additional parameters

Both methods `from_string` and `from_file` accept additional optional
parameters:

- **recognizers** - a dict of custom recognizers. These recognizers are mandatory
  if a non-textual content is being parsed and the grammar terminals don't
  provide recognizers. See [recognizers section](./recognizers.md) for more
  information.

- **debug** - set to `True` to put the grammar in debug/trace mode. `False` by
  default. See [debugging section](./debugging.md) for more information.

- **debug_parse** - set to `True` to debug/trace grammar file/string parsing.
  `False` by default.

- **debug_colors** - set to `True` to enable terminal colors in debug/trace
  output. `False` by default.

- **re_flags** - regex flags used for regex recognizers. See Python `re` module.
  By default flags is set to `re.MULTILINE`.

- **ignore_case** - By default parsing is case sensitive. Set this param to
  `True` for case-insensitive parsing.


## Grammar class

### Attributes

- **terminals** - a dict of terminals (instances of [`Terminal`](#terminal))
  keyed by fully qualified name;

- **nonterminals** - a dict of non-terminal (instances
  of [`NonTerminal`](#nonterminal)) keyed by fully qualified name;

- **start_symbol** - a grammar symbol of the start/root rule. By default this is
  the first rule in the grammar;

- **productions** - a list of productions ([`Production`](#production)
  instances);

- **recognizers** - a dict of [user supplied recognizers](./recognizers.md)
  keyed by the terminal rule name;

- **classes** - a dict of Python classes dynamically created for rules
  using [named matches](./grammar_language.md#named-matches-assignments) keyed
  by the rule name.

### Methods

- **print_debug()** - prints detailed debug/trace info;

- **get_terminal(name)** - gets the terminal by the given fully qualified name
  or `None` if not found;

- **get_nonterminal(name)** - gets the non-terminal by the given fully qualified
  name or `None` if not found;

- **get_symbol(name)** - gets either a terminal or non-terminal by the given
  fully qualified name or `None` if not found.


## GrammarSymbol class

This is a base class for `Terminal` and `NonTerminal`.

### Attributes

- **name** - the name of the grammar symbol,

- **fqn** (property) - fully qualified name of the symbol. Qualified by import
  module names.

- **location** - an instance of `parglare.common.Location`. Gives information
  about location in the file (position and span).

- **action_name** - the action name assigned for the symbol. This is given in
  the grammar using the [`@` syntax](./grammar_language.md/#referencing-semantic-actions-from-a-grammar). If action name is
  not provided in the grammar symbol name is used.

- **action_fqn** (property) - the fully qualiifed action name for the symbol.
  Qualified by the names of import modules.

- **action** - resolved reference to the action function given by the user using
  `actions` parameter of the parser. Overrides grammar action if provided. If
  not given will be the same as `grammar_action`.

- **grammar_action** - resolved reference to the action function specified in
  the grammar. Not used if `action` attribute is defined, i.e. `action`
  overrides `grammar_action`.



## Terminal class

### Attributes

- **prior (int)** - a priority used in disambiguation,

- **recognizer (callable)** - a callable in charge of recognition of this terminal
  in the input stream,

- **prefer (bool)** - If `True` this recognizer/terminal is preferred in case of
  conflict where multiple recognizer match at the same place and implicit
  disambiguation doesn't resolve the conflict.

- **dynamic (bool)** - `True` if disambiguation should
  be [resolved dynamically](./disambiguation.md#dynamic-disambiguation-filter).


## NonTerminal class

### Attributes

- **productions (list)** - A list of alternative productions for this
  non-terminal symbol.


## Production class

### Attributes

- **symbol (GrammarSymbol)** - LHS of the production,

- **rhs (ProductionRHS)** - RHS of this production,

- **assignments (dict)** - `Assignment` instances keyed by match name. Created
  by [named matches](./grammar_language.md#named-matches-assignments),

- **assoc (int)** - associativity of the production. See
  `parglare.grammar.ASSOC_{NONE|LEFT|RIGHT}`

- **prior (int)** - integer defining priority of this production. Default
  priority is 10.

- **dynamic (bool)** - `True` if this production disambiguation should
  be [resolved dynamically](./disambiguation.md#dynamic-disambiguation-filter).

- **prod_id (int)** - ordinal number of the production in the grammar,

- **prod_symbol_id** - zero-based ordinal of the production for the `symbol`
  grammar symbol, i.e. the ordinal for the alternative choice for this symbol.


## ProductionRHS class

Represents right hand side of the production. Inherits list and keeps symbols
from the production but doesn't count nor returns by index EMPTY symbols in the
production.
