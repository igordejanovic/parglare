"""
Common parsing actions.
"""
import sys

if sys.version < '3':
    text = unicode  # NOQA
else:
    text = str


class ParglareActions(object):
    """
    Default base class for parglare actions subclasses. Defines
    common actions.
    """
    def pass_none(self, value):
        return None

    def pass_nochange(_, value):
        return value

    def pass_empty(self, value):
        """
        Used for EMPTY production alternative in collect.
        """
        return []

    def pass_single(self, nodes):
        """
        Unpack single value and pass up.
        """
        return nodes[0]

    def pass_inner(self, nodes):
        """
        Pass inner value up, e.g. for parentheses `'(' token ')'`.
        """
        return nodes[1]

    def collect_first(self, nodes):
        """
        Used for:
        Elements: Elements Element;
        """
        e1, e2 = nodes
        if e2 is not None:
            e1 = list(e1)
            e1.append(e2)
        return e1

    def collect_first_sep(self, nodes):
        """
        Used for:
        Elements: Elements "," Element;
        """
        e1, _, e2 = nodes
        if e2 is not None:
            e1 = list(e1)
            e1.append(e2)
        return e1

    def collect_right_first(self, nodes):
        """
        Used for:
        Elements: Element Elements;
        """
        e1, e2 = [nodes[0]], nodes[1]
        e1.extend(e2)
        return e1

    def collect_right_first_sep(self, nodes):
        """
        Used for:
        Elements: Element "," Elements;
        """
        e1, e2 = [nodes[0]], nodes[2]
        e1.extend(e2)
        return e1

    def collect(self, nodes):
        """
        Used for productions of the form - one or more elements:
        Elements: Elements Element | Element;
        """
        [self.collect_first, self.pass_nochange][self.prod_idx](nodes)

    def collect_sep(self, nodes):
        """
        Used for productions of the form - one or more elements:
        Elements: Elements "," Element | Element;
        """
        [self.collect_first_sep, self.pass_nochange][self.prod_idx](nodes)

    def collect_optional(self, nodes):
        """
        Used for productions of the form - zero or more elements:
        Elements: Elements Element | Element | EMPTY;
        """
        [self.collect_first,
         self.pass_nochange, self.pass_empty][self.prod_idx](nodes)

    def collect_sep_optional(self, nodes):
        """
        Used for productions of the form - zero or more elements:
        Elements: Elements "," Element | Element | EMPTY;
        """
        [self.collect_first_sep,
         self.pass_nochange, self.pass_empty][self.prod_idx](nodes)

    def collect_right(self, nodes):
        """
        Used for productions of the form - one or more elements:
        Elements: Element Elements | Element;
        """
        [self.collect_right_first, self.pass_nochange][self.prod_idx](nodes)

    def collect_right_sep(self, nodes):
        """
        Used for productions of the form - one or more elements:
        Elements: Element "," Elements | Element;
        """
        [self.collect_right_first_sep,
         self.pass_nochange][self.prod_idx](nodes)

    def collect_right_optional(self, nodes):
        """
        Used for productions of the form - zero or more elements:
        Elements: Element Elements | Element | EMPTY;
        """
        [self.collect_right_first,
         self.pass_nochange, self.pass_empty][self.prod_idx](nodes)

    def collect_right_sep_optional(self, nodes):
        """
        Used for productions of the form - zero or more elements:
        Elements: Element "," Elements | Element | EMPTY;
        """
        [self.collect_right_first_sep,
         self.pass_nochange, self.pass_empty][self.prod_idx](nodes)

    def optional(self, nodes):
        """
        Used for the production of the form:
        OptionalElement: Element | EMPTY;
        """
        [self.pass_single, self.pass_none][self.prod_idx](nodes)

    def obj(self, nodes, **attrs):
        """
        Creates Python object with the attributes created from named matches.
        This action is used as default action for rules with named matches.
        """
        grammar = self.parser.grammar
        rule_name = self.production.symbol.fqn

        cls = grammar.classes[rule_name]
        instance = cls(**attrs)

        instance._pg_start_position = self.start_position
        instance._pg_end_position = self.end_position

        return instance
