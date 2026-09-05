"""파일명 일괄 변경 규칙.

여기서 만든 결과는 일반 이동 계획과 동일한 {src: {"dst", "reason", "confidence", "source"}}
형태이므로, organizer.validate_assignments -> file_ops.build_move_plan/apply_move_plan을
그대로 재사용한다. 즉 이름 변경도 경로 안전성 검사, 덮어쓰기 금지, 실패 시 자동 롤백,
버전 기록/되돌리기 혜택을 동일하게 받는다(이름 변경은 "같은 폴더로의 이동"과 같다).
"""

import os

from app.scanner import FileEntry

MODE_FIND_REPLACE = "find_replace"
MODE_PREFIX = "prefix"
MODE_SUFFIX = "suffix"
MODE_NUMBERING = "numbering"

MODES = (MODE_FIND_REPLACE, MODE_PREFIX, MODE_SUFFIX, MODE_NUMBERING)


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
