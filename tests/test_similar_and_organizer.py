from datetime import datetime

from app.organizer import classify_entries, validate_assignments
from app.scanner import FileEntry
from app.similar import find_similar_documents
from app.templates import default_template


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


def test_validate_assignments_drops_unknown_or_empty_targets(tmp_path):
    entries = [_entry("a.txt"), _entry("b.txt")]
    assignments = {
        "a.txt": "보고서/a.txt",
        "존재하지않는파일.txt": "보고서/x.txt",
        "b.txt": "",
    }

    valid, rejected = validate_assignments(entries, assignments, str(tmp_path))

    assert valid.keys() == {"a.txt"}
    assert valid["a.txt"]["dst"] == "보고서/a.txt"
    assert {r["src"] for r in rejected} == {"존재하지않는파일.txt", "b.txt"}


def test_validate_assignments_rejects_path_traversal(tmp_path):
    entries = [_entry("a.txt")]
    valid, rejected = validate_assignments(
        entries, {"a.txt": "../outside.txt"}, str(tmp_path)
    )
    assert valid == {}
    assert rejected[0]["src"] == "a.txt"


def test_validate_assignments_rejects_absolute_destination(tmp_path):
    entries = [_entry("a.txt")]
    valid, rejected = validate_assignments(
        entries, {"a.txt": "C:/other/a.txt"}, str(tmp_path)
    )
    assert valid == {}
    assert len(rejected) == 1


def test_validate_assignments_rejects_reserved_name(tmp_path):
    entries = [_entry("a.txt")]
    valid, rejected = validate_assignments(
        entries, {"a.txt": "폴더/CON.txt"}, str(tmp_path)
    )
    assert valid == {}
    assert len(rejected) == 1


def test_validate_assignments_rejects_case_insensitive_collision(tmp_path):
    entries = [_entry("a.txt"), _entry("b.txt")]
    valid, rejected = validate_assignments(
        entries,
        {"a.txt": "보고서/Report.txt", "b.txt": "보고서/report.txt"},
        str(tmp_path),
    )
    assert len(valid) == 1
    assert len(rejected) == 1


def test_classify_entries_without_ai_uses_rules_only():
    entries = [_entry("주간회의록.txt"), _entry("이상한파일.txt")]
    result = classify_entries(entries, default_template(), model="unused", use_ai=False)

    assert "주간회의록.txt" in result["assignments"]
    assert result["assignments"]["주간회의록.txt"]["source"] == "rule"
    # AI가 꺼져 있으면 규칙에 안 걸린 pending 상태 파일은 미분류로도 강제 배정하지 않는다.
    assert "이상한파일.txt" not in result["assignments"]
