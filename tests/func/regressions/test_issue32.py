import pytest
from parglare import Grammar, GrammarError


def test_conflict_between_string_match_and_rule_with_same_name():

    with pytest.raises(GrammarError, match=r'.*already defined.*'):
        Grammar.from_string('''
            Terminals:
                "Terminals" ":" terminal_list=Terminal* ";"
            ;
        ''')
