# History

- 2018-05-22 Version 0.6.0
  - New feature: grammar modularization - see the docs:
    http://www.igordejanovic.net/parglare/grammar_modularization/
  - Backward incopatibile change: terminals are now specified in a separate
    section which starts with keyword `terminals`. This section should be
    defined after production rules. You can still use inline terminals for
    string matches but not for regex matchers. This change will prevent problems
    reported on issue #27. See the changes in the docs.
  - Fixed issue #32 - Conflict between string match and rule with the same name
  - Various improvements in error reporting, docs and tests.
  - Support for Python 3.3 dropped.

- 2018-03-25 Version 0.5
  - Added file_name to the parse context.
  - Added `re_flags` param to the `Grammar` class factory methods.
  - Added `_pg_start_position/_pg_end_position` attributes to auto-created
    objects.
  - Improved reporting of regex compile errors. Thanks Albert Hofkamp
    (alberth@GitHub)!
  - Keyword-like string recognizers (matched on word boundaries).
    Issue: https://github.com/igordejanovic/parglare/issues/12
  - Support for case-insensitive parsing. `ignore_case` param to the `Grammar`
    factory methods.
  - Added `prefer_shifts` and `prefer_shifts_over_empty` disambiguation
    strategies.
  - Introduced disambiguation keywords `shift` and `reduce` as synonyms for
    `right` and `left`.
  - Introduced per-production `nops` (no prefer shift) and `nopse` (no prefer
    shift over empty) for per-production control of disambiguation strategy.
  - Introduced `nofinish` for terminals to disable `finish` optimization
    strategy.
  - Introduced `action` Python decorator for action definition/collection.
  - Better visuals for killed heads in GLR dot trace.
  - Fixed multiple rules with assignment bug:
    Issue: https://github.com/igordejanovic/parglare/issues/23
  - Report error on multiple number of actions for rule with multiple
    productions.
  - Improved debug/trace output.
  - Improved parse tree str output.
  - More tests.
  - More docs.
  - Code cleanup and refactorings.

- 2017-10-18 Version 0.4.1
  - Fix in GLR parser. Parser reference not set on the parser context.

- 2017-10-18 Version 0.4
  - Added regex-like syntax extension for grammar language (`?`, `*`, `+`).
    Issue: https://github.com/igordejanovic/parglare/issues/3
  - Rule actions can be defined in grammar using `@` syntax for both built-in
    actions and user supplied ones.
    Issues: https://github.com/igordejanovic/parglare/issues/1
            https://github.com/igordejanovic/parglare/issues/6
  - Introduced named matches (a.k.a. assignments). Python classes created for
    each rule using named matches.
    Issue: https://github.com/igordejanovic/parglare/issues/2
  - Introduced built-in action for creating Python object for rules using
    named matches.
  - Colorized and nicely formatted debug/trace output based on `click` package.
    Issue: https://github.com/igordejanovic/parglare/issues/8
  - Introduced `build_tree` parameter for explicitly configuring parser for
    building a parse tree.
  - Introducing default actions that build nested lists. Simplifying actions
    writing.
  - Added input_str to parser context.
  - Added `click` dependency.
  - Reworked `pglr` CLI to use `click`.
  - Docs reworkings/updates.
  - Various bugfixes + tests.

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
