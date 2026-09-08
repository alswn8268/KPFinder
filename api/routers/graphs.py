import networkx as nx
from fastapi import APIRouter, HTTPException

from app.content_graph import MAX_NODES_FOR_GRAPH, build_content_graph
from app.directory_graph import ROOT_LABEL, build_directory_relation_graph, build_directory_tree
from api.serialization import models_to_entries
from api.schemas import GraphEdgeModel, GraphNodeModel, GraphRequest, GraphResponse, TreeNodeModel

router = APIRouter(prefix="/api/graphs", tags=["graphs"])


def _graph_response(graph: nx.Graph) -> GraphResponse:
    nodes = [
        GraphNodeModel(
            id=n,
            ext=graph.nodes[n].get("ext", ""),
            size=graph.nodes[n].get("size", 0),
            file_count=graph.nodes[n].get("file_count", 0),
        )
        for n in graph.nodes
    ]
    edges = [
        GraphEdgeModel(source=u, target=v, weight=graph[u][v].get("weight", 0.0))
        for u, v in graph.edges
    ]
    return GraphResponse(nodes=nodes, edges=edges)


@router.post("/content", response_model=GraphResponse)
def content_graph(req: GraphRequest):
    if len(req.entries) > MAX_NODES_FOR_GRAPH:
        raise HTTPException(
            status_code=422,
            detail=(
                f"파일이 너무 많아({len(req.entries)}개) 그래프를 그리지 않습니다. "
                f"{MAX_NODES_FOR_GRAPH}개 이하일 때만 지원합니다."
            ),
        )
    entries = models_to_entries(req.entries)
    graph, _edges = build_content_graph(entries, min_score=req.min_score)
    if req.hide_isolated:
        graph = graph.copy()
        graph.remove_nodes_from(list(nx.isolates(graph)))
    return _graph_response(graph)


def _tree_to_model(tree: nx.DiGraph, node: str) -> TreeNodeModel:
    children = [_tree_to_model(tree, child) for child in tree.successors(node)]
    return TreeNodeModel(id=node, file_count=tree.nodes[node].get("file_count", 0), children=children)


@router.post("/directory-tree", response_model=TreeNodeModel)
def directory_tree(req: GraphRequest):
    entries = models_to_entries(req.entries)
    tree = build_directory_tree(entries)
    return _tree_to_model(tree, ROOT_LABEL)


@router.post("/directory-relation", response_model=GraphResponse)
def directory_relation(req: GraphRequest):
    entries = models_to_entries(req.entries)
    graph = build_directory_relation_graph(entries, min_score=req.min_score)
    graph = graph.copy()
    graph.remove_nodes_from(list(nx.isolates(graph)))
    return _graph_response(graph)
