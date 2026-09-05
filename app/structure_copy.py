"""폴더 구조만(파일 내용 없이) 다른 위치에 그대로 만드는 기능.

새 프로젝트를 시작할 때 "지난번과 같은 폴더 체계만" 다시 쓰고 싶을 때, 혹은
정리 전에 미리 새 위치에 뼈대만 만들어 보고 싶을 때 사용한다. 파일은 절대
복사하지 않고, 빈 폴더만 생성한다.
"""

import os

from app import path_safety
from app.scanner import FileEntry


def list_folder_paths(entries: list[FileEntry]) -> list[str]:
    """스캔된 파일들이 속한 모든 하위 폴더 경로(중간 경로 포함)를 중복 없이 뽑는다."""
    folders: set[str] = set()
    for entry in entries:
        rel_dir = os.path.dirname(entry.relative_path.replace("\\", "/"))
        if not rel_dir:
            continue
        parts = rel_dir.split("/")
        for i in range(1, len(parts) + 1):
            folders.add("/".join(parts[:i]))
    return sorted(folders)


def copy_structure_only(entries: list[FileEntry], dest_root: str) -> tuple[int, list[str], list[str]]:
    """entries의 폴더 구조만 dest_root 아래에 재현한다(파일은 만들지 않는다).

    반환값: (생성한 폴더 수, 생성한 폴더 목록, 건너뛴/거부된 폴더와 사유 목록)
    """
    dest_root = os.path.abspath(dest_root)
    os.makedirs(dest_root, exist_ok=True)

    created: list[str] = []
    skipped: list[str] = []
    for rel_dir in list_folder_paths(entries):
        ok, reason = path_safety.is_safe_destination(dest_root, rel_dir)
        if not ok:
            skipped.append(f"{rel_dir}: {reason}")
            continue
        target = os.path.join(dest_root, rel_dir)
        already_existed = os.path.isdir(target)
        os.makedirs(target, exist_ok=True)
        if not already_existed:
            created.append(rel_dir)

    return len(created), created, skipped
