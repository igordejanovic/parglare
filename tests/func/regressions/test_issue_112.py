import pytest
from parglare import Grammar, GLRParser, ParseError


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
    assert results[0].to_str().strip() == expected.strip()


def test_issue_112_wrong_error_report():
    """
    Test that token ahead is not among expected symbols in error message.
    """
    grammar = r'''
    _input:                  sentence
                        |   standalonePhrase;

    standalonePhrase:       interjection* __phrase;

    sentence:               interjection* sentence1
                        |   sentenceJoiningAdverb? sentence1;

    sentence1:              subordinateClause* _clause sentenceEnd
                        |   subordinateClause* quotationShortForm;

    subordinateClause:      _clause clauseConnector punctuation*;


    _clause:                __phrase* verbPhrase
                        |   __phrase* complement? copulaPhrase;

    // ---- phrases ----

    __phrase:                 topic
                        |   subject
                        |   object
                        |   adjectivalPhrase
                        |   adverbialPhrase
                        |   nounPhrase;

    topic:                  nounPhrase topicMarker;
    subject:                nounPhrase subjectMarker;
    object:                 nounPhrase objectMarker;
    complement:             nounPhrase complementMarker?;
    adjectivalPhrase:       adjective+ nounPhrase;

    // ---- noun-related ----

    nounPhrase:             singleNounPhrase
                        |   combinedNounPhrase;

    combinedNounPhrase:     singleNounPhrase continuedNounPhrase+;
    continuedNounPhrase:    conjunction singleNounPhrase;


    singleNounPhrase:       determiner singleNounPhrase1 auxiliaryParticle* punctuation*
                        |   singleNounPhrase1 auxiliaryParticle* punctuation*;
    singleNounPhrase1:      basicNounPhrase
                        |   modifiedNounPhrase
                        |   countingPhrase;

    basicNounPhrase:        noun+
                        |   possessive;
    possessive:             noun+ possessiveMarker;

    modifiedNounPhrase:     basicNounPhrase nounModifyingSuffix;

    countingPhrase:         basicNounPhrase number
                        |   basicNounPhrase number counter
                        |   number basicNounPhrase
                        |   counter possessiveMarker basicNounPhrase;

    noun:                   simpleNoun
                        |   nominalForm
                        |   nominalizedVerb
                        |   verbModifiedToNoun;

    nominalizedVerb:        _clause nominalizingSuffix;
    verbModifiedToNoun:     _clause verbToNounModifyingForm;

    adjective:              _clause adnominalSuffix
                        |   possessive;

    // ---- verb-related ----

    copulaPhrase:           adverb* copula verbSuffix* predicateEndingSuffix?;

    verbPhrase:             adverb* verbPhrase1 nominalVerbForm? verbSuffix* predicateEndingSuffix?;
    verbPhrase1:            basicVerbPhrase
                        |   negative basicVerbPhrase
                        |   basicVerbPhrase negative;

    basicVerbPhrase:        verbCombination
                        |   honorificVerb
                        |   verbAndAuxiliary
                        |   modifiedVerb
                        |   indirectQuotation
                        |   nominalAsVerb;

    verbCombination:        verb
                        |   verb verbCombiner verbCombination;

    verb:                   simpleVerb
                        |   descriptiveVerb;

    honorificVerb:          verb honorificMarker;

    verbAndAuxiliary:       verb nominalVerbForm? verbSuffix* auxiliaryVerb+;
    modifiedVerb:           verb honorificMarker? verbModifier
                        |   verbAndAuxiliary honorificMarker? verbModifier;
    nominalAsVerb:          verb verbNominal
                        |   verbAndAuxiliary verbNominal;

    auxiliaryVerb:          simpleAuxiliaryVerb honorificMarker?
                        |   auxiliaryVerbForm honorificMarker?;
    simpleAuxiliaryVerb:    auxiliaryVerbConnector verb;

    adverbialPhrase:        nounPhrase adverbialParticle auxiliaryParticle*
                        |   verb adverbialParticle auxiliaryParticle*;

    // ---- quotation forms ----

    indirectQuotation:      verb quotationSuffix;

    quotationShortForm:     basicVerbPhrase shortQuotationSuffix verbSuffix* predicateEndingSuffix?;

    // ------ others -----

    interjection:           interjectionTerminal punctuation*;

    // --- terminal symbols ------------------------------

    terminals
        sentenceEnd:            /[^:]+:(SF);/;
        interjectionTerminal:   /[^:]+:(IC);/;
        punctuation:            /[^:]+:(SP|SS|SE|SO|SW|SWK);/;
        clauseConnector:        /[^:]+:(EC|CCF|CCMOD|CCNOM);/;
        topicMarker:            /[^:]+:(TOP);/;
        objectMarker:           /[^:]+:(JKO);/;
        subjectMarker:          /[^:]+:(JKS);/;
        complementMarker:       /[^:]+:(JKC);/;
        conjunction:            /[^:]+:(JC|CON);/;
        determiner:             /[^:]+:(MM);/;
        auxiliaryParticle:      /[^:]+:(JX);/;
        possessiveMarker:       /[^:]+:(JKG);/;
        nounModifyingSuffix:    /[^:]+:(XSN|JKV);/;
        nominalizingSuffix:     /[^:]+:(ETN);/;
        adnominalSuffix:        /[^:]+:(ETM);/;
        verbSuffix:             /[^:]+:(EP|TNS);/;
        predicateEndingSuffix:  /[^:]+:(SEF|EF);/;
        negative:               /[^:]+:(NEG);/;
        verbCombiner:           /고:(EC|CCF);/;
        honorificMarker:        /(으시|시):EP;/;
        verbModifier:           /[^:]+:(VMOD);/;
        verbNominal:            /[^:]+:(VNOM);/;
        adverbialParticle:      /[^:]+:(JKB);/;
        quotationSuffix:        /[^:]+:(QOT);/;
        shortQuotationSuffix:   /[^:]+:(SQOT);/;
        sentenceJoiningAdverb:  /[^:]+:MAJ;/;
        simpleNoun:             /[^:]+:(NNG|NNP|NNB|NR|SL|NP|SN);/;
        adverb:                 /[^:]+:(MAG);/;
        simpleVerb:             /[^:]+:(VV|VVD|VHV);/;
        descriptiveVerb:        /[^:]+:(VA|VCP|VCN|VAD|VHA);/;
        auxiliaryVerbConnector: /[^:]+:(EC);/;
        auxiliaryVerbForm:      /[^:]+:(EC);/;
        copula:                 /(되:VV)|([^:]+:(VCP|VCN));/;
        number:                 /[^:]+:(SN|NR);/;
        counter:                /[^:]+:(NNB|NNG);/;
        nominalForm:            /[^:]+:(NNOM);/;
        verbToNounModifyingForm: /[^:]+:(NMOD);/;
        nominalVerbForm:        /[^:]+:(VNOM);/;
    '''  # noqa

    g = Grammar.from_string(grammar)
    parser = GLRParser(g)
    with pytest.raises(ParseError) as e:
        parser.parse('공부하:VHV; 는:ETM; 것:NNB; 은:TOP; 아니:VCN; ㅂ니다:SEF; .:SF;')

    assert 'Expected: adnominalSuffix or nominalizingSuffix or '\
        'verbToNounModifyingForm but found <sentenceEnd(.:SF;)>'\
        in str(e.value)
