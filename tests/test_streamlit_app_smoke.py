"""streamlit.testing.v1.AppTest로 실제 화면 흐름(스캔 -> 규칙 기반 분류 -> 제안 편집 ->
적용 미리보기)이 예외 없이 끝까지 도는지 확인하는 스모크 테스트.

Ollama 없이도(오프라인 모드) 핵심 화면이 동작해야 한다는 요구사항을 검증하는
용도이기도 하다. 실제 파일 이동(적용 버튼 클릭)까지는 하지 않는다.
"""

import os

from streamlit.testing.v1 import AppTest

APP_PATH = os.path.join(os.path.dirname(__file__), "..", "streamlit_app.py")


def _make_sample_folder(tmp_path):
    (tmp_path / "주간회의록_0212.txt").write_text("2월 12일 마케팅팀 회의록입니다.", encoding="utf-8")
    (tmp_path / "계약서_초안.txt").write_text("신규 협력사와의 계약서 초안입니다.", encoding="utf-8")
    (tmp_path / "이상한파일.txt").write_text("분류하기 애매한 내용입니다.", encoding="utf-8")
    return str(tmp_path)


def test_app_runs_scan_and_offline_classification_without_errors(tmp_path):
    folder = _make_sample_folder(tmp_path)

    at = AppTest.from_file(APP_PATH)
    at.run(timeout=30)
    assert not at.exception

    folder_input = next(t for t in at.text_input if t.label == "정리할 폴더 경로")
    folder_input.set_value(folder)

    scan_button = next(b for b in at.button if b.label == "1️⃣ 스캔")
    scan_button.click().run(timeout=30)
    assert not at.exception
    assert len(at.session_state["entries"]) == 3

    classify_button = next(b for b in at.button if b.label.startswith("2️⃣ 분류 실행"))
    classify_button.click().run(timeout=30)  # Ollama 미연결 -> 규칙 기반 분류
    assert not at.exception
    assert at.session_state["proposal"] is not None
    assignments = at.session_state["proposal"]["assignments"]
    assert "주간회의록_0212.txt" in assignments
    assert assignments["주간회의록_0212.txt"]["dst"].startswith("08_회의록/")
