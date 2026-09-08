"""폴더 스캔: 파일 목록 수집, 해시 계산, 완전 중복 탐지."""

import hashlib
import os
from dataclasses import dataclass
from datetime import datetime

SUPPORTED_TEXT_EXTS = {".txt", ".docx", ".xlsx", ".csv", ".pptx", ".pdf", ".hwpx", ".hwp"}
HASH_CHUNK_SIZE = 1024 * 1024


@dataclass
class FileEntry:
    path: str
    relative_path: str
    name: str
    ext: str
    size: int
    modified: datetime
    file_hash: str = ""
    summary: str = ""
    summary_status: str = "pending"  # pending | ok | empty | unsupported | failed


def scan_folder(
    root: str,
    exclude_dirs: set[str] | None = None,
    exclude_exts: set[str] | None = None,
    include_hidden: bool = False,
    max_file_size_mb: float | None = None,
    on_error=None,
) -> list[FileEntry]:
    """root 이하를 재귀적으로 스캔해 파일 목록을 반환한다.

    기본값은 기존 동작과 동일하다(숨김 파일/폴더 제외, 필터 없음, 크기 제한 없음).
    - exclude_dirs: 건너뛸 폴더 이름 집합(대소문자 무시, 트리 어디에 있든 매칭).
    - exclude_exts: 건너뛸 확장자 집합(".pdf" 또는 "pdf" 모두 허용).
    - max_file_size_mb: 이보다 큰 파일은 스캔 목록에서 제외.
    - on_error(path, reason): 읽지 못한 파일이 있을 때 호출(기존에는 조용히 버려졌다).
    """
    root = os.path.abspath(root)
    exclude_dirs_norm = {d.lower() for d in (exclude_dirs or ())}
    exclude_exts_norm = {
        e.lower() if e.startswith(".") else f".{e.lower()}" for e in (exclude_exts or ())
    }
    max_size_bytes = max_file_size_mb * 1024 * 1024 if max_file_size_mb else None

    entries: list[FileEntry] = []
    for dirpath, dirnames, filenames in os.walk(root):
        if not include_hidden:
            dirnames[:] = [d for d in dirnames if not d.startswith(".")]
        if exclude_dirs_norm:
            dirnames[:] = [d for d in dirnames if d.lower() not in exclude_dirs_norm]
        for filename in filenames:
            if not include_hidden and filename.startswith("."):
                continue
            ext = os.path.splitext(filename)[1].lower()
            if ext in exclude_exts_norm:
                continue
            full_path = os.path.join(dirpath, filename)
            try:
                stat = os.stat(full_path)
            except OSError as exc:
                if on_error:
                    on_error(full_path, str(exc))
                continue
            if max_size_bytes is not None and stat.st_size > max_size_bytes:
                continue
            rel_path = os.path.relpath(full_path, root)
            entries.append(
                FileEntry(
                    path=full_path,
                    relative_path=rel_path,
                    name=filename,
                    ext=ext,
                    size=stat.st_size,
                    modified=datetime.fromtimestamp(stat.st_mtime),
                )
            )
    return entries


def hash_file(path: str) -> str:
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(HASH_CHUNK_SIZE)
            if not chunk:
                break
            hasher.update(chunk)
    return hasher.hexdigest()


def compute_hashes(entries: list[FileEntry]) -> None:
    for entry in entries:
        try:
            entry.file_hash = hash_file(entry.path)
        except OSError:
            entry.file_hash = ""


def find_duplicate_groups(entries: list[FileEntry]) -> dict[str, list[FileEntry]]:
    """동일 해시(=완전히 같은 내용)를 가진 파일들을 그룹으로 묶어 반환한다."""
    groups: dict[str, list[FileEntry]] = {}
    for entry in entries:
        if not entry.file_hash:
            continue
        groups.setdefault(entry.file_hash, []).append(entry)
    return {h: es for h, es in groups.items() if len(es) > 1}
