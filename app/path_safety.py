"""이동 목적지 경로의 안전성 검증.

LLM이 반환한 목적지 문자열은 신뢰하지 않고, 대상 폴더(root) 밖으로 나가거나
운영체제에서 유효하지 않은 경로가 되지 않는지 여기서 검사한다.
"""

import os
import re

RESERVED_NAMES = {"CON", "PRN", "AUX", "NUL"} | {f"COM{i}" for i in range(1, 10)} | {
    f"LPT{i}" for i in range(1, 10)
}
ILLEGAL_CHARS_RE = re.compile(r'[<>:"|?*\x00-\x1f]')
MAX_PATH_LEN = 240


def validate_rel_dst(rel_dst: str) -> tuple[bool, str]:
    """상대 목적지 경로 문자열 자체의 형식을 검사한다(존재 여부와 무관)."""
    if not rel_dst:
        return False, "목적지 경로가 비어 있습니다."
    if os.path.isabs(rel_dst) or (len(rel_dst) >= 2 and rel_dst[1] == ":"):
        return False, "절대경로는 목적지로 사용할 수 없습니다."

    normalized = rel_dst.replace("\\", "/")
    segments = [seg for seg in normalized.split("/") if seg != ""]
    if not segments:
        return False, "목적지 경로가 비어 있습니다."

    for seg in segments:
        if seg in ("..", "."):
            return False, "상위 경로(..)를 포함한 목적지는 허용되지 않습니다."
        if ILLEGAL_CHARS_RE.search(seg):
            return False, f"목적지 이름에 사용할 수 없는 문자가 있습니다: {seg}"
        if seg != seg.rstrip(" ."):
            return False, f"이름 끝에 공백이나 마침표를 사용할 수 없습니다: {seg}"
        stem = seg.split(".")[0].upper()
        if stem in RESERVED_NAMES:
            return False, f"운영체제 예약어는 폴더/파일 이름으로 사용할 수 없습니다: {seg}"

    return True, ""


def is_within_root(root: str, path: str) -> bool:
    """path가 realpath 기준으로 root 내부에 있는지 확인한다(심볼릭 링크 탈출 포함 차단)."""
    real_root = os.path.realpath(root)
    real_path = os.path.realpath(path)
    if real_path == real_root:
        return False
    try:
        common = os.path.commonpath([real_root, real_path])
    except ValueError:
        return False
    return common == real_root


def is_safe_destination(root: str, rel_dst: str) -> tuple[bool, str]:
    """목적지 상대경로가 root 내부의 유효한 경로인지 종합 검사한다."""
    ok, reason = validate_rel_dst(rel_dst)
    if not ok:
        return False, reason

    dst = os.path.join(os.path.abspath(root), rel_dst)
    if not is_within_root(root, dst):
        return False, "대상 폴더 밖으로 나가는 경로는 허용되지 않습니다."
    if len(dst) > MAX_PATH_LEN:
        return False, f"경로 길이가 너무 깁니다({len(dst)}자, 최대 {MAX_PATH_LEN}자)."
    return True, ""
