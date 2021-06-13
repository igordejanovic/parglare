import pytest
import sys
from parglare import Grammar, GLRParser

grammar = r"""
Sentence: KindDefinitionSentence | OtherSentence;
KindDefinitionSentence: "a" IdentifierWord* "is" "a" "kind" "of" IdentifierWord* KindWith? DOT;
OtherSentence: IdentifierWord* DOT;
KindWith: "with" IdentifierWord*;

terminals

IdentifierWord: /\w+/;
DOT: ".";
"""  # noqa


@pytest.mark.skipif(sys.version_info < (3, 6),
                    reason="list comparison doesn't work "
                    "correctly in pytest 4.1")
def test_issue_114_empty_and_lexical_ambiguity():

    g = Grammar.from_string(grammar)
    parser = GLRParser(g, build_tree=True)

    results = parser.parse("a car is a kind of vehicle.")
    assert len(results) == 2

    expected = r'''
Sentence[0->27]
  KindDefinitionSentence[0->27]
    a[0->1, "a"]
    IdentifierWord_0[2->5]
      IdentifierWord_1[2->5]
        IdentifierWord[2->5, "car"]
    is[6->8, "is"]
    a[9->10, "a"]
    kind[11->15, "kind"]
    of[16->18, "of"]
    IdentifierWord_0[19->26]
      IdentifierWord_1[19->26]
        IdentifierWord[19->26, "vehicle"]
    KindWith_opt[26->26]
    DOT[26->27, "."]

Sentence[0->27]
  OtherSentence[0->27]
    IdentifierWord_0[0->26]
      IdentifierWord_1[0->26]
        IdentifierWord_1[0->18]
          IdentifierWord_1[0->15]
            IdentifierWord_1[0->10]
              IdentifierWord_1[0->8]
                IdentifierWord_1[0->5]
                  IdentifierWord_1[0->1]
                    IdentifierWord[0->1, "a"]
                  IdentifierWord[2->5, "car"]
                IdentifierWord[6->8, "is"]
              IdentifierWord[9->10, "a"]
            IdentifierWord[11->15, "kind"]
          IdentifierWord[16->18, "of"]
        IdentifierWord[19->26, "vehicle"]
    DOT[26->27, "."]
    '''

    assert '\n\n'.join([r.to_str()
                        for r in results]).strip() == expected.strip()

    results = parser.parse("a car is a kind of vehicle with wheels.")
    assert len(results) == 3

    expected = r'''
Sentence[0->39]
  OtherSentence[0->39]
    IdentifierWord_0[0->38]
      IdentifierWord_1[0->38]
        IdentifierWord_1[0->31]
          IdentifierWord_1[0->26]
            IdentifierWord_1[0->18]
              IdentifierWord_1[0->15]
                IdentifierWord_1[0->10]
                  IdentifierWord_1[0->8]
                    IdentifierWord_1[0->5]
                      IdentifierWord_1[0->1]
                        IdentifierWord[0->1, "a"]
                      IdentifierWord[2->5, "car"]
                    IdentifierWord[6->8, "is"]
                  IdentifierWord[9->10, "a"]
                IdentifierWord[11->15, "kind"]
              IdentifierWord[16->18, "of"]
            IdentifierWord[19->26, "vehicle"]
          IdentifierWord[27->31, "with"]
        IdentifierWord[32->38, "wheels"]
    DOT[38->39, "."]

Sentence[0->39]
  KindDefinitionSentence[0->39]
    a[0->1, "a"]
    IdentifierWord_0[2->5]
      IdentifierWord_1[2->5]
        IdentifierWord[2->5, "car"]
    is[6->8, "is"]
    a[9->10, "a"]
    kind[11->15, "kind"]
    of[16->18, "of"]
    IdentifierWord_0[19->38]
      IdentifierWord_1[19->38]
        IdentifierWord_1[19->31]
          IdentifierWord_1[19->26]
            IdentifierWord[19->26, "vehicle"]
          IdentifierWord[27->31, "with"]
        IdentifierWord[32->38, "wheels"]
    KindWith_opt[38->38]
    DOT[38->39, "."]

Sentence[0->39]
  KindDefinitionSentence[0->39]
    a[0->1, "a"]
    IdentifierWord_0[2->5]
      IdentifierWord_1[2->5]
        IdentifierWord[2->5, "car"]
    is[6->8, "is"]
    a[9->10, "a"]
    kind[11->15, "kind"]
    of[16->18, "of"]
    IdentifierWord_0[19->26]
      IdentifierWord_1[19->26]
        IdentifierWord[19->26, "vehicle"]
    KindWith_opt[27->38]
      KindWith[27->38]
        with[27->31, "with"]
        IdentifierWord_0[32->38]
          IdentifierWord_1[32->38]
            IdentifierWord[32->38, "wheels"]
    DOT[38->39, "."]
    '''

    assert '\n\n'.join([r.to_str()
                        for r in results]).strip() == expected.strip()
