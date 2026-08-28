import os

import pytest

import app.file_ops as file_ops
from app.file_ops import apply_move_plan, build_move_plan, undo_move_plan


@pytest.fixture(autouse=True)
def isolated_cache_dir(tmp_path, monkeypatch):
    cache_dir = tmp_path / "_cache"
    monkeypatch.setattr(file_ops, "CACHE_DIR", str(cache_dir))


def test_build_move_plan_skips_noop_moves(tmp_path):
    plan = build_move_plan(str(tmp_path), {"a.txt": "a.txt", "b.txt": "폴더/b.txt"})
    assert len(plan) == 1
    assert plan[0]["rel_src"] == "b.txt"
    assert plan[0]["rel_dst"] == os.path.join("폴더", "b.txt")


def test_apply_and_undo_move_plan(tmp_path):
    (tmp_path / "b.txt").write_text("content", encoding="utf-8")
    plan = build_move_plan(str(tmp_path), {"b.txt": "폴더/b.txt"})

    log_path = apply_move_plan(plan)
    moved_path = tmp_path / "폴더" / "b.txt"
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

    plan = build_move_plan(str(tmp_path), {"src.txt": "폴더/src.txt"})
    log_path = apply_move_plan(plan)

    assert (dest_dir / "src.txt").read_text(encoding="utf-8") == "existing"
    assert (dest_dir / "src_1.txt").read_text(encoding="utf-8") == "new"

