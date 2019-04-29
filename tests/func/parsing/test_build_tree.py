import pytest  # noqa
from parglare import Grammar, Parser


def test_call_actions_during_tree_build():
    grammar = """
    Program: "begin" MoveCommand* "end";
    MoveCommand: "move" Direction;
    Direction: "up" | "down" | "left" | "right";
    """

    g = Grammar.from_string(grammar)

    code = """
    begin
        move left
        move left
        move up
        move down
    end
    """

    left_moves = []

    def left_dir_collector(_, nodes):
        """Finds all 'left' moves and adds them into a list."""
        term = nodes[0]
        if term.value == "left":
            left_moves.append(term)

    parser = Parser(g, build_tree=True,
                    actions={"Direction": left_dir_collector})
    parser.parse(code)

    # call_actions_during_tree_build is False by default, so left_dir_collector
    # will not be called.
    assert len(left_moves) == 0

    parser.call_actions_during_tree_build = True
    parser.parse(code)

    assert len(left_moves) == 2
