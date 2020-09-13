# -*- coding: utf-8 -*-
import os
from copy import deepcopy
from typing import Dict, Union, List, Iterator, TypeVar, ContextManager, Optional, Callable, Any, Sequence

from parglare.exceptions import GrammarBuilderValidationError
from parglare.grammar import MULT_ONE_OR_MORE, MULT_ZERO_OR_MORE, MULT_OPTIONAL, Terminal, MULT_ONE

Action = Callable[[Any, List[Any]], Any]  # TODO: Narrow this down a bit, if possible.
Struct = Union[None, bool, int, float, str, Action, List['Struct'], Dict[str, 'Struct']]

SelfType = TypeVar('SelfType')
ParentType = TypeVar('ParentType')


MULT_SYMBOLS = {
    MULT_ONE: '',
    MULT_OPTIONAL: '?',
    MULT_ZERO_OR_MORE: '*',
    MULT_ONE_OR_MORE: '+'
}


class BuilderBase(ContextManager):
    """Base class for grammar builder family"""

    def __init__(self, parent: ParentType):
        self._parent = parent  # type: ParentType
        self._children = []
        self._closed = False
        if parent is not self:
            parent.add_child(self)

    @property
    def closed(self) -> bool:
        """A bool indicating whether end() has already been called on the builder."""
        return self._closed

    def add_child(self, child: 'BuilderBase') -> None:
        """Add a child builder to this builder's children.
        Used to ensure that children are closed when the parent is closed."""
        if self._closed:
            raise ValueError("Parent builder is already closed.")
        self._children.append(child)

    def __getattr__(self, item: str) -> Any:
        """A little magic to automatically call self.end() and move back to the parent builder when a parent attribute
        is accessed.

        This method only gets called if the normal lookup mechanism for an attribute fails. In other words, we only
        get here if someone requests an attribute that this object doesn't have. When this happens, we call self.end()
        and then get try to get the attribute from the parent. If we are correct in doing so, everything is beautiful.
        If we are wrong to do it, the search will propagate up to the root and fail, which looks exactly like failing
        directly from the perspective of the caller.

        NOTE: Because of this feature, it's even more important that the methods in all the builder classes be clearly
              named, and only share a name if they have the same purpose. Otherwise, the user is going to get confused
              very easily.
        """
        if self._parent is self:
            # We have reached the root of the hierarchy and should end the search.
            raise AttributeError(item)

        attribute = getattr(self._parent, item)
        self.end()
        return attribute

    def iter_validation_errors(self) -> Iterator[str]:
        """Return an iterator over validation error messages for the builder's current state."""
        raise NotImplementedError()

    def validate(self: SelfType) -> SelfType:
        """Validate the builder's current state. Raise a GrammarBuilderValidationError if any problems are detected."""
        if self._parent is not self and self._parent.closed:
            raise GrammarBuilderValidationError("Parent is already closed.")
        for validation_error in self.iter_validation_errors():
            raise GrammarBuilderValidationError(validation_error)
        return self

    def _apply(self) -> None:
        """Apply the effects of this builder to the grammar struct."""
        raise NotImplementedError()

    def end(self) -> ParentType:
        """Close the builder, validating it and applying changes in the process. Any children left open will be
        closed as well. This is a no-op if end() has already been called for this builder. Return the parent builder."""
        if self._closed:
            return self._parent
        try:
            for child in list(self._children):
                child.end()
            self.validate()
            self._apply()
            return self._parent
        finally:
            self._closed = True

    def __enter__(self: SelfType) -> SelfType:
        """This and __exit__ work together to allow a builder to be used as a context manager in a 'with' statement:

            with GrammarBuilder() as builder:
                with builder.rule('A') as rule:
                    rule.production('B', 'C')  # A: B C
                    rule.production('C', 'D')  # B: C D
                struct = builder.get_struct()
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """See doc string for __enter__."""
        self.end()


class RuleBuilder(BuilderBase):
    """Builds a rule for a grammar"""

    def __init__(self, grammar_builder: 'GrammarBuilder', grammar_struct: Struct, symbol: str):
        self._grammar_struct = grammar_struct  # type: Struct
        self._symbol = symbol  # type: str
        self._rule_struct = {'productions': []}  # type: Dict[str, Struct]
        if self._symbol in grammar_struct['rules']:
            raise GrammarBuilderValidationError("Symbol is already defined as a rule: %r" % self._symbol)
        if self._symbol in grammar_struct['terminals']:
            raise GrammarBuilderValidationError("Symbol is already defined as a terminal: %r" % self._symbol)
        super().__init__(grammar_builder)

    def iter_validation_errors(self) -> Iterator[str]:
        if not self._rule_struct['productions']:
            yield "Empty rule for symbol: %r" % self._symbol

    def set_action(self: SelfType, action: Union[str, Action]) -> SelfType:
        if 'action' in self._productions_struct:
            raise GrammarBuilderValidationError("Action is already set for symbol: %r" % self._symbol)
        self._productions_struct['action'] = action
        return self

    def production(self, *args: Union[str, Terminal, tuple, dict], action: Union[str, Action] = None,
                   modifiers: Union[str, Sequence[str]] = None) -> 'ProductionBuilder':
        production_builder = ProductionBuilder(self, self._rule_struct['productions'], self._symbol)
        for arg in args:
            if isinstance(arg, (list, tuple)):
                production_builder.append(*arg)
            elif isinstance(arg, dict):
                production_builder.append(**arg)
            else:
                if isinstance(arg, Terminal):
                    arg = str(arg)
                production_builder.append(arg)
        if action is not None:
            production_builder.action(action)
        if modifiers is not None:
            if isinstance(modifiers, (list, tuple)):
                production_builder.modifiers(*modifiers)
            else:
                production_builder.modifiers(modifiers)
        return production_builder

    def action(self, action: Union[str, Action]) -> 'RuleBuilder':
        if 'action' in self._rule_struct:
            raise GrammarBuilderValidationError("Action is already set for rule: %r" % self._symbol)
        self._rule_struct['action'] = action
        return self

    def _apply(self) -> None:
        assert self._rule_struct['productions']
        grammar_rules = self._grammar_struct['rules']  # type: Struct
        grammar_rules[self._symbol] = self._rule_struct


class ProductionBuilder(BuilderBase):
    """Builds a production for a grammar rule"""

    def __init__(self, rule_builder: 'RuleBuilder', productions_list: Struct, symbol: str):
        self._productions_list = productions_list  # type: List[Struct]
        self._symbol = symbol  # type: str
        self._production_struct = {'production': []}  # type: Dict[str, Struct]
        super().__init__(rule_builder)

    def iter_validation_errors(self) -> Iterator[str]:
        if not self._production_struct['production']:
            yield "Empty rule for symbol: %r" % self._symbol

    def append(self, symbol: str, mult=None, modifiers=None) -> 'ProductionBuilder':
        if mult is None and modifiers is None:
            entry = symbol  # type: Struct
        else:
            entry = {'symbol': symbol}  # type: Struct
            if mult is not None:
                entry['mult'] = mult
            if modifiers is not None:
                entry['modifiers'] = modifiers
        self._production_struct['production'].append(entry)
        return self

    def modifiers(self, *modifiers: str) -> 'ProductionBuilder':
        if 'modifiers' in self._production_struct:
            raise GrammarBuilderValidationError("Modifier already set for rule production: %r" % self._symbol)
        else:
            self._production_struct['modifiers'] = list(modifiers)
        return self

    def _apply(self) -> None:
        self._productions_list.append(self._production_struct)


class TerminalBuilder(BuilderBase):
    """Builds a terminal for a grammar"""

    def __init__(self, grammar_builder: 'GrammarBuilder', grammar_struct: Struct, symbol: str):
        self._grammar_struct = grammar_struct  # type: Struct
        self._symbol = symbol  # type: str
        self._recognizer = None  # type: Optional[str]
        if self._symbol in self._grammar_struct['rules']:
            raise GrammarBuilderValidationError("Symbol is already defined as a rule: %r" % self._symbol)
        if self._symbol in self._grammar_struct['terminals']:
            raise GrammarBuilderValidationError("Terminal symbol is already defined: %r" % self._symbol)
        super().__init__(grammar_builder)

    def iter_validation_errors(self) -> Iterator[str]:
        if self._recognizer is None:
            yield "Recognizer not set for symbol: %r" % self._symbol

    def recognizer(self: SelfType, recognizer: str) -> SelfType:
        if self._recognizer is not None:
            raise GrammarBuilderValidationError("Recognizer already set for terminal: %r" % self._symbol)
        self._recognizer = recognizer
        return self

    def _apply(self) -> None:
        terminals = self._grammar_struct['terminals']  # type: Struct
        terminals[self._symbol] = {
            'recognizer': self._recognizer
        }


class GrammarBuilder(BuilderBase):
    """Builds a grammar programmatically"""

    def __init__(self):
        self._grammar_struct = {
            'rules': {},
            'terminals': {},
        }  # type: Struct
        super().__init__(self)

    def iter_validation_errors(self) -> Iterator[str]:
        """Return an iterator over the error messages generated when validating the grammar."""
        if 'start' not in self._grammar_struct:
            yield 'No start symbol defined.'
        elif self._grammar_struct['start'] not in self._grammar_struct['rules']:
            yield 'No rule for start symbol: %s' % self._grammar_struct['start']

    def save(self, path: str, overwrite: bool = False) -> 'GrammarBuilder':
        self.end()
        if not overwrite and os.path.isfile(path):
            raise FileExistsError(path)
        with open(path, 'w') as file:
            file.write(self.to_string())
        return self

    def to_string(self, rule_spacing: int = 1, terminal_spacing: int = 0) -> str:
        self.end()
        lines = []
        start = self._grammar_struct['start']
        for symbol in sorted(self._grammar_struct['rules'], key=lambda s: (s != start, s)):
            rule_struct = self._grammar_struct['rules'][symbol]  # type: Dict[Struct]
            assert rule_struct.keys() <= {'action', 'productions'}, rule_struct.keys() - {'actions', 'productions'}
            assert rule_struct['productions']
            action = rule_struct.get('action', None)
            if isinstance(action, str):
                pass
            elif hasattr(action, '__name__'):
                action = action.__name__
            else:
                action = None
            if action:
                lines.append('@' + action)
            lines.append(symbol + ':')
            for index, production_struct in enumerate(rule_struct['productions']):
                production_str_items = []
                for item in production_struct['production']:
                    if isinstance(item, str):
                        production_str_items.append(item)
                    else:
                        assert isinstance(item, dict)
                        item_str = item['symbol']
                        if 'mult' in item:
                            item_str += MULT_SYMBOLS[item['mult']]
                        item_modifiers = item.get('modifiers', None)
                        if item_modifiers:
                            item_str += '[%s]' % ', '.join(sorted(item_modifiers))
                        production_str_items.append(item_str)
                if production_struct.get('modifiers', None):
                    production_str_items.append('  {%s}' % ', '.join(production_struct['modifiers']))
                production_str = ' '.join(production_str_items)
                if len(rule_struct['productions']) == 1:
                    lines[-1] += ' ' + production_str
                elif not index:
                    lines.append('   ' + production_str)
                else:
                    lines.append(' | ' + production_str)
            lines[-1] += ';'
            for _ in range(rule_spacing):
                lines.append('')
        lines.append('')
        lines.append('terminals')
        lines.append('')
        for symbol in sorted(self._grammar_struct['terminals']):
            terminal_struct = self._grammar_struct['terminals'][symbol]  # type: Dict[Struct]
            action = terminal_struct.get('action', None)
            if isinstance(action, str):
                pass
            elif hasattr(action, '__name__'):
                action = action.__name__
            else:
                action = None
            if action:
                lines.append('@' + action)
            terminal_str_items = []
            recognizer = terminal_struct.get('recognizer', None)
            if isinstance(recognizer, str):
                # TODO: This gives me some concern. There should be a more reliable way to tell them apart. What if the
                #       user wants a string recognizer that matches something that starts and ends with slashes?
                if len(recognizer) > 1 and recognizer.startswith('/') and recognizer.endswith('/'):
                    terminal_str_items.append(recognizer)
                else:
                    terminal_str_items.append(repr(recognizer))
            if terminal_struct.get('modifiers', None):
                terminal_str_items.append('  {%s}' % ', '.join(terminal_struct['modifiers']))
            terminal_str = ' '.join(terminal_str_items)
            lines.append('%s: %s;' % (symbol, terminal_str))
            for _ in range(terminal_spacing):
                lines.append('')
        return '\n'.join(lines) + '\n'

    def get_struct(self) -> Struct:
        self.end()
        return deepcopy(self._grammar_struct)

    def start(self, symbol: str) -> 'GrammarBuilder':
        if 'start' in self._grammar_struct:
            raise GrammarBuilderValidationError("Start symbol is already set.")
        self._grammar_struct['start'] = symbol
        return self

    def rule(self, symbol: str) -> RuleBuilder:
        return RuleBuilder(self, self._grammar_struct, symbol)

    def terminal(self, symbol: str, recognizer: str = None) -> TerminalBuilder:
        terminal_builder = TerminalBuilder(self, self._grammar_struct, symbol)
        if recognizer is not None:
            terminal_builder.recognizer(recognizer)
        return terminal_builder

    def _apply(self) -> None:
        pass
