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


def test_recommended_models_marks_installed_models(client, monkeypatch):
    monkeypatch.setattr(
        llm_client,
        "list_installed_models",
        lambda *a, **k: [{"name": llm_client.DEFAULT_MODEL, "size_mb": 1600, "parameter_size": "", "quantization": ""}],
    )

    resp = client.get("/api/models/recommended")

    assert resp.status_code == 200
    data = resp.json()
    names = {m["name"]: m["installed"] for m in data}
    assert names[llm_client.DEFAULT_MODEL] is True
    assert any(not v for k, v in names.items() if k != llm_client.DEFAULT_MODEL)


def test_pull_model_streams_progress_lines(client, monkeypatch):
    def fake_stream(model, base_url=llm_client.OLLAMA_BASE_URL):
        assert model == "qwen2.5:1.5b"
        yield '{"status": "pulling manifest"}'
        yield '{"status": "downloading", "total": 100, "completed": 50}'
        yield '{"status": "success"}'

    monkeypatch.setattr(llm_client, "pull_model_stream", fake_stream)

    resp = client.post("/api/models/pull", json={"model": "qwen2.5:1.5b"})

    assert resp.status_code == 200
    lines = [line for line in resp.text.strip().split("\n") if line]
    assert len(lines) == 3
    assert lines[-1] == '{"status": "success"}'
