from datetime import datetime

from app.relatedness import build_relatedness_edges, score_pair
from app.scanner import FileEntry


def _entry(rel_path, summary="", status="pending", file_hash=""):
    e = FileEntry(
        path=rel_path,
        relative_path=rel_path,
        name=rel_path,
        ext=".txt",
        size=10,
        modified=datetime.now(),
        file_hash=file_hash,
    )
    e.summary = summary
    e.summary_status = status
    return e


def test_score_pair_uses_name_only_without_summaries():
    a = _entry("보고서.txt")
    b = _entry("보고서_사본.txt")
    score = score_pair(a, b)
    assert 0 < score <= 1


def test_score_pair_weighs_summary_when_both_ok():
    a = _entry("동일파일명.txt", summary="동일한 내용의 문서", status="ok")
    b = _entry("동일파일명.txt", summary="동일한 내용의 문서", status="ok")
    assert score_pair(a, b) == 1.0


def test_build_relatedness_edges_excludes_exact_duplicates_by_default():
    a = _entry("a.txt", file_hash="same")
    b = _entry("b.txt", file_hash="same")
    assert build_relatedness_edges([a, b], min_score=0.0) == []


def test_build_relatedness_edges_respects_min_score():
    a = _entry("완전히다른이름1.txt")
    b = _entry("완전히다른이름2.txt")
    high = build_relatedness_edges([a, b], min_score=0.99)
    low = build_relatedness_edges([a, b], min_score=0.0)
    assert high == []
    assert len(low) == 1
