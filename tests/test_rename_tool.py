from datetime import datetime

from app.scanner import FileEntry
from app.rename_tool import (
    MODE_FIND_REPLACE,
    MODE_NUMBERING,
    MODE_PREFIX,
    MODE_SUFFIX,
    build_rename_assignments,
    build_suggested_rename_assignments,
    preview_rename,
    suggest_clean_names,
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


def test_suggest_clean_names_strips_copy_artifacts():
    entries = [
        _entry("사업자등록증_요청양식(1).txt"),
        _entry("보고서_복사본.txt"),
        _entry("보고서_사본.txt"),
        _entry("계약서.txt"),
    ]
    suggestions = suggest_clean_names(entries)

    assert suggestions["사업자등록증_요청양식(1).txt"] == "사업자등록증_요청양식.txt"
    assert suggestions["보고서_복사본.txt"] == "보고서.txt"
    # "계약서.txt"는 지울 게 없으니 제안에 아예 포함되지 않는다.
    assert "계약서.txt" not in suggestions


def test_suggest_clean_names_preserves_meaningful_version_markers():
    """"_v2"/"_final"/"_초안"처럼 서로 다른 문서를 구분하는 표시는 지우지 않는다 —
    지우면 서로 다른 파일이 같은 이름이 되어버린다."""
    entries = [_entry("제안서_v2.txt"), _entry("제안서_초안.txt")]
    suggestions = suggest_clean_names(entries)
    assert suggestions == {}


def test_suggest_clean_names_skips_when_result_would_collide():
    """정리 후 이름이 같은 폴더의 다른 파일(원본이든 다른 제안이든)과 겹치면 건드리지
    않는다 — 서로 다른 문서가 뒤섞이지 않도록."""
    entries = [
        _entry("보고서_복사본.txt"),
        _entry("보고서_사본.txt"),
        _entry("보고서.txt"),
    ]
    suggestions = suggest_clean_names(entries)

    # "보고서.txt"가 이미 있으므로 "보고서_복사본.txt"는 정리해도 이름이 겹쳐 제외된다.
    assert "보고서_복사본.txt" not in suggestions
    assert "보고서_사본.txt" not in suggestions


def test_build_suggested_rename_assignments_shape():
    entries = [_entry("영업/보고서_복사본.txt")]
    assignments = build_suggested_rename_assignments(entries)

    assert assignments["영업/보고서_복사본.txt"]["dst"] == "영업/보고서.txt"
    assert assignments["영업/보고서_복사본.txt"]["source"] == "rename_suggest"
