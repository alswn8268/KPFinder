"""폴더 스캔: 파일 목록 수집, 해시 계산, 완전 중복 탐지."""

import hashlib
import os
from dataclasses import dataclass
from datetime import datetime

SUPPORTED_TEXT_EXTS = {".txt", ".docx", ".xlsx", ".csv", ".pptx", ".pdf"}
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


def scan_folder(root: str) -> list[FileEntry]:
    """root 이하를 재귀적으로 스캔해 파일 목록을 반환한다. 숨김 파일/폴더는 건너뛴다."""
    root = os.path.abspath(root)
    entries: list[FileEntry] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if not d.startswith(".")]
        for filename in filenames:
            if filename.startswith("."):
                continue
            full_path = os.path.join(dirpath, filename)
            try:
                stat = os.stat(full_path)
            except OSError:
                continue
            ext = os.path.splitext(filename)[1].lower()
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
