import os
from datetime import datetime

from app.scanner import FileEntry
from app.structure_copy import copy_structure_only, list_folder_paths


def _entry(rel_path: str) -> FileEntry:
    return FileEntry(
        path=rel_path,
        relative_path=rel_path,
        name=rel_path.split("/")[-1],
        ext=".txt",
        size=10,
        modified=datetime.now(),
    )


def test_list_folder_paths_includes_intermediate_dirs():
    entries = [_entry("영업/2026/보고서.txt"), _entry("최상위.txt")]
    assert list_folder_paths(entries) == ["영업", "영업/2026"]


def test_copy_structure_only_creates_empty_folders_without_files(tmp_path):
    entries = [_entry("영업/실적/a.txt"), _entry("법무/b.txt")]
    dest = tmp_path / "새위치"

    count, created, skipped = copy_structure_only(entries, str(dest))

    assert count == 3  # 영업, 영업/실적, 법무
    assert not skipped
    assert os.path.isdir(dest / "영업" / "실적")
    assert os.path.isdir(dest / "법무")
    # 파일은 절대 생성되지 않는다.
    assert not (dest / "영업" / "실적" / "a.txt").exists()
    assert not (dest / "법무" / "b.txt").exists()


def test_copy_structure_only_is_idempotent(tmp_path):
    entries = [_entry("영업/a.txt")]
    dest = tmp_path / "새위치"

    first_count, _, _ = copy_structure_only(entries, str(dest))
    second_count, created_again, _ = copy_structure_only(entries, str(dest))

    assert first_count == 1
    assert second_count == 0  # 이미 존재하므로 새로 만든 폴더는 없다.
    assert created_again == []
