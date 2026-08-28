from datetime import datetime

from app.organizer import validate_assignments
from app.scanner import FileEntry
from app.similar import find_similar_documents


def _entry(rel_path: str, summary: str = "", file_hash: str = "") -> FileEntry:
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
    e.summary_status = "ok" if summary else "pending"
    return e


def test_find_similar_documents_flags_near_duplicate_versions():
    a = _entry("1분기_보고서_v1.txt", "1분기 영업 실적 보고서. 매출 12% 증가.", file_hash="h1")
    b = _entry("1분기_보고서_v2_final.txt", "1분기 영업 실적 보고서. 매출 12% 증가, 거래처 수정.", file_hash="h2")
    c = _entry("전혀_다른_문서.txt", "연차 휴가 신청 절차 안내.", file_hash="h3")

    results = find_similar_documents([a, b, c])
    pairs = {(r[0].relative_path, r[1].relative_path) for r in results}

    assert (a.relative_path, b.relative_path) in pairs
    assert not any(c.relative_path in pair for pair in pairs)


def test_find_similar_documents_skips_exact_duplicates():
    a = _entry("a.txt", "동일 문서 내용입니다.", file_hash="same")
    b = _entry("b.txt", "동일 문서 내용입니다.", file_hash="same")

    assert find_similar_documents([a, b]) == []


def test_validate_assignments_drops_unknown_or_empty_targets():
    entries = [_entry("a.txt"), _entry("b.txt")]
    assignments = {
        "a.txt": "보고서/a.txt",
        "존재하지않는파일.txt": "보고서/x.txt",
        "b.txt": "",
    }

    result = validate_assignments(entries, assignments)

    assert result == {"a.txt": "보고서/a.txt"}
