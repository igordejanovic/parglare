# Grammar modularization

Grammar can be split across multiple files and imported using the `import`
statement. This statement accepts a path to the target grammar file relative to
the source grammar file and optional name of the target grammar after the `as`
keyword.

For example,

    import '../../othergrammar.pg';

or

    import '../../othergrammar.pg' as og;


Rules from imported grammar can be referenced by fully qualified name consisting
of dot-separated target grammar name and the rule name. By default the name of
the target grammar is the base name of the grammar file. In the first example we
can reference rules by using `othergrammar.` prefix as for example:

    SomeRule: INT othergrammar.SomeTargetRule+;

Or in the second example we are using name `og` as the target grammar name so
the previous example will be written as:

    SomeRule: INT og.SomeTargetRule+;


`import` statement supports diamond imports as well as recursive imports.

Each rule in the overall grammar has a fully qualified name (FQN). This name is
constructed by the dot-separated chain of target grammar names ending with the
rule name, using the first chain of imports that lead to the rule.
This naming scheme enables the import of grammar files from arbitrary locations
while still preserving a deterministic FQN for each rule of the grammar.

For example, if there is a grammar file `A.pg` importing `B.pg` and `C.pg`,
where `B.pg` also imports `C.pg` than, if the `A.pg` is the root of the grammar,
all the rules in `C.pg` have FQN in the form of `B.C.some_rule`. Notice that the
first path to `C.pg` was from `B.pg` as the `B.pg` grammar is imported first in
`A.pg.`. See [fqn
tests](https://github.com/igordejanovic/parglare/blob/master/tests/func/import/fqn/test_fqn.py)
for an example.



## Grammar file recognizers

Grammar file can optionally provide its [recognizers](./recognizers.md). These
should be given in a Python file named `<base grammar name>_recognizers.py` and
should be found in the same folder where the grammar file is found.

For example, if grammar file is named `mygrammar.pg` than recognizers module
should be named `mygrammar_recognizers.py`.

For a parglare to be able to collect all recognizers defined in a module a
`collector` is used. It is a decorator constructed in the Python recognizer
module and used to decorate each recognizer function.

For example, `mygrammar_recognizers.py` might be given as:

```python
from parglare import get_collector

recognizer = get_collector()

@recognizer
def term_a(input, position):
  ... some recognition

@recognizer
def term_b(input, position):
  ...
```

`recognizer` object is `collector` in this case. It will construct a dictionary
of all recognizers decorated by it and that dictionary will be provided as
`recognizer.all`. parglare recognizer loader will implicitly search for
`recognizer.all`.

By default, a name of a decorated function will serve as a terminal name this
recognizer is defined for. But, you can provide different name using a string
parameter to `recognizer` decorator, like:

```python
@recognizer('NUMERIC_ID')
def number(input, pos):
    ...
```

In this case grammar terminal is named `NUMERIC_ID` while the recognition
function is named `number`. This can be used, for example, to create a library
of common recognizer function and use them in grammar for terminals with
different names, like:

```python
from somemodule import myrecognizer
from parglare import get_collector

recognizer = get_collector()

recognizer('NUMERIC_ID')(myrecognizer)
```

You can use a fully qualified terminal name to override recognizer for imported
terminal:

```python
@recognizer('base.COMMA')
def comma_recognizer(input, pos):
    if input[pos] == ',':
        return input[pos:pos + 1]
```

In this case there is an imported grammar `base` whose terminal `COMMA`
recognizer has been overriden by `comma_recognizer` recognizer function.

!!! warning

    Since the way a recognizer module is imported in Python you **must** use
    only Python absolute module imports inside the recognizer module.


### Recognizer search order

Recognizers are loaded from a grammar module but can be overriden from importing
grammars, using FQN of the terminal, or by using `recognizers` parameter of the
grammar.


## Grammar file actions

Similarly to recognizers, actions can be provided in a Python file named `<base
grammar name>_actions.py` that should be found in the same folder where the
grammar file is found.

For example, if grammar file is named `mygrammar.pg` than actions module should
be named `mygrammar_actions.py`.

For a parglare to be able to collect all actions defined in a module a
`collector` is used in very much the same way as it is used for recognizers. It
is a decorator constructed in the Python actions module and used to decorate
each action function.

For example, `mygrammar_actions.py` might be given as:

```python
from parglare import get_collector

action = get_collector()

@action
def first_rule(context, nodes):
  ...

@action
def second_rule(context, nodes):
  ...
```

`action` object is `collector` in this case. It will construct a dictionary of
all actions decorated by it and that dictionary will be provided as
`action.all`. parglare action loader will implicitly search for `action.all`.

By default, a name of a decorated function will serve as a grammar symbol name
or in-grammar defined action name (using `@`, see [syntax for action
specification](./grammar_language.md#referencing-semantic-actions-from-a-grammar))
this action is defined for. But, you can provide different name using a string
parameter to `action` decorator:


!!! warning

    Since the way an action module is imported in Python you **must** use
    only Python absolute module imports inside of it.


### Action search order

Actions are searched in the order of specificity by searching the following (in
the given order):

1. Actions given using `actions` parameter by FQN of the symbol,
2. Actions loaded from actions module using FQN of the symbol,
3. Actions given using `actions` parameter by FQN of the action,
4. Actions loaded from actions module using FQN of the action,
5. Actions given using `actions` parameter by symbol name,
6. Actions loaded from actions module using symbol name,
7. Actions given using `actions` parameter by action name,
8. Actions loaded from actions module using action name,
9. [parglare built-in actions](./actions.md#built-in-actions) using action name.
