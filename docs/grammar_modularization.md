# Grammar modularization

Grammar can be split across multiple files and imported using the `import`
statement. This statement accepts a path to the target grammar file relative to
the source grammar file.

For example,

    import '../../othergrammar.pg';

Rules from imported grammars share the same name-space as the base file so you
must ensure that no rules with the same name exists across imported grammar
files.

When the grammar file is imported its rules can be directly referenced. For
example if the `othergrammar.pg` from above have `SomeTargetRule` we could write
in the rest of the file:

    SomeRule: INT SomeTargetRule+;

`import` statement supports diamond imports as well as recursive imports.
