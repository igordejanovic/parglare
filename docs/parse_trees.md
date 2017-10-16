# Parse trees

During shift/reduce operations parser will call [actions](./actions.md). If no
user actions are provided the default actions will be called which will build the
parse tree. In the case of GLR parser multiple trees can be built simultaneously
(the parse forest). If user actions are provided, no tree building takes place
but the user actions decide what to create for each shift/reduction.

The nodes of parse trees are instances of either `NodeTerm` for terminal nodes
(leafs of the tree) or `NodeNonTerm` for non-terminal nodes (intermediate
nodes).


Each node of the tree has following attributes:

- **start_position/end_position** - the start and end position in the input
  stream where the node starts/ends. It is given in absolute 0-based offset. To
  convert to line/column format for textual inputs you can use
  `parglare.pos_to_line_col(input_str, position)` function which returns tuple
  `(line, column)`. Of course, this call doesn't make any sense if you are
  parsing a non-textual content.
- **layout_content** - the layout that preceeds the given tree node. The layout
  consists of whitespaces/comments.
- **symbol** - a grammar symbol this node is created for.


Additionally, each `NodeTerm` has:

- **value** - the value (a part of input_str) which this terminal represents. It
  can be viewed as `input_str[start_position:end_position]`.

Additionally, each `NodeNonTerm` has:

- **children** - subnodes which are also of `NodeNonTerm`/`NodeTerm` type.
  `NodeNonTerm` is iterable. Iterating over it will iterate over its children.
- **production** - a grammar production which reduction created this node.

Each node has a `tree_str()` method which will return a string representation of
the subtree starting from the given node. If called on root node it will return
the string representation of the whole tree.

For example, parsing the input `1 + 2 * 3 -1` using default actions (thus,
producing the parse tree) will look like this if printed with `tree_str()`:

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
