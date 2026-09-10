import pytest

import app.organizer as organizer
import app.version_history as version_history


@pytest.fixture(autouse=True)
def isolated_cache_dir(tmp_path, monkeypatch):
    cache_dir = tmp_path / "_cache"
    monkeypatch.setattr(organizer, "CACHE_DIR", str(cache_dir))
    monkeypatch.setattr(version_history, "CACHE_DIR", str(cache_dir))


def test_list_versions_empty_when_none_recorded(tmp_path):
    root = str(tmp_path / "some_folder")
    assert version_history.list_versions(root) == []


def test_record_version_appends_with_incrementing_id(tmp_path):
    root = str(tmp_path / "some_folder")
    v1 = version_history.record_version(root, "log1.json", note="1차 정리", files_moved=3)
    v2 = version_history.record_version(root, "log2.json", note="2차 정리", files_moved=5)

    versions = version_history.list_versions(root)
    assert [v["version_id"] for v in versions] == ["v1", "v2"]
    assert v1["restored"] is False
    assert v2["files_moved"] == 5


def test_mark_restored_updates_only_target_version(tmp_path):
    root = str(tmp_path / "some_folder")
    version_history.record_version(root, "log1.json", note="", files_moved=1)
    version_history.record_version(root, "log2.json", note="", files_moved=2)

    version_history.mark_restored(root, "v1")
    versions = version_history.list_versions(root)

    restored = {v["version_id"]: v["restored"] for v in versions}
    assert restored == {"v1": True, "v2": False}


def test_can_restore_blocked_when_later_version_unrestored(tmp_path):
    root = str(tmp_path / "some_folder")
    version_history.record_version(root, "log1.json", note="", files_moved=1)
    version_history.record_version(root, "log2.json", note="", files_moved=2)

    allowed, reason = version_history.can_restore(root, "v1")

    assert allowed is False
    assert reason


def test_can_restore_allowed_for_most_recent_unrestored(tmp_path):
    root = str(tmp_path / "some_folder")
    version_history.record_version(root, "log1.json", note="", files_moved=1)
    version_history.record_version(root, "log2.json", note="", files_moved=2)

    allowed, reason = version_history.can_restore(root, "v2")

    assert allowed is True
    assert reason == ""


def test_record_version_does_not_persist_zero_move_version(tmp_path):
    """옮긴 파일이 0개인 적용(예: 계획한 파일이 모두 이후에 변경/삭제돼 스킵된 경우)은
    버전 이력에 남지 않아야 한다 — 그렇지 않으면 이 "빈 버전"이 최신 버전으로 남아,
    실제로 파일을 옮긴 그 이전 버전을 되돌리지 못하게 영구히 막아버린다(회귀 방지)."""
    root = str(tmp_path / "some_folder")
    version_history.record_version(root, "log1.json", note="1차 정리", files_moved=3)
    version_history.record_version(root, "log2.json", note="빈 적용", files_moved=0)

    versions = version_history.list_versions(root)
    assert [v["version_id"] for v in versions] == ["v1"]

    allowed, reason = version_history.can_restore(root, "v1")
    assert allowed is True
    assert reason == ""
