import os

import pytest

from app.path_safety import is_safe_destination, is_within_root, validate_rel_dst


def test_rejects_parent_traversal():
    ok, reason = validate_rel_dst("../outside.txt")
    assert not ok
    assert reason


def test_rejects_parent_traversal_in_middle_segment():
    ok, _ = validate_rel_dst("폴더/../../외부/x.txt")
    assert not ok


def test_rejects_absolute_dst():
    ok, _ = validate_rel_dst("C:/other/b.txt")
    assert not ok
    ok, _ = validate_rel_dst("/home/user/x.txt")
    assert not ok


def test_rejects_windows_reserved_name():
    ok, _ = validate_rel_dst("폴더/CON.txt")
    assert not ok
    ok, _ = validate_rel_dst("com1.docx")
    assert not ok


def test_rejects_illegal_chars():
    ok, _ = validate_rel_dst('폴더/bad<name>.txt')
    assert not ok


def test_rejects_trailing_dot_or_space():
    ok, _ = validate_rel_dst("폴더 /file.txt")
    assert not ok
    ok, _ = validate_rel_dst("폴더./file.txt")
    assert not ok


def test_rejects_path_too_long(tmp_path):
    long_name = "a" * 300 + ".txt"
    ok, reason = is_safe_destination(str(tmp_path), long_name)
    assert not ok
    assert "길이" in reason


def test_allows_normal_nested_path(tmp_path):
    ok, reason = is_safe_destination(str(tmp_path), "보고서/2026/영업보고서.docx")
    assert ok
    assert reason == ""


def test_is_within_root_true_for_nested_path(tmp_path):
    nested = os.path.join(str(tmp_path), "a", "b.txt")
    assert is_within_root(str(tmp_path), nested)


def test_is_within_root_false_for_sibling_path(tmp_path):
    sibling = os.path.join(os.path.dirname(str(tmp_path)), "other", "b.txt")
    assert not is_within_root(str(tmp_path), sibling)


def test_rejects_symlink_escape(tmp_path):
    outside = tmp_path.parent / "outside_target"
    outside.mkdir(exist_ok=True)
    root = tmp_path / "root"
    root.mkdir()
    link = root / "link_out"
    try:
        link.symlink_to(outside, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("symlink 생성 권한이 없는 환경입니다.")

    escaped = os.path.join(str(link), "file.txt")
    assert not is_within_root(str(root), escaped)
