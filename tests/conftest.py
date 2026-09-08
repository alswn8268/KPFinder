"""api/ 엔드포인트 테스트에서 공용으로 쓰는 fixture.

기존 tests/test_file_ops.py, test_version_history.py 등이 각자 파일 안에서 정의해 온
`isolated_cache_dir` 패턴을 그대로 따르되, api 테스트 여러 파일에서 반복하지 않도록
conftest로 옮겼다. 같은 이름의 fixture를 개별 테스트 모듈이 다시 정의하면 그쪽이
우선하므로 기존 테스트 동작에는 영향이 없다.
"""

import pytest
from fastapi.testclient import TestClient

from app import file_ops, organizer, templates, version_history
from api.main import app


@pytest.fixture(autouse=True)
def isolated_cache_dir(tmp_path, monkeypatch):
    cache_dir = tmp_path / "_cache"
    monkeypatch.setattr(organizer, "CACHE_DIR", str(cache_dir))
    monkeypatch.setattr(file_ops, "CACHE_DIR", str(cache_dir))
    monkeypatch.setattr(version_history, "CACHE_DIR", str(cache_dir))
    monkeypatch.setattr(templates, "CACHE_DIR", str(cache_dir))
    monkeypatch.setattr(templates, "TEMPLATE_DIR", str(cache_dir / "templates"))


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def sample_folder(tmp_path):
    root = tmp_path / "sample"
    root.mkdir()
    (root / "회의록_0212.txt").write_text("2월 12일 마케팅팀 회의록입니다.", encoding="utf-8")
    (root / "계약서_초안.txt").write_text("신규 협력사와의 계약서 초안입니다.", encoding="utf-8")
    (root / "이상한파일.txt").write_text("분류하기 애매한 내용입니다.", encoding="utf-8")
    return str(root)
