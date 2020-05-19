"""
Common parsing actions.
"""
import sys

if sys.version < '3':
    text = unicode  # NOQA
else:
    text = str


class Actions(object):
    """
    Default base class for parglare actions subclasses. Defines
    common actions.
    """
    def none(self, value):
        return None

    def nochange(self, value):
        return value

    def empty(self, value):
        """
        Used for EMPTY production alternative in collect.
        """
        return []

    def single(self, nodes):
        """
        Unpack single value and pass up.
        """
        return nodes[0]

    def inner(self, nodes):
        """
        Pass inner value up, e.g. for stripping parentheses as in
        `( <some expression> )`.
        """
        n = nodes[1:-1]
        try:
            n, = n
        except ValueError:
            pass
        return n

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
        return [self.collect_first, self.nochange][self.prod_idx](nodes)

    def collect_sep(self, nodes):
        """
        Used for productions of the form - one or more elements:
        Elements: Elements "," Element | Element;
        """
        return [self.collect_first_sep,
                self.nochange][self.prod_idx](nodes)

    def collect_optional(self, nodes):
        """
        Used for productions of the form - zero or more elements:
        Elements: Elements Element | Element | EMPTY;
        """
        return [self.collect_first,
                self.nochange, self.empty][self.prod_idx](nodes)

    def collect_sep_optional(self, nodes):
        """
        Used for productions of the form - zero or more elements:
        Elements: Elements "," Element | Element | EMPTY;
        """
        return [self.collect_first_sep,
                self.nochange, self.empty][self.prod_idx](nodes)

    def collect_right(self, nodes):
        """
        Used for productions of the form - one or more elements:
        Elements: Element Elements | Element;
        """
        return [self.collect_right_first,
                self.nochange][self.prod_idx](nodes)

    def collect_right_sep(self, nodes):
        """
        Used for productions of the form - one or more elements:
        Elements: Element "," Elements | Element;
        """
        return [self.collect_right_first_sep,
                self.nochange][self.prod_idx](nodes)

    def collect_right_optional(self, nodes):
        """
        Used for productions of the form - zero or more elements:
        Elements: Element Elements | Element | EMPTY;
        """
        return [self.collect_right_first,
                self.nochange, self.empty][self.prod_idx](nodes)

    def collect_right_sep_optional(self, nodes):
        """
        Used for productions of the form - zero or more elements:
        Elements: Element "," Elements | Element | EMPTY;
        """
        return [self.collect_right_first_sep,
                self.nochange, self.empty][self.prod_idx](nodes)

    def optional(self, nodes):
        """
        Used for the production of the form:
        OptionalElement: Element | EMPTY;
        """
        return [self.single, self.none][self.prod_idx](nodes)

    def obj(self, nodes, **attrs):
        """
        Creates Python object with the attributes created from named matches.
        This action is used as default action for rules with named matches.
        """
        grammar = self.parser.grammar
        rule_name = self.context.production.symbol.name

        cls = grammar.classes[rule_name]
        instance = cls(**attrs)

        instance._pg_start_position = self.context.start_position
        instance._pg_end_position = self.context.end_position

        return instance

    def EMPTY(self, nodes):
        return self.none(nodes)
