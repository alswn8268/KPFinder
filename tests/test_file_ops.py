import json
import os

import pytest

import app.file_ops as file_ops
from app.file_ops import apply_move_plan, build_move_plan, list_move_logs, undo_move_plan
from app.scanner import compute_hashes, scan_folder


@pytest.fixture(autouse=True)
def isolated_cache_dir(tmp_path, monkeypatch):
    cache_dir = tmp_path / "_cache"
    monkeypatch.setattr(file_ops, "CACHE_DIR", str(cache_dir))


def _scanned_entries(root):
    entries = scan_folder(root)
    compute_hashes(entries)
    return entries


def _read_events(log_path):
    with open(log_path, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def test_build_move_plan_skips_noop_moves(tmp_path):
    plan = build_move_plan(str(tmp_path), {"a.txt": "a.txt", "b.txt": "폴더/b.txt"})
    assert len(plan) == 1
    assert plan[0]["rel_src"] == "b.txt"
    assert plan[0]["rel_dst"] == "폴더/b.txt"  # build_move_plan은 구분자를 정규화하지 않는다


def test_build_move_plan_rejects_unsafe_destinations(tmp_path):
    plan = build_move_plan(
        str(tmp_path),
        {"a.txt": "../outside.txt", "b.txt": "C:/other/b.txt", "c.txt": "정상/c.txt"},
    )
    assert [p["rel_src"] for p in plan] == ["c.txt"]


def test_apply_and_undo_move_plan(tmp_path):
    (tmp_path / "b.txt").write_text("content", encoding="utf-8")
    entries = _scanned_entries(str(tmp_path))
    plan = build_move_plan(str(tmp_path), {"b.txt": "폴더/b.txt"})

    log_path, moved_count = apply_move_plan(plan, entries)
    moved_path = tmp_path / "폴더" / "b.txt"
    assert moved_count == 1
    assert moved_path.exists()
    assert not (tmp_path / "b.txt").exists()

    restored = undo_move_plan(log_path)
    assert restored == 1
    assert (tmp_path / "b.txt").exists()
    assert not moved_path.exists()


def test_apply_move_plan_avoids_overwriting_existing_file(tmp_path):
    (tmp_path / "src.txt").write_text("new", encoding="utf-8")
    dest_dir = tmp_path / "폴더"
    dest_dir.mkdir()
    (dest_dir / "src.txt").write_text("existing", encoding="utf-8")

    entries = _scanned_entries(str(tmp_path))
    plan = build_move_plan(str(tmp_path), {"src.txt": "폴더/src.txt"})
    log_path, moved_count = apply_move_plan(plan, entries)

    assert moved_count == 1
    assert (dest_dir / "src.txt").read_text(encoding="utf-8") == "existing"
    assert (dest_dir / "src_1.txt").read_text(encoding="utf-8") == "new"


def test_plan_is_saved_before_any_move_happens(tmp_path):
    (tmp_path / "a.txt").write_text("content", encoding="utf-8")
    entries = _scanned_entries(str(tmp_path))
    plan = build_move_plan(str(tmp_path), {"a.txt": "폴더/a.txt"})

    log_path = file_ops.save_plan(plan, {e.relative_path: e.file_hash for e in entries})

    assert (tmp_path / "a.txt").exists()  # 아직 이동 전
    events = _read_events(log_path)
    assert events[0]["event"] == "planned"
    assert events[0]["rel_src"] == "a.txt"


def test_move_is_logged_immediately_per_file(tmp_path):
    (tmp_path / "a.txt").write_text("a", encoding="utf-8")
    (tmp_path / "b.txt").write_text("b", encoding="utf-8")
    entries = _scanned_entries(str(tmp_path))
    plan = build_move_plan(str(tmp_path), {"a.txt": "폴더/a.txt", "b.txt": "폴더/b.txt"})

    log_path, moved_count = apply_move_plan(plan, entries)

    events = _read_events(log_path)
    move_ok_events = [e for e in events if e["event"] == "move_ok"]
    assert moved_count == 2
    assert len(move_ok_events) == 2


def test_rollback_on_mid_batch_failure(tmp_path, monkeypatch):
    (tmp_path / "a.txt").write_text("a", encoding="utf-8")
    (tmp_path / "b.txt").write_text("b", encoding="utf-8")
    entries = _scanned_entries(str(tmp_path))
    plan = build_move_plan(str(tmp_path), {"a.txt": "폴더/a.txt", "b.txt": "폴더/b.txt"})

    import shutil

    real_move = shutil.move
    calls = {"n": 0}

    def flaky_move(src, dst):
        calls["n"] += 1
        if calls["n"] == 2:
            raise OSError("simulated failure")
        return real_move(src, dst)

    monkeypatch.setattr(file_ops.shutil, "move", flaky_move)

    log_path, moved_count = apply_move_plan(plan, entries)

    assert moved_count == 0
    assert (tmp_path / "a.txt").exists()
    assert (tmp_path / "b.txt").exists()
    assert not (tmp_path / "폴더").exists() or not any(
        (tmp_path / "폴더").iterdir()
    )
    events = _read_events(log_path)
    assert any(e["event"] == "move_failed" for e in events)
    assert any(e["event"] == "rollback_ok" for e in events)


def test_skips_source_changed_since_scan(tmp_path):
    (tmp_path / "a.txt").write_text("original", encoding="utf-8")
    entries = _scanned_entries(str(tmp_path))
    # 스캔 이후 파일 내용이 바뀜
    (tmp_path / "a.txt").write_text("changed after scan", encoding="utf-8")

    plan = build_move_plan(str(tmp_path), {"a.txt": "폴더/a.txt"})
    log_path, moved_count = apply_move_plan(plan, entries)

    assert moved_count == 0
    assert (tmp_path / "a.txt").exists()
    events = _read_events(log_path)
    assert any(e["event"] == "skipped_changed" for e in events)


def test_list_move_logs_returns_jsonl_files(tmp_path):
    (tmp_path / "a.txt").write_text("a", encoding="utf-8")
    entries = _scanned_entries(str(tmp_path))
    plan = build_move_plan(str(tmp_path), {"a.txt": "폴더/a.txt"})
    log_path, _ = apply_move_plan(plan, entries)

    logs = list_move_logs()
    assert log_path in logs
    assert all(p.endswith(".jsonl") for p in logs)
