def test_env_check_never_errors(client):
    resp = client.get("/api/env/check")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data["items"], list)
    assert any(i["item"] == "Ollama 실행 여부" for i in data["items"])


def test_cache_lifecycle(client, sample_folder):
    info = client.get("/api/cache/info", params={"root": sample_folder}).json()
    assert info["exists"] is False

    entries = client.post("/api/scan", json={"root": sample_folder}).json()["entries"]
    client.post("/api/summarize", json={"entries": entries, "root": sample_folder, "model": "x"})

    info_after = client.get("/api/cache/info", params={"root": sample_folder}).json()
    assert info_after["exists"] is True
    assert info_after["entry_count"] > 0

    cleared = client.delete("/api/cache/current", params={"root": sample_folder}).json()
    assert cleared["cleared"] is True

    info_final = client.get("/api/cache/info", params={"root": sample_folder}).json()
    assert info_final["exists"] is False


def test_clear_all_caches_reports_count(client, sample_folder):
    entries = client.post("/api/scan", json={"root": sample_folder}).json()["entries"]
    client.post("/api/summarize", json={"entries": entries, "root": sample_folder, "model": "x"})

    resp = client.delete("/api/cache/all")
    assert resp.status_code == 200
    assert resp.json()["cleared_count"] >= 1
