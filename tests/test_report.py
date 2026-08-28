from app.report import render_current_tree, render_proposed_tree
from app.scanner import FileEntry
from datetime import datetime


def _entry(rel_path: str) -> FileEntry:
    return FileEntry(
        path=rel_path,
        relative_path=rel_path,
        name=rel_path.split("/")[-1],
        ext=".txt",
        size=10,
        modified=datetime.now(),
    )


def test_render_current_tree_groups_by_folder():
    entries = [_entry("a.txt"), _entry("사업계획/b.txt"), _entry("사업계획/c.txt")]
    tree_text = render_current_tree(entries)

    assert "📁 사업계획/" in tree_text
    assert "📄 a.txt" in tree_text
    assert "📄 b.txt" in tree_text


def test_render_proposed_tree_empty_assignments():
    assert render_proposed_tree({}) == "(제안된 이동이 없습니다)"


def test_render_proposed_tree_with_assignments():
    text = render_proposed_tree({"a.txt": "보고서/a.txt", "b.txt": "보고서/b.txt"})
    assert "📁 보고서/" in text
    assert "📄 a.txt" in text
