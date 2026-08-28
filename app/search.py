"""Obsidian 식 빠른 검색: 파일명/경로/AI 요약 내용으로 필터링한다 (P1)."""

from app.scanner import FileEntry


def search_entries(
    entries: list[FileEntry],
    query: str = "",
    extensions: list[str] | None = None,
) -> list[FileEntry]:
    results = entries
    if extensions:
        wanted = {ext.lower() for ext in extensions}
        results = [e for e in results if e.ext.lower() in wanted]

    query = query.strip().lower()
    if query:
        results = [
            e
            for e in results
            if query in e.name.lower()
            or query in e.relative_path.lower()
            or query in (e.summary or "").lower()
        ]
    return results
