"""
A support for token recognizers.
Recognizers are callables capable of recognizing low-level patterns
(a.k.a tokens) in the input.
"""
import re
from parglare.exceptions import GrammarError


class Recognizers(object):
    """
    Base class for grammar recognizers.

    Methods of this class are used to recognize tokens in the input stream.
    """
    def __init__(self):
        self.recognizers = {}

    def add_recognizer(self, name, recognizer):
        """
        Dynamically register a new recognizer.
        """
        self.recognizers[name] = recognizer

    def __getattr__(self, name):
        """
        If regular recognizer method is not found search into dynamically
        registered recognizers.
        """
        r = self.recognizers.get(name, None)
        if r:
            return r
        raise AttributeError

    def __contains__(self, name):
        try:
            getattr(self, name)
        except AttributeError:
            return False
        return True

    def EMPTY(self, input, pos):
        pass

    def EOF(self, input, pos):
        pass

    def STOP(self, input, pos):
        pass


class Recognizer(object):
    """
    Base class for a recognizer.

    Recognizers are callables capable of recognizing low-level patterns
    (a.k.a tokens) in the input.
    """
    def __init__(self, name, location=None):
        self.name = name
        self.location = location


class StringRecognizer(Recognizer):
    """
    String recognizer will recognize the given literal string in the input
    string.
    """
    def __init__(self, value, ignore_case=False, **kwargs):
        super(StringRecognizer, self).__init__(value, **kwargs)
        self.value = value
        self.ignore_case = ignore_case
        self.value_cmp = value.lower() if ignore_case else value

    def __call__(self, in_str, pos):
        if self.ignore_case:
            if in_str[pos:pos+len(self.value)].lower() == self.value_cmp:
                return self.value
        else:
            if in_str[pos:pos+len(self.value)] == self.value_cmp:
                return self.value


def esc_control_characters(regex):
    """
    Escape control characters in regular expressions.
    """
    unescapes = [('\a', r'\a'), ('\b', r'\b'), ('\f', r'\f'), ('\n', r'\n'),
                 ('\r', r'\r'), ('\t', r'\t'), ('\v', r'\v')]
    for val, text in unescapes:
        regex = regex.replace(val, text)
    return regex


class RegExRecognizer(Recognizer):
    """
    Regular expression recognizer will recognize given regular expression in
    the input string.
    """
    def __init__(self, regex, name=None, re_flags=re.MULTILINE,
                 ignore_case=False, **kwargs):
        if name is None:
            name = regex
        super(RegExRecognizer, self).__init__(name, kwargs)
        self._regex = regex
        self.ignore_case = ignore_case
        if ignore_case:
            re_flags |= re.IGNORECASE
        self.re_flags = re_flags
        try:
            self.regex = re.compile(self._regex, re_flags)
        except re.error as ex:
            regex = esc_control_characters(self._regex)
            message = 'Regex compile error in /{}/ (report: "{}")'
            raise GrammarError(message.format(regex, str(ex)))

    def __call__(self, in_str, pos):
        m = self.regex.match(in_str, pos)
        if m and m.group():
            return m.group()
