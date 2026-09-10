"""matplotlib 그래프에서 한글 라벨이 깨지지 않도록 폰트를 설정하는 공용 유틸.

일반 사무용 PC(주로 Windows)에는 맑은 고딕이 기본 설치되어 있다는 가정 하에
후보 폰트 목록에서 설치된 것을 찾아 적용한다. 하나도 없으면 기본 폰트를 쓰고,
그 경우 한글 라벨이 네모(□)로 보일 수 있다(README에 알려진 제한사항으로 기록).
"""

import matplotlib

matplotlib.use("Agg")
from matplotlib import font_manager

_CANDIDATE_FONTS = [
    "Malgun Gothic",  # Windows 기본 한글 폰트
    "AppleGothic",  # macOS 기본 한글 폰트
    "NanumGothic",  # Linux에 흔히 설치되는 한글 폰트
    "Noto Sans CJK KR",
    "Noto Sans KR",
]

_cache: dict = {}


def apply_korean_font() -> str | None:
    if "font" not in _cache:
        available = {f.name for f in font_manager.fontManager.ttflist}
        _cache["font"] = next((name for name in _CANDIDATE_FONTS if name in available), None)
    font_name = _cache["font"]
    if font_name:
        matplotlib.rcParams["font.family"] = font_name
    matplotlib.rcParams["axes.unicode_minus"] = False
    return font_name
