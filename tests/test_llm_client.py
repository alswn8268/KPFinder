import pytest

from app import llm_client
from app.llm_client import OllamaError, _parse_json_response, normalize_assignments


def test_normalize_assignments_handles_dict_form():
    raw = {"a.txt": {"dst": "보고서/a.txt", "reason": "영업 실적 문서", "confidence": "높음"}}
    result = normalize_assignments(raw)
    assert result["a.txt"] == {
        "dst": "보고서/a.txt",
        "reason": "영업 실적 문서",
        "confidence": "높음",
        "source": "ai",
    }


def test_normalize_assignments_handles_legacy_string_form():
    raw = {"a.txt": "보고서/a.txt"}
    result = normalize_assignments(raw)
    assert result["a.txt"]["dst"] == "보고서/a.txt"
    assert result["a.txt"]["confidence"] == "보통"


def test_normalize_assignments_defaults_invalid_confidence():
    raw = {"a.txt": {"dst": "보고서/a.txt", "confidence": "알수없음"}}
    result = normalize_assignments(raw)
    assert result["a.txt"]["confidence"] == "보통"


def test_normalize_assignments_skips_unusable_values():
    raw = {"a.txt": 12345}
    assert normalize_assignments(raw) == {}


def test_parse_json_response_repairs_unescaped_windows_backslash():
    # 실제 Ollama 리허설에서 재현된 응답: 모델이 "backup_old\사내_정책.txt" 같은 상대경로를
    # JSON 문자열 안에 그대로 베껴 쓰면서 백슬래시를 이스케이프하지 않았다.
    content = (
        '```json\n{"categories": ["03_재무·회계"], '
        '"assignments": {"backup_old\\사내_보안_정책_v3.txt": '
        '{"dst": "03_재무·회계/사내_보안_정책_v3.txt", "reason": "사내 정책 문서", "confidence": "높음"}}, '
        '"notes": "정리 완료"}\n```'
    )
    result = _parse_json_response(content)
    assert "backup_old\\사내_보안_정책_v3.txt" in result["assignments"]


def test_parse_json_response_still_raises_on_genuinely_broken_json():
    with pytest.raises(OllamaError):
        _parse_json_response("이건 JSON이 아예 아님")


def test_propose_folder_structure_uses_generous_structure_timeout(monkeypatch):
    # 실기 리허설에서 파일 10개짜리 구조 제안 호출이 258초 걸려 기존 180초 고정값으로는
    # 부족했던 것을 재현 방지하는 회귀 테스트 — chat()에 실제로 넘어가는 timeout을 가로채서 확인한다.
    captured = {}

    def fake_post(url, json=None, timeout=None):
        captured["timeout"] = timeout

        class FakeResponse:
            def raise_for_status(self):
                pass

            def json(self):
                return {"message": {"content": '{"categories": [], "assignments": {}, "notes": ""}'}}

        return FakeResponse()

    monkeypatch.setattr(llm_client.requests, "post", fake_post)

    llm_client.propose_folder_structure([{"relative_path": "a.txt", "ext": ".txt", "summary": "x"}])

    assert captured["timeout"] == llm_client.STRUCTURE_TIMEOUT
    assert captured["timeout"] > 180  # 실기에서 부족했던 옛 하드코딩 값보다 커야 한다


def test_list_installed_models_sorts_by_size_ascending(monkeypatch):
    # 사양이 낮은 PC 사용자가 목록의 첫 항목만 봐도 가장 가벼운 모델을 고를 수 있어야 한다.
    def fake_get(url, timeout=None):
        class FakeResponse:
            def raise_for_status(self):
                pass

            def json(self):
                return {
                    "models": [
                        {
                            "name": "big-model:7b",
                            "size_mb": 0,
                            "size": 7_000 * 1024 * 1024,
                            "details": {"parameter_size": "7B", "quantization_level": "Q4_K_M"},
                        },
                        {
                            "name": "exaone3.5:2.4b",
                            "size": 1569 * 1024 * 1024,
                            "details": {"parameter_size": "2.7B", "quantization_level": "Q4_K_M"},
                        },
                    ]
                }

        return FakeResponse()

    monkeypatch.setattr(llm_client.requests, "get", fake_get)

    models = llm_client.list_installed_models()

    assert [m["name"] for m in models] == ["exaone3.5:2.4b", "big-model:7b"]
    assert models[0]["size_mb"] == 1569
    assert models[0]["parameter_size"] == "2.7B"


def test_list_installed_models_returns_empty_list_when_ollama_unreachable(monkeypatch):
    def fake_get(url, timeout=None):
        raise llm_client.requests.ConnectionError("연결 실패")

    monkeypatch.setattr(llm_client.requests, "get", fake_get)

    assert llm_client.list_installed_models() == []


def test_list_recommended_models_flags_which_are_already_installed(monkeypatch):
    monkeypatch.setattr(
        llm_client,
        "list_installed_models",
        lambda base_url=llm_client.OLLAMA_BASE_URL: [
            {"name": llm_client.DEFAULT_MODEL, "size_mb": 1600, "parameter_size": "", "quantization": ""}
        ],
    )

    recommended = llm_client.list_recommended_models()

    by_name = {m["name"]: m["installed"] for m in recommended}
    assert by_name[llm_client.DEFAULT_MODEL] is True
    assert any(installed is False for name, installed in by_name.items() if name != llm_client.DEFAULT_MODEL)
    # 추천 목록은 항상 용량 오름차순으로 정의돼 있어야 사양 낮은 사용자가 첫 항목만 봐도 된다.
    sizes = [m["size_gb"] for m in recommended]
    assert sizes == sorted(sizes)


def test_pull_model_stream_yields_ollama_progress_lines(monkeypatch):
    class FakeResponse:
        def raise_for_status(self):
            pass

        def iter_lines(self):
            yield b'{"status": "pulling manifest"}'
            yield b""  # Ollama가 종종 빈 줄도 섞어 보낸다 — 건너뛰어야 한다
            yield b'{"status": "success"}'

    captured = {}

    def fake_post(url, json=None, stream=None, timeout=None):
        captured["url"] = url
        captured["json"] = json
        captured["stream"] = stream
        return FakeResponse()

    monkeypatch.setattr(llm_client.requests, "post", fake_post)

    lines = list(llm_client.pull_model_stream("qwen2.5:1.5b"))

    assert lines == ['{"status": "pulling manifest"}', '{"status": "success"}']
    assert captured["json"] == {"name": "qwen2.5:1.5b", "stream": True}
    assert captured["stream"] is True
    assert captured["url"].endswith("/api/pull")


def test_propose_folder_structure_timeout_is_overridable(monkeypatch):
    captured = {}

    def fake_post(url, json=None, timeout=None):
        captured["timeout"] = timeout

        class FakeResponse:
            def raise_for_status(self):
                pass

            def json(self):
                return {"message": {"content": "{}"}}

        return FakeResponse()

    monkeypatch.setattr(llm_client.requests, "post", fake_post)

    llm_client.propose_folder_structure(
        [{"relative_path": "a.txt", "ext": ".txt", "summary": "x"}], timeout=45
    )

    assert captured["timeout"] == 45
