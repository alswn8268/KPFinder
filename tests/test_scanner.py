import os

from app.scanner import compute_hashes, find_duplicate_groups, scan_folder


def test_scan_folder_finds_all_files(tmp_path):
    (tmp_path / "a.txt").write_text("hello", encoding="utf-8")
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "b.txt").write_text("world", encoding="utf-8")
    (tmp_path / ".hidden.txt").write_text("skip me", encoding="utf-8")

    entries = scan_folder(str(tmp_path))
    names = {e.relative_path for e in entries}

    assert names == {"a.txt", os.path.join("sub", "b.txt")}


def test_find_duplicate_groups_matches_identical_content(tmp_path):
    (tmp_path / "one.txt").write_text("same content", encoding="utf-8")
    (tmp_path / "two.txt").write_text("same content", encoding="utf-8")
    (tmp_path / "different.txt").write_text("other content", encoding="utf-8")

    entries = scan_folder(str(tmp_path))
    compute_hashes(entries)
    groups = find_duplicate_groups(entries)

    assert len(groups) == 1
    group = next(iter(groups.values()))
    assert {e.name for e in group} == {"one.txt", "two.txt"}
