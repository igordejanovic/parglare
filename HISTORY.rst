History
-------

- 2017-08-24 Version 0.3

  - Dynamic disambiguation filters. Introducing `dynamic` disambiguation rule in
    the grammar.
  - Terminal definitions with empty bodies.
  - Improved error reporting in recovery.
  - Report LR state symbol in conflict debug output.
  - Report killing head on unsuccessful recovery.
  - Parameter rename layout_debug -> debug_layout
  - GLR visual tracing parameter is separated from debug.
  - Fixing GLR trace visualization.

- 2017-08-09 Version 0.2

  - GLR parsing. Support for epsilon grammars, cyclic grammars and grammars with
    infinite ambiguity.
  - Lexical recognizers. Parsing the stream of arbitrary objects.
  - Error recovery. Builtin default recovery, custom user defined.
  - Common semantic actions.
  - Documentation.
  - pglr CLI command.
  - Automata visualization, GLR visual tracing.
  - Lexical disambiguation improvements.
  - Support for epsilon grammar (empty productions).
  - Support for comments in grammars.
  - `finish` and `prefer` terminal rules.
  - Change in the grammar language `=` - > `:`
  - Additions to examples and tests.
  - Various optimizations and bug fixes.

- 2017-02-02 - Version 0.1

  - Textual syntax for grammar specification. Parsed with parglare.
  - SLR and LALR tables calculation (LALR is the default)
  - Scannerless LR(1) parsing
    - Scanner is integrated into parsing. This give more power as the token
      recognition is postponed and done in the parsing context at the current
      parsing location.
  - Declarative associativity and priority based conflict resolution for
    productions
    - See the `calc` example, or the quick intro bellow.
  - Lexical disambiguation strategy.
    - The default strategy is longest-match first and then `str` over `regex`
      match (i.e. the most specific match). Terminal priority can be provided
      for override if necessary.
  - Semantic actions and default actions which builds the parse tree (controlled
    by `actions` and `default_actions` parameters for the `Parser` class).
    - If no actions are provided and the default actions are explicitely
      disabled parser works as a recognizer, i.e. no reduction actions are
      called and the only output of the parser is whether the input was
      recognized or not.
  - Support for language comments/whitespaces using special rule `LAYOUT`.
  - Debug print/tracing (set `debug=True` and/or `debug_layout=True`to the
    `Parser` instantiation).
  - Tests
  - Few examples (see `examples` folder)
