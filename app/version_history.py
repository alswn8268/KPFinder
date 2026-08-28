"""폴더별 정리 작업의 버전 히스토리 관리 (Obsidian의 파일 버전 관리에서 착안).

'적용'을 누를 때마다 새로운 버전이 기록되고, 사용자는 언제든 과거 어느 버전이든
골라서 그 이동을 되돌릴 수 있다. 실제 파일 이동/되돌리기는 app.file_ops가 담당하고,
이 모듈은 그 이동 로그들을 폴더별 '버전' 단위로 목록화하는 역할만 한다.
"""

import hashlib
import json
import os
from datetime import datetime

from app.organizer import CACHE_DIR


def _index_path_for(root: str) -> str:
    os.makedirs(CACHE_DIR, exist_ok=True)
    key = hashlib.sha256(os.path.abspath(root).encode("utf-8")).hexdigest()[:16]
    return os.path.join(CACHE_DIR, f"version_index_{key}.json")


def list_versions(root: str) -> list[dict]:
    """오래된 순서로 버전 목록을 반환한다."""
    path = _index_path_for(root)
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


def _save_versions(root: str, versions: list[dict]) -> None:
    with open(_index_path_for(root), "w", encoding="utf-8") as f:
        json.dump(versions, f, ensure_ascii=False, indent=2)


def record_version(root: str, log_path: str, note: str, files_moved: int) -> dict:
    versions = list_versions(root)
    version = {
        "version_id": f"v{len(versions) + 1}",
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "note": note or "",
        "files_moved": files_moved,
        "log_path": log_path,
        "restored": False,
    }
    versions.append(version)
    _save_versions(root, versions)
    return version


def mark_restored(root: str, version_id: str) -> None:
    versions = list_versions(root)
    for v in versions:
        if v["version_id"] == version_id:
            v["restored"] = True
    _save_versions(root, versions)
