"""파일명 일괄 변경 규칙.

여기서 만든 결과는 일반 이동 계획과 동일한 {src: {"dst", "reason", "confidence", "source"}}
형태이므로, organizer.validate_assignments -> file_ops.build_move_plan/apply_move_plan을
그대로 재사용한다. 즉 이름 변경도 경로 안전성 검사, 덮어쓰기 금지, 실패 시 자동 롤백,
버전 기록/되돌리기 혜택을 동일하게 받는다(이름 변경은 "같은 폴더로의 이동"과 같다).
"""

import os
import re
from collections import defaultdict

from app.scanner import FileEntry

MODE_FIND_REPLACE = "find_replace"
MODE_PREFIX = "prefix"
MODE_SUFFIX = "suffix"
MODE_NUMBERING = "numbering"

MODES = (MODE_FIND_REPLACE, MODE_PREFIX, MODE_SUFFIX, MODE_NUMBERING)

# "복사본"류 접미사만 지운다 — "_v2"/"_final"/"_초안"처럼 서로 다른 파일을 구분하는
# 의미 있는 버전 표시는 건드리지 않는다(지우면 서로 다른 문서가 같은 이름이 될 수 있음).
_COPY_SUFFIX_PATTERNS = [
    re.compile(r"\s*\(\d+\)\s*$"),
    re.compile(r"[ _-]*복사본\s*$", re.IGNORECASE),
    re.compile(r"[ _-]*사본\s*$", re.IGNORECASE),
    re.compile(r"[ _-]*[Cc]opy\s*\d*\s*$"),
]


def _clean_stem(stem: str) -> str:
    cleaned = stem
    changed = True
    while changed:
        changed = False
        for pat in _COPY_SUFFIX_PATTERNS:
            new = pat.sub("", cleaned)
            if new != cleaned:
                cleaned = new
                changed = True
    cleaned = re.sub(r"[ _]{2,}", "_", cleaned).strip(" _-")
    return cleaned or stem


def suggest_clean_names(entries: list[FileEntry]) -> dict[str, str]:
    """"(1)", "복사본", "사본", "copy" 같은 의미 없는 복사 흔적만 제거한 정리된 이름을
    제안한다. {relative_path: 제안하는 새 파일명} — 바뀌는 파일만 포함한다.

    정리한 이름이 같은 폴더의 다른 파일과 겹치면(원본이든 다른 제안이든) 그 파일은
    건드리지 않고 원래 이름을 유지한다 — 이름 충돌로 서로 다른 문서가 뒤섞이지 않도록.
    """
    taken_by_dir: dict[str, set[str]] = defaultdict(set)
    for e in entries:
        folder = os.path.dirname(e.relative_path.replace("\\", "/"))
        taken_by_dir[folder].add(e.name.casefold())

    suggestions: dict[str, str] = {}
    for e in sorted(entries, key=lambda e: e.relative_path):
        folder = os.path.dirname(e.relative_path.replace("\\", "/"))
        stem, ext = os.path.splitext(e.name)
        new_name = f"{_clean_stem(stem)}{ext}"
        if new_name == e.name:
            continue
        key = new_name.casefold()
        if key in taken_by_dir[folder] and key != e.name.casefold():
            continue  # 정리하면 같은 폴더의 다른 파일과 이름이 겹친다 — 건드리지 않는다
        suggestions[e.relative_path] = new_name
        taken_by_dir[folder].discard(e.name.casefold())
        taken_by_dir[folder].add(key)
    return suggestions


def build_suggested_rename_assignments(entries: list[FileEntry]) -> dict[str, dict]:
    """suggest_clean_names 결과를 이동 계획용 assignments 형태로 만든다."""
    suggestions = suggest_clean_names(entries)
    result = {}
    for rel_path, new_name in suggestions.items():
        folder = os.path.dirname(rel_path.replace("\\", "/"))
        dst = f"{folder}/{new_name}" if folder else new_name
        result[rel_path] = {
            "dst": dst,
            "reason": "복사본/사본 표시 등 불필요한 이름 흔적 제거",
            "confidence": "보통",
            "source": "rename_suggest",
        }
    return result


def _new_stem(stem: str, rule: dict) -> str:
    mode = rule.get("mode")
    if mode == MODE_FIND_REPLACE:
        find = rule.get("find", "")
        replace = rule.get("replace", "")
        return stem.replace(find, replace) if find else stem
    if mode == MODE_PREFIX:
        return f"{rule.get('text', '')}{stem}"
    if mode == MODE_SUFFIX:
        return f"{stem}{rule.get('text', '')}"
    raise ValueError(f"이 모드는 파일 단위 변환이 아닙니다: {mode}")


def preview_rename(entries: list[FileEntry], rule: dict) -> list[dict]:
    """실제로 적용하지 않고 {src, old_name, new_name, dst} 미리보기 목록만 만든다."""
    mode = rule.get("mode")
    if mode not in MODES:
        raise ValueError(f"알 수 없는 이름 변경 모드: {mode}")

    ordered = sorted(entries, key=lambda e: e.relative_path)
    rows = []
    for i, entry in enumerate(ordered, start=1):
        folder = os.path.dirname(entry.relative_path.replace("\\", "/"))
        stem, ext = os.path.splitext(entry.name)

        if mode == MODE_NUMBERING:
            base = rule.get("base_name") or stem
            digits = max(1, int(rule.get("digits", 3)))
            start = int(rule.get("start", 1))
            new_stem = f"{base}_{start + i - 1:0{digits}d}"
        else:
            new_stem = _new_stem(stem, rule)

        new_name = f"{new_stem}{ext}"
        dst = f"{folder}/{new_name}" if folder else new_name
        rows.append(
            {
                "src": entry.relative_path,
                "old_name": entry.name,
                "new_name": new_name,
                "dst": dst,
                "changed": new_name != entry.name,
            }
        )
    return rows


def build_rename_assignments(entries: list[FileEntry], rule: dict) -> dict[str, dict]:
    """변경되는 파일만 골라 이동 계획용 assignments 형태로 만든다."""
    rows = preview_rename(entries, rule)
    return {
        row["src"]: {
            "dst": row["dst"],
            "reason": "파일명 일괄 변경 규칙 적용",
            "confidence": "높음",
            "source": "rename",
        }
        for row in rows
        if row["changed"]
    }
