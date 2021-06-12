# -*- coding: utf-8 -*-
from functools import reduce
from parglare.common import dot_escape
from parglare.exceptions import LoopError


DOT_HEADER = '''
    digraph grammar {
    rankdir=TD
    fontname = "Bitstream Vera Sans"
    fontsize = 8
    node[
        style=filled,
        fillcolor=aliceblue
    ]
    nodesep = 0.3
    edge[dir=black,arrowtail=empty]


'''


def node_iterator(n):
    if isinstance(n, NodeNonTerm):
        return iter(n.children)
    else:
        return iter([])


class Node(object):
    """A node of the parse tree."""

    __slots__ = ['context']

    def __init__(self, context):
        self.context = context

    def __repr__(self):
        return str(self)

    def __iter__(self):
        return iter([])

    def __reversed__(self):
        return iter([])

    def __getattr__(self, name):
        return getattr(self.context, name)

    def is_nonterm(self):
        return False

    def is_term(self):
        return False

    def to_str(self):
        def calculate(n, subresults):
            if isinstance(n, NodeNonTerm):
                s = '{}[{}->{}]'.format(self.production.symbol,
                                        self.start_position,
                                        self.end_position)
                s += '\n\t'.join(subresults)
            else:
                s = '{}[{}->{}, "{}"]'.format(self.symbol,
                                              self.start_position,
                                              self.end_position,
                                              self.value)
            return s
        return visitor(self, node_iterator, calculate)

    def to_dot(self):
        def calculate(n, subresults):
            if isinstance(n, NodeNonTerm):
                s = '{}[label="{}"];\n'.format(
                    id(n),
                    dot_escape(f'{n.symbol}[{n.start_position}-{n.end_position}]'))
                s += ''.join(s[1] for s in subresults)
                s += ''.join(('{}->{};\n'.format(id(n), id(s[0])) for s in subresults))
            else:
                s = '{} [label="{}"];\n'\
                    .format(id(n), dot_escape(f'{n.symbol}({n.value[:10]})'
                                              f'[{n.start_position}-{n.end_position}]'))
            return (n, s)
        return DOT_HEADER + visitor(self, node_iterator, calculate)[1] + '\n}'


class NodeNonTerm(Node):
    __slots__ = ['production', 'children']

    def __init__(self, context, children, production=None):
        super(NodeNonTerm, self).__init__(context)
        self.children = children
        self.production = production

    def to_str(self, depth=0, children=None):
        indent = '  ' * depth
        s = '{}[{}->{}]'.format(self.production.symbol,
                                self.start_position,
                                self.end_position)
        children = children or self.children
        if children:
            for n in children:
                if hasattr(n, 'to_str'):
                    s += '\n' + indent + n.to_str(depth+1)
                else:
                    s += '\n' + indent + n.__class__.__name__ \
                         + '(' + str(n) + ')'
        return s

    @property
    def solutions(self):
        "For SPPF trees"
        return reduce(lambda x, y: x*y, (c.solutions for c in self.children))

    @property
    def symbol(self):
        return self.production.symbol

    def is_nonterm(self):
        return True

    def __str__(self):
        return 'NonTerm({}, {}-{})'\
            .format(self.production.symbol,
                    self.start_position, self.end_position)

    def __iter__(self):
        return iter(self.children)

    def __reversed__(self):
        return reversed(self.children)


class NodeTerm(Node):
    def __init__(self, context, token=None):
        super(NodeTerm, self).__init__(context)
        self.token = token

    @property
    def symbol(self):
        return self.token.symbol

    @property
    def value(self):
        return self.token.value

    @property
    def additional_data(self):
        return self.token.additional_data

    @property
    def solutions(self):
        "For SPPF trees"
        return 1

    def to_str(self, depth=0):
        return '{}[{}->{}, "{}"]'.format(self.symbol,
                                         self.start_position,
                                         self.end_position,
                                         self.value)

    def is_term(self):
        return True

    def __str__(self):
        return 'Term({} "{}", {}-{})'\
            .format(self.symbol, self.value[:20],
                    self.start_position, self.end_position)

    def __iter__(self):
        return iter([])

    def __reversed__(self):
        return iter([])


