from datetime import datetime

from app.content_graph import GraphTooLargeError, MAX_NODES_FOR_GRAPH, build_content_graph, render_content_graph
from app.scanner import FileEntry


def _entry(rel_path, summary="", status="pending"):
    e = FileEntry(
        path=rel_path,
        relative_path=rel_path,
        name=rel_path,
        ext=".txt",
        size=100,
        modified=datetime.now(),
    )
    e.summary = summary
    e.summary_status = status
    return e


def test_build_content_graph_creates_node_per_entry():
    entries = [_entry("a.txt"), _entry("b.txt")]
    graph, edges = build_content_graph(entries, min_score=0.99)
    assert set(graph.nodes) == {"a.txt", "b.txt"}
    assert edges == []


def test_build_content_graph_adds_edge_above_threshold():
    a = _entry("보고서_v1.txt", "동일한 요약", status="ok")
    b = _entry("보고서_v2.txt", "동일한 요약", status="ok")
    graph, edges = build_content_graph([a, b], min_score=0.5)
    assert graph.has_edge("보고서_v1.txt", "보고서_v2.txt")
    assert len(edges) == 1


def test_render_content_graph_returns_figure_for_empty_graph():
    fig, edges = render_content_graph([_entry("a.txt"), _entry("b.txt")], min_score=0.99)
    assert fig is not None
    assert edges == []


def test_render_content_graph_raises_when_too_many_entries():
    entries = [_entry(f"f{i}.txt") for i in range(MAX_NODES_FOR_GRAPH + 1)]
    try:
        render_content_graph(entries)
        assert False, "expected GraphTooLargeError"
    except GraphTooLargeError:
        pass
