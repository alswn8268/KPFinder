from datetime import datetime

from app.scanner import FileEntry
from app.templates import (
    OrgTemplate,
    classify_by_rules,
    default_template,
    export_template,
    import_template,
    template_from_current_structure,
    template_from_folder_list,
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
