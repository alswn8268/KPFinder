"""Before/After 트리 렌더링과 다운로드용 리포트 생성."""

import json
from datetime import datetime

from app.scanner import FileEntry


def paths_to_tree(paths: list[str]) -> dict:
    tree: dict = {}
    for p in paths:
        parts = p.replace("\\", "/").split("/")
        node = tree
        for part in parts[:-1]:
            node = node.setdefault(part, {})
        node.setdefault("__files__", []).append(parts[-1])
    return tree


def format_tree(tree: dict, indent: str = "") -> list[str]:
    lines = []
    folders = sorted(k for k in tree if k != "__files__")
    files = sorted(tree.get("__files__", []))
    for folder in folders:
        lines.append(f"{indent}📁 {folder}/")
        lines.extend(format_tree(tree[folder], indent + "    "))
    for name in files:
        lines.append(f"{indent}📄 {name}")
    return lines


def render_current_tree(entries: list[FileEntry]) -> str:
    tree = paths_to_tree([e.relative_path for e in entries])
    return "\n".join(format_tree(tree)) or "(파일 없음)"


def render_proposed_tree(assignments: dict) -> str:
    if not assignments:
        return "(제안된 이동이 없습니다)"
    tree = paths_to_tree(list(assignments.values()))
    return "\n".join(format_tree(tree))


def build_report(
    entries: list[FileEntry],
    duplicate_groups: dict[str, list[FileEntry]],
    proposal: dict,
    similar_docs: list[tuple[FileEntry, FileEntry, float]],
) -> str:
    report = {
        "generated_at": datetime.now().isoformat(),
        "total_files": len(entries),
        "duplicate_groups": [
            {"hash": h, "files": [e.relative_path for e in group]}
            for h, group in duplicate_groups.items()
        ],
        "similar_documents": [
            {"a": a.relative_path, "b": b.relative_path, "score": round(score, 3)}
            for a, b, score in similar_docs
        ],
        "proposed_structure": proposal,
        "file_summaries": [
            {"path": e.relative_path, "status": e.summary_status, "summary": e.summary}
            for e in entries
        ],
    }
    return json.dumps(report, ensure_ascii=False, indent=2)
