from datetime import datetime

from app.scanner import FileEntry
from app.search import search_entries


def _entry(name, ext, summary=""):
    return FileEntry(
        path=name,
        relative_path=name,
        name=name,
        ext=ext,
        size=10,
        modified=datetime.now(),
        summary=summary,
    )


def test_search_by_name():
    entries = [_entry("영업보고서.txt", ".txt"), _entry("연차규정.txt", ".txt")]
    result = search_entries(entries, query="영업")
    assert [e.name for e in result] == ["영업보고서.txt"]


def test_search_by_summary_content():
    entries = [
        _entry("a.txt", ".txt", summary="매출 실적 보고서"),
        _entry("b.txt", ".txt", summary="연차 사용 규정 안내"),
    ]
    result = search_entries(entries, query="매출")
    assert [e.name for e in result] == ["a.txt"]


def test_search_filters_by_extension():
    entries = [_entry("a.docx", ".docx"), _entry("b.txt", ".txt")]
    result = search_entries(entries, extensions=[".docx"])
    assert [e.name for e in result] == ["a.docx"]


def test_search_empty_query_returns_all():
    entries = [_entry("a.txt", ".txt"), _entry("b.txt", ".txt")]
    assert search_entries(entries) == entries
