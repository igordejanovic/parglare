from parglare import Grammar, Parser, get_collector

grammar_1 = r'''
STMT : STMT ADDOP STMT {left, 1}
     | STMT MULOP STMT {left, 1}
     | "(" STMT ")" | NUMBER;
ADDOP : "+" {1}
      | "-" {1};
MULOP : "*" {2}
      | "/" {2};

terminals
NUMBER: /\d+(.\d+)?/;
'''

grammar_2 = r'''
STMT : STMT "+" STMT {left, 1}
     | STMT "-" STMT {left, 1}
     | STMT "*" STMT {left, 2}
     | STMT "/" STMT {left, 2}
     | "(" STMT ")" | NUMBER;

terminals
NUMBER: /\d+(.\d+)?/;
'''

# Grammar could be simplified a bit
# with https://github.com/igordejanovic/parglare/issues/17
grammar_3 = r'''
STMT {left}: STMT ADDOP STMT {1}
           | STMT MULOP STMT {2};
STMT: "(" STMT ")" | NUMBER;
ADDOP {1}: "+" | "-";
MULOP {2}: "*" | "/";

terminals
NUMBER: /\d+(.\d+)?/;
'''

expression = '1 - 2 / (3 - 1 + 5 / 6 - 8 + 8 * 2 - 5)'
result = 1 - 2 / (3 - 1 + 5 / 6 - 8 + 8 * 2 - 5)

action = get_collector()


@action
def NUMBER(_, value):
    return int(value)


@action
def STMT(_, nodes):
    if len(nodes) == 1:
        return nodes[0]
    elif nodes[0] == '(':
        return nodes[1]
    else:
        left, op, right = nodes

    if op == '+':
        return left + right
    elif op == '-':
        return left - right
    elif op == '*':
        return left * right
    else:
        return left / right


def test_associativity_variant_1():
    """
    See https://github.com/igordejanovic/parglare/issues/22
    """
    g = Grammar.from_string(grammar_1)
    parser = Parser(g, actions=action.all)
    r = parser.parse(expression)

    assert r == result


def test_associativity_variant_2():
    """
    See https://github.com/igordejanovic/parglare/issues/22
    """
    g = Grammar.from_string(grammar_2)
    parser = Parser(g, actions=action.all)
    r = parser.parse(expression)

    assert r == result


def test_associativity_variant_3():
    """
    See https://github.com/igordejanovic/parglare/issues/22
    Using https://github.com/igordejanovic/parglare/issues/17
    """
    g = Grammar.from_string(grammar_3)
    parser = Parser(g, actions=action.all)
    r = parser.parse(expression)

    assert r == result
