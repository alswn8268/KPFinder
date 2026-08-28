"""실제 파일 이동(적용)과 되돌리기(undo).

원칙: 사람이 계획(plan)을 확인하고 명시적으로 승인한 뒤에만 apply_move_plan()이 호출된다.
모든 이동은 로그로 남겨 undo_move_plan()으로 되돌릴 수 있다.
"""

import json
import os
import shutil
from datetime import datetime

from app.organizer import CACHE_DIR


def build_move_plan(root: str, assignments: dict) -> list[dict]:
    """검증된 assignments(기존 상대경로 -> 새 상대경로)로부터 이동 계획을 만든다."""
    root = os.path.abspath(root)
    plan = []
    for rel_src, rel_dst in assignments.items():
        src = os.path.join(root, rel_src)
        dst = os.path.join(root, rel_dst)
        if os.path.abspath(src) == os.path.abspath(dst):
            continue
        plan.append({"src": src, "dst": dst, "rel_src": rel_src, "rel_dst": rel_dst})
    return plan


def apply_move_plan(plan: list[dict]) -> str:
    """계획대로 파일을 이동하고, 되돌리기용 로그 파일 경로를 반환한다.

    목적지에 이미 파일이 있으면 덮어쓰지 않고 `_1`, `_2`.. 를 붙여 보존한다.
    """
    os.makedirs(CACHE_DIR, exist_ok=True)
    log_entries = []
    for item in plan:
        src, dst = item["src"], item["dst"]
        if not os.path.exists(src):
            continue
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        final_dst = dst
        counter = 1
        base, ext = os.path.splitext(dst)
        while os.path.exists(final_dst):
            final_dst = f"{base}_{counter}{ext}"
            counter += 1
        shutil.move(src, final_dst)
        log_entries.append({"src": src, "dst": final_dst})

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = os.path.join(CACHE_DIR, f"move_log_{timestamp}.json")
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(log_entries, f, ensure_ascii=False, indent=2)
    return log_path


def undo_move_plan(log_path: str) -> int:
    """이동 로그를 읽어 파일들을 원래 위치로 되돌린다. 되돌린 파일 수를 반환한다."""
    with open(log_path, "r", encoding="utf-8") as f:
        log_entries = json.load(f)
    restored = 0
    for entry in reversed(log_entries):
        src, dst = entry["src"], entry["dst"]
        if os.path.exists(dst):
            os.makedirs(os.path.dirname(src), exist_ok=True)
            shutil.move(dst, src)
            restored += 1
    return restored


def list_move_logs() -> list[str]:
    if not os.path.isdir(CACHE_DIR):
        return []
    logs = [
        os.path.join(CACHE_DIR, f)
        for f in os.listdir(CACHE_DIR)
        if f.startswith("move_log_") and f.endswith(".json")
    ]
    return sorted(logs, reverse=True)
