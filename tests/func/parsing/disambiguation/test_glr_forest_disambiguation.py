# ruff: noqa: B023
"""
Forest can be disambiguated by eliminating possibilities in Parent objects.
"""
from parglare import GLRParser, Grammar, Node

# Here, we have a grammar that defines a structure of a document with different
# parts. The grammar is ambiguous. We will disambiguate the resulting forest by
# not allowing the nesting of same type document parts.
grammar = r'''
document: parts;

parts: part1+
     | part2+
     | part3+;

// To prevent nesting of the same part type we could
// spell out all possibilities in the grammar
// but for large number of part types
// it would make grammar complex.
part1: title1 parts?;
part2: title2 parts?;
part3: title3 parts?;

terminals
title1: 'part1';
title2: 'part2';
title3: 'part3';
'''


def disambiguate(parent):
    """
    Function accepting Parent object with possibilities.
    It will get called only if there is more than 1 possibility.
    It should modify the parent object to leave only valid possibilities.
    """
    valid = []

    class Invalid(Exception):
        pass

    for pos in parent:
        parts_seen = set()

        def traverse_tree(node):
            # For each possibility, descend down the sub-tree and keep parts
            # seen so far. If the same part if found the sub-tree is invalid.
            if isinstance(node, Node):
                if node.symbol in parts_seen:
                    raise Invalid()
                if node.symbol.name in ['part1', 'part2', 'part3']:
                    parts_seen.add(node.symbol)
            for n in node:
                traverse_tree(n)
            if node.symbol in parts_seen:
                parts_seen.remove(node.symbol)
        try:
            traverse_tree(pos)
        except Invalid:
            continue

        valid.append(pos)

    parent.possibilities = valid


def test_glr_forest_disambiguation():
    parser = GLRParser(Grammar.from_string(grammar))

    forest = parser.parse(r'''
    part1
     part2
      part3
     part2
    part1
     part3
      part2
     part3
    part1
     part2
      part3
    part1
     part2
    ''')

    # We have 415 solutions.
    assert len(forest) == 415
    assert forest.ambiguities == 46

    forest.disambiguate(disambiguate)

    # After the disambiguation, only one solution remains.
    assert len(forest) == 1
    assert forest.to_str().strip() == r'''
document[5->147]
  parts[5->147]
    part1_1[5->147]
      part1_1[5->126]
        part1_1[5->93]
          part1_1[5->49]
            part1[5->49]
              title1[5->10, "part1"]
              parts_opt[16->49]
                parts[16->49]
                  part2_1[16->49]
                    part2_1[16->39]
                      part2[16->39]
                        title2[16->21, "part2"]
                        parts_opt[28->39]
                          parts[28->39]
                            part3_1[28->39]
                              part3[28->39]
                                title3[28->33, "part3"]
                                parts_opt[39->39]
                    part2[39->49]
                      title2[39->44, "part2"]
                      parts_opt[49->49]
          part1[49->93]
            title1[49->54, "part1"]
            parts_opt[60->93]
              parts[60->93]
                part3_1[60->93]
                  part3_1[60->83]
                    part3[60->83]
                      title3[60->65, "part3"]
                      parts_opt[72->83]
                        parts[72->83]
                          part2_1[72->83]
                            part2[72->83]
                              title2[72->77, "part2"]
                              parts_opt[83->83]
                  part3[83->93]
                    title3[83->88, "part3"]
                    parts_opt[93->93]
        part1[93->126]
          title1[93->98, "part1"]
          parts_opt[104->126]
            parts[104->126]
              part2_1[104->126]
                part2[104->126]
                  title2[104->109, "part2"]
                  parts_opt[116->126]
                    parts[116->126]
                      part3_1[116->126]
                        part3[116->126]
                          title3[116->121, "part3"]
                          parts_opt[126->126]
      part1[126->147]
        title1[126->131, "part1"]
        parts_opt[137->147]
          parts[137->147]
            part2_1[137->147]
              part2[137->147]
                title2[137->142, "part2"]
                parts_opt[147->147]
    '''.strip()
