from datetime import datetime

from app.scanner import FileEntry
from app.rename_tool import (
    MODE_FIND_REPLACE,
    MODE_NUMBERING,
    MODE_PREFIX,
    MODE_SUFFIX,
    build_rename_assignments,
    preview_rename,
)


def _entry(rel_path: str) -> FileEntry:
    return FileEntry(
        path=rel_path,
        relative_path=rel_path,
        name=rel_path.split("/")[-1],
        ext=".txt",
        size=10,
        modified=datetime.now(),
    )


def test_find_replace_changes_only_matching_files():
    entries = [_entry("영업/(1)보고서.txt"), _entry("계약서.txt")]
    rows = preview_rename(entries, {"mode": MODE_FIND_REPLACE, "find": "(1)", "replace": ""})
    by_src = {r["src"]: r for r in rows}

    assert by_src["영업/(1)보고서.txt"]["new_name"] == "보고서.txt"
    assert by_src["영업/(1)보고서.txt"]["changed"] is True
    assert by_src["계약서.txt"]["changed"] is False


def test_prefix_and_suffix_keep_extension():
    entries = [_entry("문서.txt")]
    prefixed = preview_rename(entries, {"mode": MODE_PREFIX, "text": "2026_"})
    suffixed = preview_rename(entries, {"mode": MODE_SUFFIX, "text": "_최종"})

    assert prefixed[0]["new_name"] == "2026_문서.txt"
    assert suffixed[0]["new_name"] == "문서_최종.txt"


def test_numbering_produces_sequential_names_in_path_order():
    entries = [_entry("b.txt"), _entry("a.txt")]
    rows = preview_rename(
        entries, {"mode": MODE_NUMBERING, "base_name": "문서", "start": 1, "digits": 2}
    )
    names_by_src = {r["src"]: r["new_name"] for r in rows}

    assert names_by_src["a.txt"] == "문서_01.txt"
    assert names_by_src["b.txt"] == "문서_02.txt"


def test_numbering_preserves_folder():
    entries = [_entry("영업/실적/report.txt")]
    rows = preview_rename(entries, {"mode": MODE_NUMBERING, "base_name": "문서", "start": 1, "digits": 2})
    assert rows[0]["dst"] == "영업/실적/문서_01.txt"


def test_build_rename_assignments_excludes_unchanged_files():
    entries = [_entry("영업/(1)보고서.txt"), _entry("계약서.txt")]
    assignments = build_rename_assignments(
        entries, {"mode": MODE_FIND_REPLACE, "find": "(1)", "replace": ""}
    )
    assert list(assignments.keys()) == ["영업/(1)보고서.txt"]
    assert assignments["영업/(1)보고서.txt"]["dst"] == "영업/보고서.txt"
    assert assignments["영업/(1)보고서.txt"]["source"] == "rename"
