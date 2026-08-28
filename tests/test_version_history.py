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
