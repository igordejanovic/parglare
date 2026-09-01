import json
import os
from pathlib import Path

import pytest

from parglare import Grammar, Parser, TableCacheError

_GRAMMAR_A = """
S: 'a';
"""
_GRAMMAR_B = """
S: 'b' | 'c';
"""


def _write_grammar(path: Path, contents: str) -> None:
    path.write_text(contents, encoding="utf-8")


def test_rebuilds_cache_after_branch_switch_with_misleading_mtime(tmp_path: Path):
    grammar_path = tmp_path / "grammar.pg"
    cache_path = tmp_path / "grammar.pgc"

    _write_grammar(grammar_path, _GRAMMAR_A)
    assert Parser(Grammar.from_file(str(grammar_path))).parse("a") == "a"

    _write_grammar(grammar_path, _GRAMMAR_B)
    assert Parser(Grammar.from_file(str(grammar_path))).parse("b") == "b"
    cache_mtime = cache_path.stat().st_mtime_ns

    _write_grammar(grammar_path, _GRAMMAR_A)
    os.utime(grammar_path, ns=(cache_mtime - 1, cache_mtime - 1))

    assert Parser(Grammar.from_file(str(grammar_path))).parse("a") == "a"


def test_corrupt_cache_is_rebuilt_in_normal_mode(tmp_path: Path):
    grammar_path = tmp_path / "grammar.pg"
    _write_grammar(grammar_path, _GRAMMAR_A)
    cache_path = tmp_path / "grammar.pgc"
    cache_path.write_text("{not json", encoding="utf-8")

    assert Parser(Grammar.from_file(str(grammar_path))).parse("a") == "a"
    assert isinstance(json.loads(cache_path.read_text(encoding="utf-8")), dict)


def test_force_load_rejects_incompatible_cache(tmp_path: Path):
    grammar_path = tmp_path / "grammar.pg"
    _write_grammar(grammar_path, _GRAMMAR_A)
    Parser(Grammar.from_file(str(grammar_path)))

    _write_grammar(grammar_path, _GRAMMAR_B)
    with pytest.raises(TableCacheError, match="different grammar"):
        Parser(Grammar.from_file(str(grammar_path)), force_load_table=True)


def test_explicit_cache_path_keeps_generated_file_out_of_grammar_directory(
    tmp_path: Path,
):
    grammar_path = tmp_path / "grammar.pg"
    cache_path = tmp_path / "cache" / "table.pgc"
    cache_path.parent.mkdir()
    _write_grammar(grammar_path, _GRAMMAR_A)

    parser = Parser(Grammar.from_file(str(grammar_path)), table_cache=cache_path)
    assert parser.parse("a") == "a"
    assert cache_path.exists()
    assert not grammar_path.with_suffix(".pgc").exists()


def test_false_cache_path_never_reads_or_writes_a_cache(tmp_path: Path):
    grammar_path = tmp_path / "grammar.pg"
    _write_grammar(grammar_path, _GRAMMAR_A)

    parser = Parser(Grammar.from_file(str(grammar_path)), table_cache=False)
    assert parser.parse("a") == "a"
    assert not grammar_path.with_suffix(".pgc").exists()
