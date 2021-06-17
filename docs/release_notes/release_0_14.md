# Release notes for 0.14

## Parenthesed groups

RHS in grammar rules now can used parentheses to group element. These groups
behave similar to any other rule reference. E.g. repetitions and assignments can
be applied.

Previously:

```nohiglight
S: a_then_b*[comma] c;
a_then_b: a b;
...

```

Now you can write:

```nohiglight
S: (a b)*[comma] c;
...

```

You can nest groups, combine with choice operator etc.

```nohiglight
S: ( (a c)+ | b)*[comma] c;

```
For more info see a [new section in the docs](../grammar_language.md#parenthesized-groups).


## GLR forest

GLR now returns `Forest` object. This object represents all the possible solutions.
Forest can be iterated, indexed, yielding lazy parse trees.

See [more info in the docs](../parse_forest_trees.md).


## Extensions to `pglr` command

`pglr trace` now provides `--frontier` flag to organize GSS nodes into
frontiers. See [the docs](../pglr.md#tracing-glr-parsing).

`pglr parse` is added for parsing input strings and files and producing forests
and trees as either string or graphical dot representation. See [the
docs](../pglr.md#parsing-inputs).


## Support for visitor

*Visitor pattern* is supported as a `visitor` function enabling depth-first
processing of tree-like structures. See [the
docs](../parse_forest_trees.md#visitor).


## New examples

Several new examples are added:

- [JSON](https://github.com/igordejanovic/parglare/tree/master/examples/json)
- [BibTeX](https://github.com/igordejanovic/parglare/tree/master/examples/bibtex)
- [Java](https://github.com/igordejanovic/parglare/tree/master/examples/java) (based on Java SE 16 version)


## Performance tests

New performance tests based on new example grammars are provided in
[tests/perf](https://github.com/igordejanovic/parglare/tree/master/tests/perf).
Run `runall.sh` and read the reports in
[tests/perf/reports](https://github.com/igordejanovic/parglare/tree/master/tests/perf/reports).
