"""실제 파일 이동(적용)과 되돌리기(undo).

원칙: 사람이 계획(plan)을 확인하고 명시적으로 승인한 뒤에만 apply_move_plan()이 호출된다.
이동 계획은 이동을 시작하기 전에 먼저 로그로 저장하고, 파일을 옮길 때마다 결과를 즉시
한 줄씩 기록한다. 배치 도중 실패하면 이미 옮긴 파일들을 자동으로 원래 위치로 되돌린다.
"""

import json
import os
import shutil
from datetime import datetime

from app import path_safety
from app.organizer import CACHE_DIR
from app.scanner import hash_file


def build_move_plan(root: str, assignments: dict) -> list[dict]:
    """검증된 assignments(기존 상대경로 -> 새 상대경로)로부터 이동 계획을 만든다."""
    root = os.path.abspath(root)
    plan = []
    for rel_src, rel_dst in assignments.items():
        ok, _reason = path_safety.is_safe_destination(root, rel_dst)
        if not ok:
            continue
        src = os.path.join(root, rel_src)
        dst = os.path.join(root, rel_dst)
        if os.path.abspath(src) == os.path.abspath(dst):
            continue
        plan.append({"src": src, "dst": dst, "rel_src": rel_src, "rel_dst": rel_dst})
    return plan


def _new_log_path() -> str:
    os.makedirs(CACHE_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    return os.path.join(CACHE_DIR, f"move_log_{timestamp}.jsonl")


def _append_event(log_path: str, event: dict) -> None:
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")
        f.flush()
        os.fsync(f.fileno())


def save_plan(plan: list[dict], src_hashes: dict[str, str]) -> str:
    """이동을 시작하기 전에 계획 전체를 로그 파일에 먼저 기록하고 로그 경로를 반환한다."""
    log_path = _new_log_path()
    with open(log_path, "w", encoding="utf-8") as f:
        for index, item in enumerate(plan):
            event = {
                "event": "planned",
                "index": index,
                "rel_src": item["rel_src"],
                "rel_dst": item["rel_dst"],
                "src": item["src"],
                "dst": item["dst"],
                "src_hash": src_hashes.get(item["rel_src"], ""),
            }
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
        f.flush()
        os.fsync(f.fileno())
    return log_path


def _rollback(log_path: str, moved: list[tuple[int, str, str]]) -> None:
    """이미 이동된 파일들을 역순으로 원래 위치로 되돌린다."""
    for index, src, final_dst in reversed(moved):
        try:
            if os.path.exists(final_dst):
                os.makedirs(os.path.dirname(src), exist_ok=True)
                shutil.move(final_dst, src)
            _append_event(log_path, {"event": "rollback_ok", "index": index})
        except OSError as exc:
            _append_event(
                log_path, {"event": "rollback_failed", "index": index, "error": str(exc)}
            )


def apply_move_plan(plan: list[dict], entries: list) -> tuple[str, int]:
    """계획대로 파일을 이동하고, (로그 경로, 실제 이동 성공 개수)를 반환한다.

    - 목적지에 이미 파일이 있으면 덮어쓰지 않고 `_1`, `_2`.. 를 붙여 보존한다.
    - 이동 계획은 파일 이동을 시작하기 전에 먼저 저장하고, 이동 결과는 건마다 즉시 기록한다.
    - 스캔 시점 이후 원본 내용이 바뀐 파일은 이동하지 않고 건너뛴다.
    - 도중 이동이 실패하면 이미 이동한 파일들을 자동으로 롤백한다.
    """
    src_hashes = {e.relative_path: e.file_hash for e in entries}
    log_path = save_plan(plan, src_hashes)

    moved: list[tuple[int, str, str]] = []
    for index, item in enumerate(plan):
        src, dst = item["src"], item["dst"]
        rel_src = item["rel_src"]

        if os.path.islink(src):
            _append_event(log_path, {"event": "skipped_symlink", "index": index})
            continue
        if not os.path.exists(src):
            _append_event(log_path, {"event": "skipped_missing", "index": index})
            continue

        expected_hash = src_hashes.get(rel_src, "")
        if expected_hash:
            try:
                current_hash = hash_file(src)
            except OSError:
                _append_event(log_path, {"event": "skipped_missing", "index": index})
                continue
            if current_hash != expected_hash:
                _append_event(log_path, {"event": "skipped_changed", "index": index})
                continue

        os.makedirs(os.path.dirname(dst), exist_ok=True)
        final_dst = dst
        counter = 1
        base, ext = os.path.splitext(dst)
        while os.path.exists(final_dst):
            final_dst = f"{base}_{counter}{ext}"
            counter += 1

        try:
            shutil.move(src, final_dst)
        except OSError as exc:
            _append_event(
                log_path, {"event": "move_failed", "index": index, "error": str(exc)}
            )
            _rollback(log_path, moved)
            return log_path, 0  # 실패 시 이미 이동한 파일까지 모두 롤백했으므로 성공 개수는 0

        moved.append((index, src, final_dst))
        _append_event(
            log_path, {"event": "move_ok", "index": index, "src": src, "dst": final_dst}
        )

    return log_path, len(moved)


def _read_events(log_path: str) -> list[dict]:
    events = []
    with open(log_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                events.append(json.loads(line))
    return events


def undo_move_plan(log_path: str) -> int:
    """이동 로그를 읽어 성공적으로 이동됐던 파일들을 원래 위치로 되돌린다.

    되돌린 파일 수를 반환한다.
    """
    events = _read_events(log_path)
    last_by_index: dict[int, dict] = {}
    for event in events:
        idx = event.get("index")
        if idx is not None and event["event"] in ("move_ok", "rollback_ok"):
            last_by_index[idx] = event

    to_restore = [
        e for e in last_by_index.values() if e["event"] == "move_ok"
    ]
    to_restore.sort(key=lambda e: e["index"], reverse=True)

    restored = 0
    for event in to_restore:
        src, dst = event["src"], event["dst"]
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
        if f.startswith("move_log_") and f.endswith(".jsonl")
    ]
    return sorted(logs, reverse=True)
