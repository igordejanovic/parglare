# parglare changelog

All _notable_ changes to this project will be documented in this file.

The format is based on _[Keep a Changelog][keepachangelog]_, and this project
adheres to _[Semantic Versioning][semver]_.

Everything that is documented in the [official docs][parglareDocs] is considered
the part of the public API.

Backward incompatible changes are marked with **(BIC)**. These changes are the
reason for the major version increase so when upgrading between major versions
please take a look at related PRs and issues and see if the change affects you.

Note: Since parglare is still in pre-1.x version major version increase on
backward incompatible changes will start to apply when the projects goes 1.0
(i.e. is considered production/stable).


## [Unreleased]


### Added

  - Support for manual table loading from different sources. Thanks
    SupraSummus@GitHub. ([#81])

### Changed

  - Using plain dicts instead of OrderedDicts in table serialization. Thanks
    SupraSummus@GitHub. ([#85])
  - Making implicit lexical disambiguation optional + fixing/simplification of
    GLR error recovery and lexical disambiguation. Thanks SupraSummus@GitHub
    ([#86])
    - **(BIC)**: GLR is not using implicit lexical disambiguation now by
      default. To recover previous behaviour pass `lexical_disambiguation=True`
      to `GLRParser`.
  - Dropping support for `start_production` Parser param. Thanks
    SupraSummus@GitHub. ([#80], [#91])

### Fixed

  - Fixing regexp with backslashes. Thanks SupraSummus@GitHub. ([#75], [#74])
  - Fixing recognizer calling to prohibit empty matches. Thanks
    SupraSummus@GitHub for the tests ([#89], [#90])
  - Various typo/phrasing fixes in the docs and docstrings. Thanks
    chenl@GitHub.


## [0.8.0] (released: 2018-09-25)

### Added
  - Table caching. ([#36], [#52], [#20])
    parglare will store calculated LR table in `<grammar_file_name>.pgt` file.
    If the file exists and is newer than all of imported grammar files it will
    load table from the cached table file. Use `pglr compile` command to produce
    `.pgt` file in advance. See the docs on `pglr compile` command.
  - `force_load_table` parser param added that will load parser table if exists
    without checking modification time.
    
### Changed
  - `pglr check` command changed to `pglr compile` which checks the grammar and
    produces table file `<grammar_file_name>.pgt`.
    
### Fixed
    - Recognizer context passing made more robust.
    - Fixing location message bug in `GrammarError`


## [0.7.0] (released: 2018-09-13)

  - Rework/cleanup of both LR and GLR parsers. Backward incompatible changes
    (see below).
  - Added optional first param to recognizers passing in Context object.
    See https://github.com/igordejanovic/parglare/pull/55
    Thanks jwcraftsman@GitHub
  - `Context` object now uses `__slots__` and has `extra` attribute for user
    usage. By default `extra` is initialized to an empty dict if context object
    is not created by the user.
  - `dynamic_filter` callback params changed from `action, token, production,
    subresults, state, context` to `context, action, subresults`. To access
    previous param values use `context.tokens_ahead` for `token`,
    `context.production` for `production` and `context.state` for `state`.
  - `error_recovery` callback params changed from `(parser, input, position,
    expected_symbols)` to `(context, error)`. To access previous param values
    use `context.parser`, `context.input_str`, `context.position`,
    `error.symbols_expected`. The other way to access expected symbols is
    `context.state.actions.keys()` but in the context of GLR
    `error.symbols_expected` will give a subset of all possible symbols in the
    given state for which parser is guaranteed to continue (e.g. to execute
    SHIFT).
  - Error recovery function now returns token and position. The error is
    automatically registered and returned with parsing results.
  - `custom_lexical_disambiguation` parser param/callback changed to
    `custom_token_recognition`.
  - `custom_token_recognition` callback params changed from `symbols, input_str,
    position, get_tokens` to `context, get_tokens`. To access previous param
    values use `context.state.actions.keys()` for `symbols`, `context.input_str`
    and `context.position` for `input_str` and `position`.
  - Lexical ambiguity results in `DisambiguationError` now instead of
    `ParseError`for LR parser.
  - `start_production` parser param now accepts a fully qualified rule name
    instead of id. First production id for the given rule is used.
  - `NodeTerm` keeps a reference to the token. `value` is now a read-only
    property that proxies `token.value`.
  - Support for arbitrary user meta-data.
    See issue: https://github.com/igordejanovic/parglare/issues/57
  - `ParseError` now has `symbols_expected`, `tokens_ahead` and
    `symbols_before` attributes. See [Handling errors
    section](http://www.igordejanovic.net/parglare/0.7/handling_errors/).


## [0.6.1] (released: 2018-05-24)

  - Fixed issue with actions resolving search order.
  - Fixed #31 GLR drops valid parses on lexical ambiguity.
  - Fix in GLR graphical debug trace.


## [0.6.0] (released: 2018-05-22)

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


## [0.5] (released: 2018-03-25)

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


## [0.4.1] (released: 2017-10-18)

  - Fix in GLR parser. Parser reference not set on the parser context.


## [0.4] (released: 2017-10-18)

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


## [0.3] (released: 2017-08-24)

  - Dynamic disambiguation filters. Introducing `dynamic` disambiguation rule in
    the grammar.
  - Terminal definitions with empty bodies.
  - Improved error reporting in recovery.
  - Report LR state symbol in conflict debug output.
  - Report killing head on unsuccessful recovery.
  - Parameter rename layout_debug -> debug_layout
  - GLR visual tracing parameter is separated from debug.
  - Fixing GLR trace visualization.


## [0.2] (released: 2017-08-09)

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


## [0.1] (released: 2017-02-02)

  - Textual syntax for grammar specification. Parsed with parglare.
  - SLR and LALR tables calculation (LALR is the default)
  - Scannerless LR(1) parsing
    - Scanner is integrated into parsing. This give more power as the token
      recognition is postponed and done in the parsing context at the current
      parsing location.
  - Declarative associativity and priority based conflict resolution for
    productions
    - See the `calc` example, or the quick intro below.
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



[#91]: https://github.com/igordejanovic/parglare/pull/91
[#90]: https://github.com/igordejanovic/parglare/pull/90
[#89]: https://github.com/igordejanovic/parglare/pull/89
[#86]: https://github.com/igordejanovic/parglare/pull/86
[#85]: https://github.com/igordejanovic/parglare/pull/85
[#81]: https://github.com/igordejanovic/parglare/pull/81
[#80]: https://github.com/igordejanovic/parglare/issue/80
[#75]: https://github.com/igordejanovic/parglare/pull/75
[#74]: https://github.com/igordejanovic/parglare/issue/74
[#81]: https://github.com/igordejanovic/parglare/pull/81
[#52]: https://github.com/igordejanovic/parglare/issues/52
[#36]: https://github.com/igordejanovic/parglare/issues/36
[#20]: https://github.com/igordejanovic/parglare/issues/20


[Unreleased]: https://github.com/igordejanovic/parglare/compare/0.8.0...HEAD
[0.8.0]: https://github.com/igordejanovic/parglare/compare/0.7.0...0.8.0
[0.7.0]: https://github.com/igordejanovic/parglare/compare/0.6.1...0.7.0
[0.6.1]: https://github.com/igordejanovic/parglare/compare/0.6.0...0.6.1
[0.6.0]: https://github.com/igordejanovic/parglare/compare/0.5...0.6.0
[0.5]: https://github.com/igordejanovic/parglare/compare/0.4.1...0.5
[0.4.1]: https://github.com/igordejanovic/parglare/compare/0.4...0.4.1
[0.4]: https://github.com/igordejanovic/parglare/compare/0.3...0.4
[0.3]: https://github.com/igordejanovic/parglare/compare/0.2...0.3
[0.2]: https://github.com/igordejanovic/parglare/compare/0.1...0.2
[0.1]: https://github.com/igordejanovic/parglare/compare/47d41aa...0.1


[parglareDocs]: http://www.igordejanovic.net/parglare/
[keepachangelog]: https://keepachangelog.com/
[semver]: https://semver.org/spec/v2.0.0.html
