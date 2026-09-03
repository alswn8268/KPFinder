from app import env_check


def test_check_environment_never_raises_and_returns_items(tmp_path):
    items = env_check.check_environment(root=str(tmp_path))
    assert isinstance(items, list)
    assert all({"item", "status", "detail", "action"} <= set(i.keys()) for i in items)
    names = {i["item"] for i in items}
    assert "Ollama 실행 여부" in names
    assert "필수 라이브러리" in names


def test_check_environment_reports_missing_folder():
    items = env_check.check_environment(root="C:/definitely/not/a/real/path/xyz")
    folder_item = next(i for i in items if i["item"] == "대상 폴더 읽기 권한")
    assert folder_item["status"] == "오류"
    assert folder_item["action"]


def test_has_blocking_error_ignores_ai_only_failures():
    items = [
        {"item": "Ollama 실행 여부", "status": "오류", "detail": "", "action": ""},
        {"item": "AI 모델 설치 여부", "status": "오류", "detail": "", "action": ""},
        {"item": "필수 라이브러리", "status": "정상", "detail": "", "action": ""},
    ]
    assert env_check.has_blocking_error(items) is False


def test_has_blocking_error_true_for_non_ai_error():
    items = [
        {"item": "대상 폴더 읽기 권한", "status": "오류", "detail": "", "action": ""},
    ]
    assert env_check.has_blocking_error(items) is True
