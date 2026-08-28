"""완전 중복은 아니지만 제목/내용이 비슷한 '유사 문서(버전 다른 파일)' 탐지 (P1).

외부 임베딩 모델 없이 표준 라이브러리 difflib만으로 가볍게 판별한다.
파일명 유사도와 AI 요약 유사도를 함께 고려한다.
"""

import difflib
from itertools import combinations

from app.scanner import FileEntry

DEFAULT_THRESHOLD = 0.6


def _ratio(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    return difflib.SequenceMatcher(None, a, b).ratio()


def find_similar_documents(
    entries: list[FileEntry], threshold: float = DEFAULT_THRESHOLD
) -> list[tuple[FileEntry, FileEntry, float]]:
    candidates = [e for e in entries if e.summary_status == "ok" and e.summary]
    results = []
    for a, b in combinations(candidates, 2):
        if a.file_hash and a.file_hash == b.file_hash:
            continue  # 완전 중복은 scanner.find_duplicate_groups()에서 별도 처리
        name_ratio = _ratio(a.name, b.name)
        summary_ratio = _ratio(a.summary, b.summary)
        combined = 0.4 * name_ratio + 0.6 * summary_ratio
        if combined >= threshold:
            results.append((a, b, combined))
    results.sort(key=lambda t: t[2], reverse=True)
    return results
