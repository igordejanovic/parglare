import sys
import click

if sys.version < '3':
    text = unicode  # NOQA
else:
    text = str

colors = False

S_ATTENTION = {'fg': 'red', 'bold': True}
S_HEADER = {'fg': 'green'}
S_EMPH = {'fg': 'yellow'}


def prints(message, s={}):
    click.echo(style(message, s), color=colors)


def style(message, style):
    if colors:
        return click.style(message, **style)
    else:
        return message


def s_header(message):
    return style(message, S_HEADER)


def s_attention(message):
    return style(message, S_ATTENTION)


def s_emph(message):
    return style(message, S_EMPH)


def styled_print(header, content, level=0, new_line=False,
                 header_style=S_HEADER):
    new_line = "\n" if new_line else ""
    level = ("\t" * level) if level else ""
    prints(new_line
           + level
           + style(text(header), header_style)
           + ((" " + text(content)) if content else ""))


def h_print(header, content="", level=0, new_line=False):
    styled_print(header, content, level, new_line, S_HEADER)


def a_print(header, content="", level=0, new_line=False):
    styled_print(header, content, level, new_line, S_ATTENTION)
