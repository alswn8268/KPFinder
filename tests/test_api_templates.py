def test_default_template(client):
    resp = client.get("/api/templates/default")
    assert resp.status_code == 200
    data = resp.json()
    assert "99_미분류" in [f["path"] for f in data["folders"]]


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
