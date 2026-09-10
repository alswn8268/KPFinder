"""완전 중복은 아니지만 제목/내용이 비슷한 '유사 문서(버전 다른 파일)' 탐지 (P1).

점수 계산 로직은 app.relatedness에 있으며, 여기서는 AI 요약이 실제로 존재하는
파일들만 후보로 삼고 더 높은 임계값을 적용해 오탐을 줄인다.
"""

from app.relatedness import build_relatedness_edges
from app.scanner import FileEntry

DEFAULT_THRESHOLD = 0.6


def find_similar_documents(
    entries: list[FileEntry], threshold: float = DEFAULT_THRESHOLD
) -> list[tuple[FileEntry, FileEntry, float]]:
    candidates = [e for e in entries if e.summary_status == "ok" and e.summary]
    return build_relatedness_edges(candidates, min_score=threshold, exclude_exact_duplicates=True)
