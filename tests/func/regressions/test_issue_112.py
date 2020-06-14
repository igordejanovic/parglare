from parglare import Grammar, GLRParser


def test_issue_112_fail_on_empty():

    grammar = r'''
    sentence1:              subordinateClause* clause sentenceEnd;

    subordinateClause:      clause clauseConnector;

    clause:                 singleNounPhrase* verbPhrase;

    // ----------
    singleNounPhrase:       determiner? simpleNoun;
    // ----------

    verbPhrase:             simpleVerb verbSuffix* predicateEndingSuffix?;

    terminals
        sentenceEnd:            /[^:]+:(SF);/;
        clauseConnector:        /[^:]+:(EC|CCF|CCMOD|CCNOM);/;
        determiner:             /[^:]+:(MM);/;
        simpleNoun:             /[^:]+:(NNG|NNP|NNB|NR|SL|NP|SN);/;
        simpleVerb:             /[^:]+:(VV|VVD|VHV);/;
        verbSuffix:             /[^:]+:(EP|TNS);/;
        predicateEndingSuffix:  /[^:]+:(SEF|EF);/;
    '''

    g = Grammar.from_string(grammar)
    parser = GLRParser(g, build_tree=True)

    results = parser.parse('자전거:NNG; 있:VV; 어요:SEF; .:SF;')

    expected = r'''
sentence1[0->28]
subordinateClause_0[0->0]
clause[0->22]
  singleNounPhrase_0[0->8]
    singleNounPhrase_1[0->8]
      singleNounPhrase[0->8]
        determiner_opt[0->0]
        simpleNoun[0->8, "자전거:NNG;"]
  verbPhrase[9->22]
    simpleVerb[9->14, "있:VV;"]
    verbSuffix_0[15->15]
    predicateEndingSuffix_opt[15->22]
      predicateEndingSuffix[15->22, "어요:SEF;"]
sentenceEnd[23->28, ".:SF;"]

'''

    assert len(results) == 1
    assert results[0].tree_str().strip() == expected.strip()
