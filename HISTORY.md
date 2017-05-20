# History

- Development version

  - Lexical recognizers.

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
  - Debug print/tracing (set `debug=True` and/or `layout_debug=True`to the
    `Parser` instantiation).
  - Tests
  - Few examples (see `examples` folder)
