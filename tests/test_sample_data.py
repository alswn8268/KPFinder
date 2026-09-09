import os

import pytest

from app.scanner import scan_folder
from app.templates import classify_by_rules
from sample_data.generate_sample_data import DATASETS, generate, list_datasets
from sample_data.org_templates import SAMPLE_TEMPLATES


def test_list_datasets_matches_registry():
    listed = list_datasets()
    assert {d["key"] for d in listed} == set(DATASETS.keys())
    for d in listed:
        assert d["label"]
        assert d["output_dir"]


@pytest.mark.parametrize("dataset_key", list(DATASETS.keys()))
def test_generate_creates_expected_file_count(tmp_path, dataset_key):
    out_dir = str(tmp_path / dataset_key)
    spec = DATASETS[dataset_key]
    created = generate(out_dir, dataset=dataset_key)
    expected = len(spec["docs"]) + len(spec["duplicates"]["targets"])
    assert created == expected
    entries = scan_folder(out_dir)
    assert len(entries) == expected


def test_generate_rejects_unknown_dataset(tmp_path):
    with pytest.raises(ValueError):
        generate(str(tmp_path / "x"), dataset="no_such_team")


def test_generate_default_dataset_is_general_office_and_backward_compatible(tmp_path):
    out_dir = str(tmp_path / "legacy_call")
    # 기존 호출부(streamlit_app.py, api/routers/sample_data.py)는 dataset 키워드 없이
    # generate(output_dir, force=...) 형태로 호출한다 — 이 형태가 계속 동작해야 한다.
    created = generate(out_dir, force=True)
    assert created == len(DATASETS["general_office"]["docs"]) + len(
        DATASETS["general_office"]["duplicates"]["targets"]
    )


def test_generate_does_not_overwrite_existing_without_force(tmp_path):
    out_dir = str(tmp_path / "existing")
    os.makedirs(out_dir)
    marker = os.path.join(out_dir, "건드리면_안됨.txt")
    with open(marker, "w", encoding="utf-8") as f:
        f.write("x")

    created = generate(out_dir, dataset="ops_team")

    assert created == 0
    assert os.path.exists(marker)


@pytest.mark.parametrize("dataset_key", ["dev_team", "ops_team", "finance_team"])
def test_department_dataset_mostly_classifies_with_matching_sample_template(tmp_path, dataset_key):
    """각 부서 샘플 데이터셋의 파일명은 같은 부서 샘플 템플릿의 키워드 규칙과 맞춰
    설계되어 있다 — Ollama 없이 규칙 기반만으로도 대부분 자동 분류되는 것이 데모의
    핵심이므로, 이 매칭이 깨지지 않는지 회귀 테스트로 고정해 둔다."""
    out_dir = str(tmp_path / dataset_key)
    generate(out_dir, dataset=dataset_key)
    entries = scan_folder(out_dir)
    template = SAMPLE_TEMPLATES[dataset_key]["template"]

    result = classify_by_rules(entries, template)

    matched_ratio = len(result) / len(entries)
    assert matched_ratio >= 0.6, f"{dataset_key}: 규칙 매칭 비율이 너무 낮습니다 ({matched_ratio:.0%})"

    allowed = set(template.allowed_paths())
    for info in result.values():
        folder = info["dst"].rsplit("/", 1)[0]
        assert folder in allowed


def test_sample_templates_are_distinct_and_well_formed():
    assert len(SAMPLE_TEMPLATES) == 3
    names = {entry["template"].name for entry in SAMPLE_TEMPLATES.values()}
    assert len(names) == 3  # 이름이 서로 겹치지 않아야 함

    for entry in SAMPLE_TEMPLATES.values():
        template = entry["template"]
        assert entry["label"]
        assert entry["description"]
        paths = [f["path"] for f in template.folders]
        assert len(paths) == len(set(paths))  # 폴더 경로 중복 없음
        assert "99_미분류" in paths
        for rule in template.keyword_rules:
            assert rule["keywords"]
            assert rule["target"] in paths
