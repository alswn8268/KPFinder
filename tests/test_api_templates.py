def test_default_template(client):
    resp = client.get("/api/templates/default")
    assert resp.status_code == 200
    data = resp.json()
    assert "99_미분류" in [f["path"] for f in data["folders"]]


def test_sample_templates_cover_dev_ops_finance(client):
    resp = client.get("/api/templates/samples")
    assert resp.status_code == 200
    data = resp.json()
    names = {t["name"] for t in data}
    assert names == {"개발팀 표준 템플릿", "운영팀 표준 템플릿", "회계팀 표준 템플릿"}
    for t in data:
        assert "99_미분류" in [f["path"] for f in t["folders"]]
        assert len(t["keyword_rules"]) > 0


def test_import_export_round_trip(client):
    default = client.get("/api/templates/default").json()
    exported = client.post("/api/templates/export", json=default)
    assert exported.status_code == 200

    imported = client.post("/api/templates/import", json={"json_text": exported.text})
    assert imported.status_code == 200
    assert imported.json()["name"] == default["name"]


def test_import_rejects_invalid_json(client):
    resp = client.post("/api/templates/import", json={"json_text": "이건 json이 아님"})
    assert resp.status_code == 400


def test_from_folder_list_creates_template(client):
    resp = client.post(
        "/api/templates/from-folder-list",
        json={"text": "01_경영지원\n영업/실적", "name": "내 템플릿"},
    )
    assert resp.status_code == 200
    paths = [f["path"] for f in resp.json()["folders"]]
    assert "01_경영지원" in paths
    assert "영업/실적" in paths


def test_from_folder_list_rejects_empty(client):
    resp = client.post("/api/templates/from-folder-list", json={"text": "   ", "name": "빈 템플릿"})
    assert resp.status_code == 400


def test_from_current_structure(client):
    entries = [
        {
            "path": "x",
            "relative_path": "영업/보고서.txt",
            "name": "보고서.txt",
            "ext": ".txt",
            "size": 1,
            "modified": "2026-01-01T00:00:00",
        }
    ]
    resp = client.post(
        "/api/templates/from-current-structure", json={"entries": entries, "name": "현재 구조"}
    )
    assert resp.status_code == 200
    assert "영업" in [f["path"] for f in resp.json()["folders"]]


def test_save_and_list_templates(client):
    default = client.get("/api/templates/default").json()
    default["name"] = "저장 테스트 템플릿"
    save_resp = client.post("/api/templates/save", json={"template": default})
    assert save_resp.status_code == 200

    listed = client.get("/api/templates").json()
    assert any(t["name"] == "저장 테스트 템플릿" for t in listed)


def _summarized_entry(rel_path: str, summary: str = "요약 내용") -> dict:
    return {
        "path": rel_path,
        "relative_path": rel_path,
        "name": rel_path,
        "ext": ".txt",
        "size": 1,
        "modified": "2026-01-01T00:00:00",
        "summary": summary,
        "summary_status": "ok",
    }


def test_suggest_structure_returns_ai_proposal_without_allowed_folders(client, monkeypatch):
    from app import llm_client

    def fake_propose(file_entries, model, allowed_folders=None, user_hint=None, timeout=None):
        assert allowed_folders is None
        assert user_hint == "부서별로 나눠줘"
        return {
            "categories": ["영업", "마케팅"],
            "assignments": {
                "문서.txt": {"dst": "영업/문서.txt", "reason": "영업 관련 문서", "confidence": "높음"}
            },
            "notes": "제안 완료",
        }

    monkeypatch.setattr(llm_client, "propose_folder_structure", fake_propose)

    resp = client.post(
        "/api/templates/suggest",
        json={"entries": [_summarized_entry("문서.txt")], "model": "unused", "hint": "부서별로 나눠줘"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["categories"] == ["영업", "마케팅"]
    assert data["assignments"]["문서.txt"]["dst"] == "영업/문서.txt"
    assert data["notes"] == "제안 완료"


def test_suggest_structure_returns_guidance_when_nothing_summarized(client):
    unsummarized = {
        "path": "문서.txt",
        "relative_path": "문서.txt",
        "name": "문서.txt",
        "ext": ".txt",
        "size": 1,
        "modified": "2026-01-01T00:00:00",
    }
    resp = client.post("/api/templates/suggest", json={"entries": [unsummarized], "model": "unused"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["categories"] == []
    assert "요약" in data["notes"]


def test_suggest_structure_returns_502_on_ollama_error(client, monkeypatch):
    from app import llm_client

    def fake_propose(*args, **kwargs):
        raise llm_client.OllamaError("연결 실패")

    monkeypatch.setattr(llm_client, "propose_folder_structure", fake_propose)

    resp = client.post(
        "/api/templates/suggest", json={"entries": [_summarized_entry("문서.txt")], "model": "unused"}
    )
    assert resp.status_code == 502


def test_from_ai_proposal_creates_template(client):
    resp = client.post(
        "/api/templates/from-ai-proposal",
        json={"categories": ["영업", "영업", "마케팅", ""], "name": "AI 제안 템플릿"},
    )
    assert resp.status_code == 200
    paths = [f["path"] for f in resp.json()["folders"]]
    assert paths.count("영업") == 1
    assert "마케팅" in paths
    assert "99_미분류" in paths


def test_from_ai_proposal_rejects_empty_categories(client):
    resp = client.post("/api/templates/from-ai-proposal", json={"categories": [], "name": "빈 템플릿"})
    assert resp.status_code == 400
