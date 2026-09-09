from datetime import datetime

from app import llm_client
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


def test_classify_entries_with_ai_skips_ollama_call_when_all_rule_matched(monkeypatch):
    """규칙만으로 모든 파일이 분류되면(use_ai=True라도) 실제로 Ollama를 호출하지 않아야 한다 —
    이 세션에서 발견된 "AI 분류가 너무 오래 걸린다"는 문제의 근본 원인은 규칙으로 이미 확실한
    파일까지 전부 AI로 요약하던 것이었다. 회귀 방지용 테스트."""

    def fail_if_called(*args, **kwargs):
        raise AssertionError("규칙으로 전부 분류됐는데 Ollama가 호출되었습니다")

    monkeypatch.setattr(llm_client, "propose_folder_structure", fail_if_called)

    entries = [_entry("주간회의록.txt"), _entry("계약서_초안.txt")]
    result = classify_entries(entries, default_template(), model="unused", use_ai=True)

    assert result["assignments"]["주간회의록.txt"]["source"] == "rule"
    assert result["assignments"]["계약서_초안.txt"]["source"] == "rule"
    assert "AI 호출이 필요하지 않았습니다" in result["notes"]


def test_classify_entries_rejects_ai_folder_outside_template(monkeypatch):
    """templates.py 모듈 docstring/설계상 "AI가 매번 다른 이름의 폴더를 만들어내는 것을
    막기 위해"가 핵심 원칙인데, propose_folder_structure에는 allowed_folders가 프롬프트
    힌트로만 전달되고 실제로 강제되지 않는다. classify_entries가 응답을 직접 걸러야 한다."""

    def fake_propose(*args, **kwargs):
        return {
            "categories": ["AI가_지어낸_폴더"],
            "assignments": {
                "이상한파일.txt": {
                    "dst": "AI가_지어낸_폴더/이상한파일.txt",
                    "reason": "AI 임의 판단",
                    "confidence": "높음",
                }
            },
            "notes": "",
        }

    monkeypatch.setattr(llm_client, "propose_folder_structure", fake_propose)

    entry = _entry("이상한파일.txt")
    entry.summary_status = "ok"
    result = classify_entries([entry], default_template(), model="unused", use_ai=True)

    dst = result["assignments"]["이상한파일.txt"]["dst"]
    assert not dst.startswith("AI가_지어낸_폴더")
    assert dst.startswith("99_미분류")
    assert result["assignments"]["이상한파일.txt"]["source"] == "fallback"
