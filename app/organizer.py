"""파일 요약 오케스트레이션(+캐싱)과 폴더 구조 제안."""

import hashlib
import json
import os

from app import llm_client
from app.scanner import FileEntry
from app.text_extractor import ExtractionError, extract_text, is_supported

CACHE_DIR = os.path.join(os.path.expanduser("~"), ".ai_folder_organizer")

_STATUS_LABELS = {
    "ok": "완료",
    "empty": "내용 없음",
    "unsupported": "미지원 형식",
    "failed": "요약 불가",
    "pending": "대기",
}


def status_label(status: str) -> str:
    return _STATUS_LABELS.get(status, status)


def _cache_path_for(root: str) -> str:
    os.makedirs(CACHE_DIR, exist_ok=True)
    key = hashlib.sha256(os.path.abspath(root).encode("utf-8")).hexdigest()[:16]
    return os.path.join(CACHE_DIR, f"summary_cache_{key}.json")


def load_cache(root: str) -> dict:
    path = _cache_path_for(root)
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def save_cache(root: str, cache: dict) -> None:
    path = _cache_path_for(root)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


def _cache_key(entry: FileEntry) -> str:
    # 해시+크기가 같으면 같은 파일 내용으로 간주해 재요약을 건너뛴다(속도 최적화).
    return f"{entry.file_hash}:{entry.size}"


def summarize_entries(
    entries: list[FileEntry], root: str, model: str, progress_cb=None
) -> None:
    """각 FileEntry.summary / summary_status를 채운다. 캐시가 있으면 LLM 호출을 건너뛴다."""
    cache = load_cache(root)
    total = len(entries)
    for i, entry in enumerate(entries, start=1):
        key = _cache_key(entry)
        cached = cache.get(key)
        if cached:
            entry.summary = cached["summary"]
            entry.summary_status = cached["status"]
        elif not is_supported(entry.ext):
            entry.summary = ""
            entry.summary_status = "unsupported"
        else:
            try:
                text = extract_text(entry.path, entry.ext)
                if not text.strip():
                    entry.summary = ""
                    entry.summary_status = "empty"
                else:
                    entry.summary = llm_client.summarize_text(text, model=model)
                    entry.summary_status = "ok"
            except (ExtractionError, llm_client.OllamaError, OSError) as exc:
                entry.summary = f"요약 불가: {exc}"
                entry.summary_status = "failed"
            cache[key] = {"summary": entry.summary, "status": entry.summary_status}
            save_cache(root, cache)
        if progress_cb:
            progress_cb(i, total, entry)


def propose_structure(entries: list[FileEntry], model: str) -> dict:
    summarized = [
        {"relative_path": e.relative_path, "ext": e.ext, "summary": e.summary or "(요약 없음)"}
        for e in entries
        if e.summary_status in ("ok", "empty")
    ]
    if not summarized:
        return {
            "categories": [],
            "assignments": {},
            "notes": "요약된 파일이 없어 폴더 구조를 제안할 수 없습니다.",
        }
    return llm_client.propose_folder_structure(summarized, model=model)


def validate_assignments(entries: list[FileEntry], assignments: dict) -> dict:
    """LLM이 만들어낸 assignments 중 실제로 존재하는 파일 경로만 남긴다."""
    valid_paths = {e.relative_path for e in entries}
    return {
        src: dst
        for src, dst in (assignments or {}).items()
        if src in valid_paths and dst
    }
