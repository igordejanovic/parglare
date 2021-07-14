# Release notes for 0.15

This release should be fully backward compatible so the upgrade should require
no changes.

## Greedy repetitions

The most important new feature in this release is a support for greedy
repetition. Read more in [the docs](../../grammar_language/#greedy-repetitions).

## New way to disambiguate the GLR forest

A new and recommended way for dynamic disambiguation is by using
`forest.disambiguate`. Read more in [the docs](../../disambiguation/#disambiguation-of-a-glr-forest).

## Optimized getting of the first tree from the GLR forest

If you are not interested into analyzing the forest and comparing trees but just
want to get any valid tree you can use `forest.get_first_tree()` which is
optimized to avoid tree enumeration that might be costly. The returned tree is
fully unpacked and doesn't use proxies, i.e. it contains only `NodeTerm` and
`NodeNonTerm` instances.
