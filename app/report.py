"""Before/After 트리 렌더링과 다운로드용 리포트 생성(JSON, 엑셀)."""

import io
import json
from datetime import datetime

from app.scanner import FileEntry

# 최종 상태 표시 우선순위(§7.11): 위에서부터 먼저 매칭되는 상태를 사용한다.
STATUS_LABELS = {
    "moved": "이동",
    "kept": "유지",
    "excluded": "제외",
    "review": "검토 필요",
    "conflict": "충돌",
    "blocked": "차단",
    "error": "오류",
}


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
    dsts = [info["dst"] if isinstance(info, dict) else info for info in assignments.values()]
    tree = paths_to_tree(dsts)
    return "\n".join(format_tree(tree))


def build_final_state(
    entries: list[FileEntry],
    valid_assignments: dict,
    excluded_srcs: set,
    rejected: list[dict],
) -> list[dict]:
    """실제로 적용했을 때의 최종 상태를 파일별로 계산한다(§7.11).

    이동/유지/제외/검토 필요/충돌/차단 파일을 모두 포함해, AI가 배정한 파일만
    보여주던 기존 방식보다 실제 결과에 가깝게 미리보기를 제공한다.
    """
    rejected_by_src = {r["src"]: r["reason"] for r in rejected}
    dst_counts: dict[str, int] = {}
    for info in valid_assignments.values():
        dst_counts[info["dst"]] = dst_counts.get(info["dst"], 0) + 1

    rows = []
    for entry in entries:
        src = entry.relative_path
        if src in excluded_srcs:
            rows.append(
                {"경로": src, "상태": STATUS_LABELS["excluded"], "목적지": "-", "비고": "사용자 제외"}
            )
        elif src in valid_assignments:
            info = valid_assignments[src]
            if dst_counts.get(info["dst"], 0) > 1:
                rows.append(
                    {
                        "경로": src,
                        "상태": STATUS_LABELS["conflict"],
                        "목적지": info["dst"],
                        "비고": "다른 파일과 목적지가 충돌합니다.",
                    }
                )
            else:
                rows.append(
                    {
                        "경로": src,
                        "상태": STATUS_LABELS["moved"],
                        "목적지": info["dst"],
                        "비고": info.get("reason", ""),
                    }
                )
        elif src in rejected_by_src:
            rows.append(
                {
                    "경로": src,
                    "상태": STATUS_LABELS["blocked"],
                    "목적지": "-",
                    "비고": rejected_by_src[src],
                }
            )
        elif entry.summary_status in ("unsupported", "failed", "hwp", "encrypted", "ocr_needed"):
            rows.append(
                {
                    "경로": src,
                    "상태": STATUS_LABELS["review"],
                    "목적지": "-",
                    "비고": entry.summary or entry.summary_status,
                }
            )
        else:
            rows.append(
                {"경로": src, "상태": STATUS_LABELS["kept"], "목적지": "-", "비고": "이동 대상 아님"}
            )
    return rows


def build_report(
    entries: list[FileEntry],
    duplicate_groups: dict[str, list[FileEntry]],
    proposal: dict,
    similar_docs: list[tuple[FileEntry, FileEntry, float]],
    final_state: list[dict] | None = None,
    env_items: list[dict] | None = None,
) -> str:
    report = {
        "generated_at": datetime.now().isoformat(),
        "total_files": len(entries),
        "environment": env_items or [],
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
        "final_state": final_state or [],
    }
    return json.dumps(report, ensure_ascii=False, indent=2)


def build_excel_report(
    entries: list[FileEntry],
    duplicate_groups: dict[str, list[FileEntry]],
    final_state: list[dict],
) -> bytes:
    """리포트를 엑셀(.xlsx) 바이트로 만든다(시트: 요약, 파일별 상태, 완전 중복)."""
    from openpyxl import Workbook

    wb = Workbook()

    summary_ws = wb.active
    summary_ws.title = "요약"
    status_counts: dict[str, int] = {}
    for row in final_state:
        status_counts[row["상태"]] = status_counts.get(row["상태"], 0) + 1
    summary_ws.append(["항목", "값"])
    summary_ws.append(["생성 시각", datetime.now().isoformat(timespec="seconds")])
    summary_ws.append(["전체 파일 수", len(entries)])
    summary_ws.append(["완전 중복 그룹 수", len(duplicate_groups)])
    for status, count in status_counts.items():
        summary_ws.append([f"파일 상태: {status}", count])

    files_ws = wb.create_sheet("파일별 최종 상태")
    files_ws.append(["경로", "상태", "목적지", "비고"])
    for row in final_state:
        files_ws.append([row["경로"], row["상태"], row["목적지"], row["비고"]])

    dup_ws = wb.create_sheet("완전 중복")
    dup_ws.append(["그룹 해시", "경로", "크기(bytes)"])
    for h, group in duplicate_groups.items():
        for e in group:
            dup_ws.append([h[:12], e.relative_path, e.size])

    buffer = io.BytesIO()
    wb.save(buffer)
    return buffer.getvalue()
