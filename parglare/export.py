from __future__ import unicode_literals
from parglare.parser import REDUCE, SHIFT, ACCEPT
import codecs
import sys
from parglare import termui as t
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
    colors = t.colors
    t.colors = False
    s = text(s)
    out = s.replace('\n', r'\n')\
           .replace('\\', '\\\\')\
           .replace('"', r'\"')\
           .replace('|', r'\|')\
           .replace('{', r'\{')\
           .replace('}', r'\}')\
           .replace('>', r'\>')\
           .replace('<', r'\<')\
           .replace('?', r'\?')
    t.colors = colors
    return out


def grammar_pda_export(table, file_name):

    with codecs.open(file_name, 'w', encoding="utf-8") as f:
        f.write(HEADER)

        for state in table.states:

            kernel_items = ""
            for item in state.kernel_items:
                kernel_items += "{}\\l".format(dot_escape(text(item)))

            nonkernel_items = "|" if state.nonkernel_items else ""
            for item in state.nonkernel_items:
                nonkernel_items += "{}\\l".format(dot_escape(text(item)))

            # SHIFT actions and GOTOs will be encoded in links.
            # REDUCE actions will be presented inside each node.
            reduce_actions = []
            for term, actions in state.actions.items():
                r_actions = [a for a in actions if a.action is REDUCE]
                if r_actions:
                    reduce_actions.append((term, r_actions))

            reductions = ""
            if reduce_actions:
                reductions = "|Reductions:\\l{}".format(
                    ", ".join(["{}:{}".format(
                        dot_escape(x[0].name), x[1][0].prod.prod_id
                        if len(x[1]) == 1 else "[{}]".format(
                                ",".join([str(i.prod.prod_id) for i in x[1]])))
                               for x in reduce_actions]))

            # States
            f.write('{}[label="{}|{}{}{}"]\n'
                    .format(
                        state.state_id,
                        dot_escape("{}:{}"
                                   .format(state.state_id, state.symbol)),
                        kernel_items, nonkernel_items, reductions))

            f.write("\n")

            # SHIFT and GOTOs as links
            shacc = []
            for term, actions in state.actions.items():
                for a in [a for a in actions if a.action in [SHIFT, ACCEPT]]:
                    shacc.append((term, a))
            for term, action in shacc:
                    f.write('{} -> {} [label="{}:{}"]'.format(
                        state.state_id, action.state.state_id,
                        "SHIFT" if action.action == SHIFT else "ACCEPT", term))

            for symb, goto_state in ((symb, goto) for symb, goto
                                     in state.gotos.items()):
                    f.write('{} -> {} [label="GOTO:{}"]'.format(
                        state.state_id, goto_state.state_id, symb))

        f.write("\n}\n")
