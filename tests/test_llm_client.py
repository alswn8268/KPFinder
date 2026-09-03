from app.llm_client import normalize_assignments


def test_normalize_assignments_handles_dict_form():
    raw = {"a.txt": {"dst": "보고서/a.txt", "reason": "영업 실적 문서", "confidence": "높음"}}
    result = normalize_assignments(raw)
    assert result["a.txt"] == {
        "dst": "보고서/a.txt",
        "reason": "영업 실적 문서",
        "confidence": "높음",
        "source": "ai",
    }


def test_normalize_assignments_handles_legacy_string_form():
    raw = {"a.txt": "보고서/a.txt"}
    result = normalize_assignments(raw)
    assert result["a.txt"]["dst"] == "보고서/a.txt"
    assert result["a.txt"]["confidence"] == "보통"


def test_normalize_assignments_defaults_invalid_confidence():
    raw = {"a.txt": {"dst": "보고서/a.txt", "confidence": "알수없음"}}
    result = normalize_assignments(raw)
    assert result["a.txt"]["confidence"] == "보통"


def test_normalize_assignments_skips_unusable_values():
    raw = {"a.txt": 12345}
    assert normalize_assignments(raw) == {}
