import pytest  # noqa
import subprocess
import os

CURRENT_DIR = os.path.abspath(os.path.dirname(__file__))
GRAMMAR_FILE = os.path.join(CURRENT_DIR, 'grammar.pg')


@pytest.mark.skipif("TRAVIS" in os.environ
                    and os.environ["TRAVIS"] == "true",
                    reason="Test fails under TRAVIS")
def test_pglr_check():
    """
    Test pglr command for grammar checking.
    """
    result = subprocess.call(['pglr', 'compile', GRAMMAR_FILE])
    assert result == 0


@pytest.mark.skipif("TRAVIS" in os.environ
                    and os.environ["TRAVIS"] == "true",
                    reason="Test fails under TRAVIS")
def test_pglr_viz():
    """
    Test pglr command for PDA visualization.
    """
    DOT_FILE = os.path.join(CURRENT_DIR, '{}.dot'.format(GRAMMAR_FILE))
    try:
        os.remove(DOT_FILE)
    except Exception:
        pass
    assert not os.path.exists(DOT_FILE)
    result = subprocess.call(['pglr', '--no-colors', 'viz', GRAMMAR_FILE])
    assert result == 0
    assert os.path.exists(DOT_FILE)
    assert 'digraph grammar' in open(DOT_FILE, 'r').read()
