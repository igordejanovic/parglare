# parglare grammar language

parglare grammar specification language is based on [BNF](). parglare is based
on Context-Free Grammars (CFGs) and grammar is given declaratively. You don't
have to think about the parsing process like in e.g. [PEGs](). Ambiguities are
dealt with explicitely (see section on conflicts...).

Grammar consists of a set of rules where each rule is of the form:

```
<rule_name> = <rule_pattern1> | <rule_pattern2> | ... ;
```

If you got use to various BNF extensions
(like [Kleene star]()https://en.wikipedia.org/wiki/Kleene_star) you might find
this awkward. The grammars are indeed more verbose but, on the other hand,
actions are much easier to write and you have full control over tree
construction process.

Rule name format


pattern

Alternative patterns

Recursion
