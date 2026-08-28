"""파일 내용 기반 연관도 그래프 (Obsidian '그래프 뷰'에서 착안).

노드 = 파일, 엣지 = 파일명/AI 요약 유사도. 임베딩·외부 API 없이 difflib 기반
가벼운 점수만 사용하므로 완벽한 의미 기반 연관도는 아니지만, 오프라인에서
즉시 계산 가능하고 "어떤 문서들이 서로 관련 있어 보이는지" 감을 잡기엔 충분하다.
"""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx

from app.plotting import apply_korean_font
from app.relatedness import build_relatedness_edges
from app.scanner import FileEntry

MAX_NODES_FOR_GRAPH = 400
_EXT_PALETTE = plt.get_cmap("tab20")


class GraphTooLargeError(Exception):
    pass


def _ext_color(ext: str, ext_order: list[str]):
    if ext not in ext_order:
        ext_order.append(ext)
    return _EXT_PALETTE((ext_order.index(ext) % 20) / 20)


def build_content_graph(
    entries: list[FileEntry], min_score: float = 0.35
) -> tuple[nx.Graph, list[tuple[FileEntry, FileEntry, float]]]:
    graph = nx.Graph()
    for e in entries:
        graph.add_node(e.relative_path, ext=e.ext or "(없음)", size=e.size)
    edges = build_relatedness_edges(entries, min_score=min_score)
    for a, b, score in edges:
        graph.add_edge(a.relative_path, b.relative_path, weight=score)
    return graph, edges


def render_content_graph(
    entries: list[FileEntry],
    min_score: float = 0.35,
    show_labels: bool = True,
    hide_isolated: bool = True,
):
    if len(entries) > MAX_NODES_FOR_GRAPH:
        raise GraphTooLargeError(
            f"파일이 너무 많아({len(entries)}개) 그래프를 그리지 않습니다. "
            f"{MAX_NODES_FOR_GRAPH}개 이하일 때만 지원합니다."
        )
    apply_korean_font()

    graph, edges = build_content_graph(entries, min_score=min_score)
    if hide_isolated:
        graph = graph.copy()
        graph.remove_nodes_from(list(nx.isolates(graph)))

    fig, ax = plt.subplots(figsize=(9, 7))
    if graph.number_of_nodes() == 0:
        ax.text(
            0.5, 0.5, "표시할 연관 관계가 없습니다.\n임계값을 낮추거나 AI 분석을 먼저 실행해보세요.",
            ha="center", va="center",
        )
        ax.axis("off")
        return fig, edges

    k = 1.4 / max(len(graph.nodes), 1) ** 0.5
    pos = nx.spring_layout(graph, seed=42, k=k)

    ext_order: list[str] = []
    node_colors = [_ext_color(graph.nodes[n]["ext"], ext_order) for n in graph.nodes]
    node_sizes = [200 + min(graph.nodes[n]["size"], 200_000) / 400 for n in graph.nodes]
    weights = [graph[u][v]["weight"] for u, v in graph.edges]

    nx.draw_networkx_edges(graph, pos, ax=ax, width=[1 + 3 * w for w in weights], alpha=0.4)
    nx.draw_networkx_nodes(graph, pos, ax=ax, node_color=node_colors, node_size=node_sizes)
    if show_labels:
        labels = {n: n.rsplit("/", 1)[-1] for n in graph.nodes}
        nx.draw_networkx_labels(graph, pos, labels=labels, ax=ax, font_size=7)
    ax.axis("off")
    fig.tight_layout()
    return fig, edges
