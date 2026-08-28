"""디렉토리(폴더) 단위의 구조도와 연관도 그래프.

- 구조도(build_directory_tree): 상위/하위 폴더 관계를 트리로 표현한다.
- 연관도(build_directory_relation_graph): 서로 다른 폴더에 있는 파일들의 내용
  유사도를 폴더 단위로 집계해, "내용은 비슷한데 다른 폴더에 흩어져 있는" 폴더
  쌍을 찾아준다 — 폴더 병합/통합 후보를 가늠하는 용도.

pygraphviz 등 외부 바이너리 없이 networkx + matplotlib만으로 그린다.
"""

import os
from collections import defaultdict

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx

from app.plotting import apply_korean_font
from app.relatedness import build_relatedness_edges
from app.scanner import FileEntry

ROOT_LABEL = "(최상위)"


def _folder_of(rel_path: str) -> str:
    d = os.path.dirname(rel_path.replace("\\", "/"))
    return d if d else ROOT_LABEL


def build_directory_tree(entries: list[FileEntry]) -> nx.DiGraph:
    """폴더 경로들로부터 부모->자식 트리를 만든다. 노드 속성 file_count = 직속 파일 수."""
    tree = nx.DiGraph()
    tree.add_node(ROOT_LABEL, file_count=0)
    file_counts: dict[str, int] = defaultdict(int)

    for e in entries:
        folder = _folder_of(e.relative_path)
        file_counts[folder] += 1
        if folder == ROOT_LABEL:
            continue
        parts = folder.split("/")
        parent = ROOT_LABEL
        acc = ""
        for part in parts:
            acc = f"{acc}/{part}" if acc else part
            if not tree.has_node(acc):
                tree.add_node(acc, file_count=0)
            if not tree.has_edge(parent, acc):
                tree.add_edge(parent, acc)
            parent = acc

    for node in tree.nodes:
        tree.nodes[node]["file_count"] = file_counts.get(node, 0)
    return tree


def _hierarchy_positions(tree: nx.DiGraph, root: str) -> dict:
    """networkx 그래프에 pygraphviz 없이 간단한 계층형(트리) 좌표를 계산한다."""
    positions: dict = {}

    def leaf_count(node: str) -> int:
        children = list(tree.successors(node))
        return 1 if not children else sum(leaf_count(c) for c in children)

    def assign(node: str, depth: int, x_start: float, x_end: float) -> None:
        positions[node] = ((x_start + x_end) / 2, -depth)
        children = list(tree.successors(node))
        if not children:
            return
        total = sum(leaf_count(c) for c in children)
        cursor = x_start
        for child in children:
            width = (x_end - x_start) * (leaf_count(child) / total)
            assign(child, depth + 1, cursor, cursor + width)
            cursor += width

    assign(root, 0, 0.0, 1.0)
    return positions


def render_directory_tree(entries: list[FileEntry]):
    apply_korean_font()
    tree = build_directory_tree(entries)
    pos = _hierarchy_positions(tree, ROOT_LABEL)

    fig, ax = plt.subplots(figsize=(9, 6))
    sizes = [300 + tree.nodes[n]["file_count"] * 60 for n in tree.nodes]
    labels = {n: (ROOT_LABEL if n == ROOT_LABEL else n.rsplit("/", 1)[-1]) for n in tree.nodes}

    nx.draw_networkx_edges(tree, pos, ax=ax, arrows=False, alpha=0.5)
    nx.draw_networkx_nodes(tree, pos, ax=ax, node_size=sizes, node_color="#8ecae6")
    nx.draw_networkx_labels(tree, pos, labels=labels, ax=ax, font_size=8)
    ax.axis("off")
    fig.tight_layout()
    return fig


def build_directory_relation_graph(entries: list[FileEntry], min_score: float = 0.4) -> nx.Graph:
    """서로 다른 폴더에 있는 파일들의 내용 유사도를 폴더 단위로 평균 집계한 그래프."""
    all_pairs = build_relatedness_edges(entries, min_score=0.0, exclude_exact_duplicates=True)
    pair_scores: dict[tuple[str, str], list[float]] = defaultdict(list)
    file_counts: dict[str, int] = defaultdict(int)
    for e in entries:
        file_counts[_folder_of(e.relative_path)] += 1

    for a, b, score in all_pairs:
        fa, fb = _folder_of(a.relative_path), _folder_of(b.relative_path)
        if fa == fb:
            continue
        pair_scores[tuple(sorted((fa, fb)))].append(score)

    graph = nx.Graph()
    for folder, count in file_counts.items():
        graph.add_node(folder, file_count=count)
    for (fa, fb), scores in pair_scores.items():
        avg_score = sum(scores) / len(scores)
        if avg_score >= min_score:
            graph.add_edge(fa, fb, weight=avg_score, pair_count=len(scores))
    return graph


def render_directory_relation_graph(entries: list[FileEntry], min_score: float = 0.4):
    apply_korean_font()
    graph = build_directory_relation_graph(entries, min_score=min_score)
    graph = graph.copy()
    graph.remove_nodes_from(list(nx.isolates(graph)))

    fig, ax = plt.subplots(figsize=(9, 6))
    if graph.number_of_nodes() == 0:
        ax.text(
            0.5, 0.5, "폴더 간 뚜렷한 연관 관계가 없습니다.\n임계값을 낮춰보세요.",
            ha="center", va="center",
        )
        ax.axis("off")
        return fig

    pos = nx.spring_layout(graph, seed=7)
    sizes = [300 + graph.nodes[n]["file_count"] * 60 for n in graph.nodes]
    weights = [graph[u][v]["weight"] for u, v in graph.edges]

    nx.draw_networkx_edges(
        graph, pos, ax=ax, width=[1 + 4 * w for w in weights], alpha=0.5, edge_color="#e76f51"
    )
    nx.draw_networkx_nodes(graph, pos, ax=ax, node_size=sizes, node_color="#ffb703")
    nx.draw_networkx_labels(
        graph, pos, labels={n: n.rsplit("/", 1)[-1] for n in graph.nodes}, ax=ax, font_size=8
    )
    ax.axis("off")
    fig.tight_layout()
    return fig
