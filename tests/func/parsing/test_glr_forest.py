import pytest  # noqa
from parglare import Grammar, GLRParser


@pytest.fixture
def parser():
    grammar = r"""
    E: E "+" E | E "*" E | "(" E ")" | Number;
    terminals
    Number: /\d+/;
    """
    return GLRParser(Grammar.from_string(grammar))


def test_solutions(parser):
    """
    Test that the number of solution for expression grammar reported by the
    forest is [Catalan number](https://en.wikipedia.org/wiki/Catalan_number).

    """
    forest = parser.parse('2 + 3 * 5')
    assert forest.solutions == 2

    forest = parser.parse('2 + 3 * 5 + 4')
    assert forest.solutions == 5

    forest = parser.parse('2 + 3 * 5 + 4 *1')
    assert forest.solutions == 14

    forest = parser.parse('2 + 3 * 5 + 4 * 1 * 7')
    assert forest.solutions == 42


def test_ambiguities(parser):
    """
    Forest.ambiguities should return the number of ambiguous nodes in SPPF.
    """
    forest = parser.parse('2 + 3 * 5')
    assert forest.ambiguities == 1

    forest = parser.parse('2 + 3 * 5 + 4')
    assert forest.ambiguities == 3

    forest = parser.parse('2 + 3 * 5 + 4 *1')
    assert forest.ambiguities == 6


def test_tree_iteration(parser):
    forest = parser.parse('2 + 3 * 5 + 4 * 1 * 7')

    assert len(forest) == 42

    tree_iterated = 0
    for tree in forest:
        assert tree.is_nonterm()
        assert tree.symbol.name == 'E'
        tree_iterated += 1

    assert tree_iterated == 42
    assert len(list(enumerate(forest))) == 42


def test_forest_index(parser):
    """
    Test that forest enables index access returning lazy tree.
    """
    forest = parser.parse('2 + 3 * 5 + 4 * 1 * 7')

    assert len(forest) == 42

    assert forest[0].to_str() == forest.get_tree().to_str()
    assert forest[17].to_str() == forest.get_tree(17).to_str()
    assert forest[41].to_str() == forest.get_tree(41).to_str()
    with pytest.raises(IndexError):
        forest[42]


def test_non_lazy_tree_enumeration(parser):
    forest = parser.parse('2 + 3 * 5 + 4 * 1 * 7')

    tree = forest.get_nonlazy_tree()

    assert tree.is_nonterm()
    assert tree.symbol.name == 'E'
    assert len(tree.children) == 3
    assert 'Ambiguity' not in tree.to_str()

    tree = forest.get_nonlazy_tree(5)
    assert tree.is_nonterm()
    assert tree.symbol.name == 'E'
    assert len(tree.children) == 3
    assert 'Ambiguity' not in tree.to_str()

    # Last tree
    tree = forest.get_nonlazy_tree(len(forest)-1)
    assert tree.is_nonterm()
    assert tree.symbol.name == 'E'
    assert len(tree.children) == 3
    assert 'Ambiguity' not in tree.to_str()

    # If idx is greater than the number of solutions
    # exception is raised
    with pytest.raises(IndexError):
        forest.get_nonlazy_tree(len(forest)).to_str()


def test_lazy_tree_enumeration(parser):
    forest = parser.parse('2 + 3 * 5 + 4 * 1 * 7')

    tree = forest.get_tree()

    assert tree.is_nonterm()
    assert tree.symbol.name == 'E'
    assert len(tree.children) == 3
    assert 'Ambiguity' not in tree.to_str()

    tree = forest.get_tree(5)
    assert tree.is_nonterm()
    assert tree.symbol.name == 'E'
    assert len(tree.children) == 3
    assert 'Ambiguity' not in tree.to_str()

    # Last tree
    tree = forest.get_tree(len(forest)-1)
    assert tree.is_nonterm()
    assert tree.symbol.name == 'E'
    assert len(tree.children) == 3
    assert 'Ambiguity' not in tree.to_str()

    # If idx is greater than the number of solutions
    # exception is raised
    with pytest.raises(IndexError):
        forest.get_tree(len(forest)).to_str()


def test_no_equal_trees(parser):
    """
    Test that forest returns different trees.
    """
    forest = parser.parse('2 + 3 * 5 + 4 * 1 * 7 + 9 + 10')

    # Non-lazy iterator
    trees = set()
    for tree in forest.nonlazy_iter():
        tree_str = tree.to_str()
        assert tree_str not in trees
        trees.add(tree_str)

    # Lazy iterator
    trees = set()
    for tree in forest:
        tree_str = tree.to_str()
        assert tree_str not in trees
        trees.add(tree_str)


def test_lazy_nonlazy_same_trees(parser):
    """
    Test that both lazy and non lazy iterators return same trees.
    """
    forest = parser.parse('2 + 3 * 5 + 4 * 1 * 7 + 9 + 10')

    for tree, lazy_tree in zip(forest.nonlazy_iter(), forest):
        assert tree.to_str() == lazy_tree.to_str()


def test_multiple_iteration(parser):
    """
    Test that tree can be iterated multiple times yielding the
    same result.
    """
    forest = parser.parse('2 + 3 * 5 + 4 * 1 * 7 + 9 + 10')
    for tree in forest:
        assert tree.to_str() == tree.to_str()

    for tree in forest.nonlazy_iter():
        assert tree.to_str() == tree.to_str()
