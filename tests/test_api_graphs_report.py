def _scan(client, root):
    return client.post("/api/scan", json={"root": root}).json()["entries"]


def test_content_graph_returns_nodes(client, sample_folder):
    entries = _scan(client, sample_folder)
    resp = client.post("/api/graphs/content", json={"entries": entries})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["nodes"]) <= len(entries)


def test_content_graph_rejects_too_many_entries(client, sample_folder, monkeypatch):
    import api.routers.graphs as graphs_router

    monkeypatch.setattr(graphs_router, "MAX_NODES_FOR_GRAPH", 1)
    entries = _scan(client, sample_folder)
    resp = client.post("/api/graphs/content", json={"entries": entries})
    assert resp.status_code == 422


def test_directory_tree_has_root_and_children(client, tmp_path):
    (tmp_path / "영업").mkdir()
    (tmp_path / "영업" / "a.txt").write_text("x", encoding="utf-8")
    entries = _scan(client, str(tmp_path))

    resp = client.post("/api/graphs/directory-tree", json={"entries": entries})
    assert resp.status_code == 200
    tree = resp.json()
    assert any(child["id"] == "영업" for child in tree["children"])


def test_directory_relation_returns_graph(client, sample_folder):
    entries = _scan(client, sample_folder)
    resp = client.post("/api/graphs/directory-relation", json={"entries": entries})
    assert resp.status_code == 200


def test_directory_relation_rejects_too_many_entries(client, sample_folder, monkeypatch):
    """content_graph의 /content 엔드포인트와 동일한 크기 가드가 있어야 한다 — 이전에는
    이 엔드포인트에만 가드가 빠져 있어 큰 폴더에서 O(n^2) 계산이 그대로 실행됐다."""
    import api.routers.graphs as graphs_router

    monkeypatch.setattr(graphs_router, "MAX_NODES_FOR_GRAPH", 1)
    entries = _scan(client, sample_folder)
    resp = client.post("/api/graphs/directory-relation", json={"entries": entries})
    assert resp.status_code == 422


def test_report_json_excel_html_all_download(client, sample_folder):
    entries = _scan(client, sample_folder)
    template = client.get("/api/templates/default").json()
    classify = client.post(
        "/api/classify",
        json={"entries": entries, "template": template, "model": "unused", "use_ai": False},
    ).json()
    validate = client.post(
        "/api/assignments/validate",
        json={"entries": entries, "root": sample_folder, "assignments": classify["assignments"]},
    ).json()

    payload = {
        "entries": entries,
        "duplicate_groups": [],
        "proposal": classify,
        "similar_docs": [],
        "final_state": validate["final_state"],
        "env_items": [],
        "model": "unused",
        "template_name": template["name"],
        "template_version": template["version"],
    }

    r_json = client.post("/api/report/json", json=payload)
    assert r_json.status_code == 200
    assert r_json.headers["content-type"].startswith("application/json")
    body = r_json.json()
    assert body["template_name"] == template["name"]

    r_xlsx = client.post("/api/report/excel", json=payload)
    assert r_xlsx.status_code == 200
    assert len(r_xlsx.content) > 0

    r_html = client.post("/api/report/html", json=payload)
    assert r_html.status_code == 200
    assert "<html" in r_html.text.lower()
