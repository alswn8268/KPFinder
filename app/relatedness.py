"""파일 간 관계(유사도) 점수 계산.

app.similar(유사 문서 탐지)와 app.content_graph/app.directory_graph(연관도 시각화)가
공유하는 공용 로직이다. 외부 임베딩 모델 없이 표준 라이브러리 difflib만으로
가볍게 계산하며, AI 요약이 아직 없는 파일은 파일명 유사도만으로도 관계를 추정한다.
"""

import difflib
from itertools import combinations

from app.scanner import FileEntry


def _ratio(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    return difflib.SequenceMatcher(None, a, b).ratio()


def score_pair(a: FileEntry, b: FileEntry) -> float:
    """0~1 사이의 관계 점수. AI 요약이 둘 다 있으면 요약 유사도에 더 큰 비중을 둔다."""
    name_ratio = _ratio(a.name, b.name)
    if a.summary_status == "ok" and b.summary_status == "ok" and a.summary and b.summary:
        summary_ratio = _ratio(a.summary, b.summary)
        return round(0.3 * name_ratio + 0.7 * summary_ratio, 4)
    return round(name_ratio, 4)


def build_relatedness_edges(
    entries: list[FileEntry],
    min_score: float = 0.3,
    exclude_exact_duplicates: bool = True,
) -> list[tuple[FileEntry, FileEntry, float]]:
    """점수가 min_score 이상인 파일 쌍만 골라 점수 내림차순으로 반환한다."""
    edges = []
    for a, b in combinations(entries, 2):
        if exclude_exact_duplicates and a.file_hash and b.file_hash and a.file_hash == b.file_hash:
            continue
        score = score_pair(a, b)
        if score >= min_score:
            edges.append((a, b, score))
    edges.sort(key=lambda t: t[2], reverse=True)
    return edges
