from app import llm_client


def test_models_endpoint_reports_disconnected_when_ollama_down(client, monkeypatch):
    monkeypatch.setattr(llm_client, "check_connection", lambda *a, **k: False)

    resp = client.get("/api/models")

    assert resp.status_code == 200
    data = resp.json()
    assert data == {"connected": False, "models": []}


def test_models_endpoint_lists_installed_models_when_connected(client, monkeypatch):
    monkeypatch.setattr(llm_client, "check_connection", lambda *a, **k: True)
    monkeypatch.setattr(
        llm_client,
        "list_installed_models",
        lambda *a, **k: [
            {"name": "exaone3.5:2.4b", "size_mb": 1569, "parameter_size": "2.7B", "quantization": "Q4_K_M"}
        ],
    )

    resp = client.get("/api/models")

    assert resp.status_code == 200
    data = resp.json()
    assert data["connected"] is True
    assert data["models"] == [
        {"name": "exaone3.5:2.4b", "size_mb": 1569, "parameter_size": "2.7B", "quantization": "Q4_K_M"}
    ]
