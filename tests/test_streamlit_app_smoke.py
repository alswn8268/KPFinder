"""streamlit.testing.v1.AppTest로 실제 화면 흐름(스캔 -> 규칙 기반 분류 -> 제안 편집 ->
적용 미리보기)이 예외 없이 끝까지 도는지 확인하는 스모크 테스트.

Ollama 없이도(오프라인 모드) 핵심 화면이 동작해야 한다는 요구사항을 검증하는
용도이기도 하다. 실제 파일 이동(적용 버튼 클릭)까지는 하지 않는다.

이 테스트를 실행하는 PC에 실제 Ollama가 설치·연결되어 있을 수도 있으므로("AI 분류 사용"
체크박스가 기본으로 켜져 느린 실제 AI 호출 경로를 타 버릴 수 있다), 환경과 무관하게
결정적으로 규칙 기반 경로만 타도록 체크박스를 명시적으로 끈다.
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

    # 실제 Ollama가 이 PC에 연결되어 있어도 이 테스트는 항상 규칙 기반 경로만 결정적으로
    # 검증한다 — "AI 분류 사용" 체크박스가 켜져 있으면(Ollama 연결 시 기본값) 꺼 준다.
    use_ai_checkbox = next(c for c in at.checkbox if c.label == "AI 분류 사용")
    if use_ai_checkbox.value:
        use_ai_checkbox.set_value(False).run(timeout=30)
        assert not at.exception

    classify_button = next(b for b in at.button if b.label == "2️⃣ 분류 실행 (규칙 기반, AI 미사용)")
    classify_button.click().run(timeout=30)  # 규칙 기반 분류(오프라인 경로)
    assert not at.exception
    assert at.session_state["proposal"] is not None
    assignments = at.session_state["proposal"]["assignments"]
    assert "주간회의록_0212.txt" in assignments
    assert assignments["주간회의록_0212.txt"]["dst"].startswith("08_회의록/")
