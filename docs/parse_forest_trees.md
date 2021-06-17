# GLR forest

The GLR parser returns the parse forest (`Forest` object). The forest is created
in an efficient way to store all the possible solutions without exponential
explosion. This structure is called *Shared Packed Parse Forest* (SPPF).

The forest is iterable and indexable structure.

For example:

```python
forest = GLRParser(grammar).parse(some_input)

for tree in forest:
  ... do something
  
tree = forest[3]

# To get the number of trees/solutions
print(len(forest))

# or
print(forest.solutions)

# To get the total number of ambiguities in the forest.
print(forest.ambiguities)

```

Forest trees are lazily constructed during iteration and accessing of tree
nodes.

Both forest and parse trees have `to_str` and `to_dot` methods to render as
string/dot.


!!! tip

    You can use `to_str()` on the forest get the string representation with all
    ambiguities indicated. This can be used to analyze ambiguity. For example:

        parser = GLRParser(g)
        forest = parser.parse_file('some_file')
        with open('forest.txt', 'w') as f:
          f.write(forest.to_str())

    This can also be done with `pglr parse` command.

    Another option is to use `to_str()` on individual trees and then use diffing
    tool to compare.
    
    For example:
    
        parser = GLRParser(g)
        forest = parser.parse_file('some_file')
        for idx, tree in enumerate(forest):
            with open(f'tree_{idx:03d}.txt', 'w') as f:
                f.write(tree.to_str())
    
    Now you can run any diff tool on the produced outputs to see where are the ambiguities:
    
        $ meld tree_000.txt tree_001.txt
        
    For smaller inputs you can also use `to_dot` to display a forest/tree as a graph.


# Parse trees

Parse trees are produced by GLR parse forest.

Parse trees are also returned by the LR parser if `build_tree` parser
constructor parameter is set to `True`.

The nodes of parse trees are instances of either `NodeTerm` for terminal nodes
(leafs of the tree) or `NodeNonTerm` for non-terminal nodes (intermediate
nodes).


Each node of the tree has following attributes:

- `start_position/end_position` - the start and end position in the input stream
  where the node starts/ends. It is given in absolute 0-based offset. To convert
  to line/column format for textual inputs you can use
  `parglare.pos_to_line_col(input_str, position)` function which returns tuple
  `(line, column)`. Of course, this call doesn't make any sense if you are
  parsing a non-textual content.

- `layout_content` - the
  [layout](./grammar_language.md#handling-whitespaces-and-comments-in-your-language)
  that preceeds the given tree node. The layout consists of
  whitespaces/comments.

- `symbol` (property) - a grammar symbol this node is created for.


Additionally, each `NodeTerm` has:

- `value` - the value (a part of input_str) which this terminal represents. It
  is equivalent to `input_str[start_position:end_position]`.

- `additional_data` - a list of additional information returned by a custom
  recognizer. This gets passed to terminal nodes actions if `call_actions` is
  called for the parse tree.

Additionally, each `NodeNonTerm` has:

- `children` - sub-nodes which are also of `NodeNonTerm`/`NodeTerm` type.
  `NodeNonTerm` is iterable. Iterating over it will iterate over its children.

- `production` - a grammar production whose reduction created this node.

Each node has a `to_str()` method which will return a string representation of
the sub-tree starting from the given node. If called on a root node it will
return the string representation of the whole tree.

For example, parsing the input `1 + 2 * 3 - 1` with the expression grammar from
the quick start will look like this if printed
with `to_str()`:

    E[0]
    E[0]
      E[0]
        number[0, 1]
      +[2, +]
      E[4]
        E[4]
          number[4, 2]
        *[6, *]
        E[8]
          number[8, 3]
    -[10, -]
    E[11]
      number[11, 1]


# Visitor

A `visitor` function is provided for depth-first processing of a tree-like
structures (actually can be applied to graphs also).

The signature of `visitor` is:

```python
def visitor(root, iterator, visit, memoize=True, check_cycle=False):

```
Where:

- `root` is the root element of the structure to process
- `iterator` iterator is a callable that should return an iterator for the given
  element yielding the next elements to process. E.g. for a tree node iterator
  callable should return an iterator yielding children nodes.
- `visit` is a function called when the node is visited. It results will be
  passed into visitors higher in the hierarchy (thus enabling bottom-up
  processing). `visit` function should accept a node and sub-results from
  lower-level visitors.
- `memoize` - Should results be cached. Handy for direct acyclic graphs if we
  want to prevent multiple calculation of the same sub-graph.
- `check_cycle` - If set to `True` will prevent traversing of cyclic structure
  by keeping cache of already visited nodes and throwing `LoopError` if cycle is
  detected.
  
`visitor` is used internally by parglare so the best place to see how it is used
is the parglare code itself.
