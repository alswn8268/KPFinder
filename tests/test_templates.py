from datetime import datetime

from app.scanner import FileEntry
from app.templates import (
    OrgTemplate,
    classify_by_rules,
    default_template,
    export_template,
    import_template,
    template_from_ai_proposal,
    template_from_current_structure,
    template_from_folder_list,
    template_from_hybrid_proposal,
)


def _entry(rel_path: str, summary: str = "") -> FileEntry:
    e = FileEntry(
        path=rel_path,
        relative_path=rel_path,
        name=rel_path.split("/")[-1],
        ext=".txt",
        size=10,
        modified=datetime.now(),
    )
    e.summary = summary
    e.summary_status = "ok" if summary else "pending"
    return e


def test_default_template_has_unclassified_folder():
    tmpl = default_template()
    assert "99_미분류" in tmpl.allowed_paths()


def test_classify_by_rules_matches_filename_keyword():
    entries = [_entry("2월_회의록.txt")]
    result = classify_by_rules(entries, default_template())
    assert result["2월_회의록.txt"]["dst"] == "08_회의록/2월_회의록.txt"
    assert result["2월_회의록.txt"]["confidence"] == "높음"


def test_classify_by_rules_skips_unmatched_files():
    entries = [_entry("이상한이름.txt")]
    result = classify_by_rules(entries, default_template())
    assert "이상한이름.txt" not in result


def test_classify_by_rules_matches_summary_keyword():
    entries = [_entry("문서1.txt", summary="이 문서는 계약서 검토 내용을 담고 있습니다.")]
    result = classify_by_rules(entries, default_template())
    assert result["문서1.txt"]["dst"] == "04_계약·법무/문서1.txt"


def test_classify_by_rules_org_rules_outrank_user_rules():
    """모듈 docstring이 명시하는 우선순위(조직 고정 규칙 -> 사용자 지정 규칙)를 지킨다 —
    같은 키워드를 서로 다른 폴더로 매핑하는 사용자 규칙이 있어도 조직 규칙이 이긴다."""
    entries = [_entry("2026_예산_보고서.txt")]
    user_rules = [{"keywords": ["예산"], "target": "99_미분류"}]

    result = classify_by_rules(entries, default_template(), user_rules=user_rules)

    assert result["2026_예산_보고서.txt"]["dst"] == "03_재무·회계/2026_예산_보고서.txt"


def test_export_import_roundtrip():
    tmpl = OrgTemplate(name="테스트 템플릿", folders=[{"path": "A", "description": ""}])
    text = export_template(tmpl)
    restored = import_template(text)
    assert restored.name == "테스트 템플릿"
    assert restored.allowed_paths() == ["A"]


def test_template_from_current_structure_uses_top_dirs():
    entries = [_entry("영업/보고서.txt"), _entry("법무/계약서.txt"), _entry("최상위.txt")]
    tmpl = template_from_current_structure(entries, name="현재 구조")
    assert set(tmpl.allowed_paths()) >= {"영업", "법무"}


def test_template_from_folder_list_parses_lines_and_ignores_comments():
    text = "01_경영지원\n# 이 줄은 무시\n\n영업/실적\n"
    tmpl = template_from_folder_list(text, name="내 템플릿")
    assert "01_경영지원" in tmpl.allowed_paths()
    assert "영업/실적" in tmpl.allowed_paths()
    assert "99_미분류" in tmpl.allowed_paths()


def test_template_from_folder_list_rejects_empty_input():
    import pytest

    with pytest.raises(ValueError):
        template_from_folder_list("   \n# 주석뿐\n", name="빈 템플릿")


def test_template_from_ai_proposal_dedupes_and_filters_empty():
    tmpl = template_from_ai_proposal(["영업", "", "영업", "마케팅", "  "], name="AI 제안")
    assert tmpl.allowed_paths() == ["영업", "마케팅", "99_미분류"]


def test_template_from_ai_proposal_keeps_existing_unclassified_folder_once():
    tmpl = template_from_ai_proposal(["영업", "99_미분류"], name="AI 제안")
    assert tmpl.allowed_paths().count("99_미분류") == 1


def test_template_from_ai_proposal_rejects_empty_categories():
    import pytest

    with pytest.raises(ValueError):
        template_from_ai_proposal([], name="빈 제안")

    with pytest.raises(ValueError):
        template_from_ai_proposal(["", "  "], name="빈 값뿐인 제안")


def _base_hybrid_template() -> OrgTemplate:
    return OrgTemplate(
        name="현재 템플릿",
        folders=[{"path": "01_경영지원", "description": "기존 설명"}, {"path": "99_미분류", "description": ""}],
        keyword_rules=[{"keywords": ["회의록"], "target": "01_경영지원"}],
    )


def test_template_from_hybrid_proposal_keeps_existing_folders_and_rules():
    base = _base_hybrid_template()
    tmpl = template_from_hybrid_proposal(base, ["영업"], name="갱신된 템플릿")

    assert tmpl.allowed_paths() == ["01_경영지원", "99_미분류", "영업"]
    assert tmpl.keyword_rules == base.keyword_rules
    # 기존 폴더의 설명이 손상되지 않아야 한다.
    assert tmpl.folders[0]["description"] == "기존 설명"
    assert tmpl.name == "갱신된 템플릿"


def test_template_from_hybrid_proposal_dedupes_against_existing_folders():
    base = _base_hybrid_template()
    tmpl = template_from_hybrid_proposal(base, ["01_경영지원", "영업", "영업"], name="갱신된 템플릿")

    assert tmpl.allowed_paths() == ["01_경영지원", "99_미분류", "영업"]


def test_template_from_hybrid_proposal_allows_empty_categories_without_error():
    """AI가 "지금 템플릿으로 충분하다"고 판단해 새 카테고리가 없으면, template_from_ai_proposal()
    과 달리 에러 없이 기존 템플릿과 같은 구성을 그대로 돌려줘야 한다."""
    base = _base_hybrid_template()
    tmpl = template_from_hybrid_proposal(base, [], name="변화 없음")

    assert tmpl.allowed_paths() == base.allowed_paths()
    assert tmpl.name == "변화 없음"


def test_template_from_hybrid_proposal_does_not_mutate_base_template():
    base = _base_hybrid_template()
    original_paths = base.allowed_paths()

    template_from_hybrid_proposal(base, ["영업"], name="갱신된 템플릿")

    assert base.allowed_paths() == original_paths