class Tree:
    """
    Represents a tree from the parse forest.
    """
    __slots__ = ['root', 'children']

    def __init__(self, root, counter):
        possibility = 0
        if counter > 0 and len(root.possibilities) > 1:
            # Find the right possibility bucket
            solutions = root.possibilities[possibility].solutions
            while solutions <= counter:
                counter -= solutions
                possibility += 1
                solutions = root.possibilities[possibility].solutions

        self.root = root.possibilities[possibility]
        self._init_children(counter)

    def _init_children(self, counter):
        if self.root.is_nonterm():
            self.children = self._enumerate_children(counter)

    def _enumerate_children(self, counter):
        children = []
        # Calculate counter division based on weighted numbering system.
        # Basically, enumerating variations of children solutions.
        weights = [c.solutions for c in self.root.children]
        for idx, c in enumerate(self.root.children):
            factor = reduce(lambda x, y: x*y, weights[idx+1:], 1)
            new_counter = counter // factor
            counter %= factor
            children.append(self.__class__(c, new_counter))
        return children

    def to_str(self, depth=0):
        if self.root.is_nonterm():
            return self.root.to_str(depth, self.children)
        else:
            return self.root.to_str(depth)

    def __iter__(self):
        return iter(self.children or [])

    def __reversed__(self):
        return reversed(self.children)

    def __getattr__(self, attr):
        # Proxy to tree node
        return getattr(self.root, attr)


class LazyTree(Tree):
    """
    Represents a lazy tree from the parse forest.

    Attributes:
    root(Parent):
    counter(int):
    """
    __slots__ = ['root', 'counter', '_children']

    def __init__(self, root, counter):
        self._children = None
        super().__init__(root, counter)

    def _init_children(self, counter):
        self.counter = counter

    def __getattr__(self, attr):
        if 'children' == attr:
            if self._children is None:
                if self.root.is_nonterm():
                    self._children = self._enumerate_children(self.counter)
            return self._children
        # Proxy to tree node
        return getattr(self.root, attr)


class Forest:
    """
    Shared packed forest returned by the GLR parser.
    Creates lazy tree enumerators and enables iteration over trees.
    """
    def __init__(self, parser):
        self.parser = parser
        results = [p for r in parser._accepted_heads for p in r.parents.values()]
        self.result = results.pop()
        while results:
            result = results.pop()
            self.result.merge(result)

    def get_tree(self, idx=0):
        return LazyTree(self.result, idx)

    def get_nonlazy_tree(self, idx=0):
        return Tree(self.result, idx)

    @property
    def solutions(self):
        return self.result.solutions

    @property
    def ambiguities(self):
        "Number of ambiguous nodes in this forest."
        return self.result.ambiguities

    def __str__(self):
        return f'Forest({self.solutions})'

    def to_str(self):
        return self.result.to_str()

    def to_dot(self):
        return self.result.to_dot()

    def __len__(self):
        return self.solutions

    def __iter__(self):
        for i in range(self.solutions):
            yield self.get_tree(i)

    def __getitem__(self, idx):
        return self.get_tree(idx)

    def nonlazy_iter(self):
        for i in range(self.solutions):
            yield self.get_nonlazy_tree(i)


def visitor(root, iterator, visit, memoize=True, check_cycle=False):
    """Generic iterative depth-first visitor with memoization.

    Accepts the start of the structure to visit (root), iterator callable which
    gets called to get the next elements to visit and `visit` function which
    is called with the element and sub-results of the iterated child elements.
    Should return the result for the given node.

    Memoize parameter uses cache to store the results of already visited elements.

    """
    if memoize:
        cache = {}
    stack = [(root, iterator(root), [])]
    if check_cycle:
        visiting = set([id(root)])
    while stack:
        node, it, results = stack[-1]
        try:
            next_elem = next(it)
        except StopIteration:
            # No more sub-elements for this node
            stack.pop()
            if check_cycle:
                visiting.remove(id(node))
            result = visit(node, results)
            if memoize:
                cache[id(node)] = result
            if stack:
                stack[-1][-1].append(result)
            continue
        if check_cycle and id(next_elem) in visiting:
            raise LoopError('Looping during traversal on "{}". '
                            'Last elements: {}'.format(next_elem,
                                                       [r[0] for r in stack[-10:]]))
        if memoize and id(next_elem) in cache:
            results.append(cache[id(next_elem)])
        else:
            stack.append((next_elem, iterator(next_elem), []))
            if check_cycle:
                visiting.add(id(next_elem))

    return result
