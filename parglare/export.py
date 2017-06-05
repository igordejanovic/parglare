from __future__ import unicode_literals
from parglare.parser import REDUCE, SHIFT, ACCEPT
import codecs
import sys
if sys.version < '3':
    text = unicode  # noqa
else:
    text = str


HEADER = '''
    digraph grammar {
    rankdir=LR
    fontname = "Bitstream Vera Sans"
    fontsize = 8
    node[
        shape=record,
        style=filled,
        fillcolor=aliceblue
    ]
    nodesep = 0.3
    edge[dir=black,arrowtail=empty]


'''


def dot_escape(s):
    return s.replace('\n', r'\n')\
            .replace('\\', '\\\\')\
            .replace('"', r'\"')\
            .replace('|', r'\|')\
            .replace('{', r'\{')\
            .replace('}', r'\}')\
            .replace('>', r'\>')\
            .replace('<', r'\<')\
            .replace('?', r'\?')


def grammar_pda_export(states, all_actions, all_goto, file_name):

    with codecs.open(file_name, 'w', encoding="utf-8") as f:
        f.write(HEADER)

        for state in states:

            kernel_items = ""
            for item in state.kernel_items:
                kernel_items += "{}\\l".format(dot_escape(text(item)))

            nonkernel_items = ""
            for item in state.nonkernel_items:
                nonkernel_items += "{}\\l".format(dot_escape(text(item)))

            # SHIFT actions and GOTOs will be encoded in links.
            # REDUCE actions will be presented inside each node.
            reduce_actions = [(term, action)
                              for term, action
                              in all_actions[state.state_id].items()
                              if action.action == REDUCE]
            reductions = ""
            if reduce_actions:
                reductions = "Reductions:\\l{}".format(
                    ", ".join(["{}:{}".format(x[0], x[1].prod.prod_id)
                               for x in reduce_actions]))

            # States
            f.write('{}[label="{}|{}|{}|{}"]\n'
                    .format(
                        state.state_id,
                        dot_escape("{}:{}"
                                   .format(state.state_id, state.symbol)),
                        kernel_items, nonkernel_items, reductions))

            f.write("\n")

            # SHIFT and GOTOs as links
            for term, action in ((term, action) for term, action
                                 in all_actions[state.state_id].items()
                                 if action.action in [SHIFT, ACCEPT]):
                    f.write('{} -> {} [label="{}:{}"]'.format(
                        state.state_id, action.state.state_id,
                        "SHIFT" if action.action == SHIFT else "ACCEPT", term))

            for symb, goto_state in ((symb, goto) for symb, goto
                                     in all_goto[state.state_id].items()):
                    f.write('{} -> {} [label="GOTO:{}"]'.format(
                        state.state_id, goto_state.state_id, symb))

        f.write("\n}\n")
