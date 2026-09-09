import os
from datetime import datetime

from app.content_graph import GraphTooLargeError, MAX_NODES_FOR_GRAPH
from app.directory_graph import (
    ROOT_LABEL,
    build_directory_relation_graph,
    build_directory_tree,
    render_directory_relation_graph,
    render_directory_tree,
)
from app.scanner import FileEntry


def _entry(rel_path, summary="", status="pending"):
    e = FileEntry(
        path=rel_path,
        relative_path=rel_path,
        name=os.path.basename(rel_path),
        ext=".txt",
        size=10,
        modified=datetime.now(),
    )
    e.summary = summary
    e.summary_status = status
    return e


def test_build_directory_tree_creates_parent_child_edges():
    entries = [_entry("a.txt"), _entry("폴더1/b.txt"), _entry("폴더1/하위/c.txt")]
    tree = build_directory_tree(entries)

    assert tree.has_edge(ROOT_LABEL, "폴더1")
    assert tree.has_edge("폴더1", "폴더1/하위")
    assert tree.nodes[ROOT_LABEL]["file_count"] == 1
    assert tree.nodes["폴더1"]["file_count"] == 1
    assert tree.nodes["폴더1/하위"]["file_count"] == 1


def test_build_directory_relation_graph_links_similar_cross_folder_files():
    a = _entry("폴더A/보고서.txt", "동일한 요약 내용", status="ok")
    b = _entry("폴더B/보고서_사본.txt", "동일한 요약 내용", status="ok")
    graph = build_directory_relation_graph([a, b], min_score=0.5)
    assert graph.has_edge("폴더A", "폴더B")


def test_build_directory_relation_graph_ignores_same_folder_pairs():
    a = _entry("폴더A/보고서1.txt", "동일한 요약 내용", status="ok")
    b = _entry("폴더A/보고서2.txt", "동일한 요약 내용", status="ok")
    graph = build_directory_relation_graph([a, b], min_score=0.5)
    assert graph.number_of_edges() == 0


def test_render_functions_return_figures():
    entries = [_entry("a.txt"), _entry("폴더1/b.txt")]
    fig1 = render_directory_tree(entries)
    fig2 = render_directory_relation_graph(entries, min_score=0.99)
    assert fig1 is not None
    assert fig2 is not None


def test_build_directory_relation_graph_raises_when_too_many_entries():
    """content_graph.py와 같은 O(n^2) 계산이라 같은 상한이 있어야 한다 — 이전에는
    이 가드가 빠져 있어 큰 폴더에서 요청이 그대로 멈춰버릴 수 있었다(회귀 방지)."""
    entries = [_entry(f"폴더{i}/f.txt") for i in range(MAX_NODES_FOR_GRAPH + 1)]
    try:
        build_directory_relation_graph(entries)
        assert False, "expected GraphTooLargeError"
    except GraphTooLargeError:
        pass
