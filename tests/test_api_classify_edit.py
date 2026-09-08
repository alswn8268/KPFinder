def _scan(client, root):
    resp = client.post("/api/scan", json={"root": root})
    assert resp.status_code == 200
    return resp.json()["entries"]


def test_classify_without_ai_uses_rules_only(client, sample_folder):
    entries = _scan(client, sample_folder)
    template = client.get("/api/templates/default").json()

    resp = client.post(
        "/api/classify",
        json={"entries": entries, "template": template, "model": "unused", "use_ai": False},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["ai_failed"] is False
    assignments = data["assignments"]
    assert "회의록_0212.txt" in assignments
    assert assignments["회의록_0212.txt"]["dst"].startswith("08_회의록/")
    assert assignments["회의록_0212.txt"]["source"] == "rule"
    # 규칙에 안 걸리고 AI도 꺼져 있으면 강제로 미분류 처리하지 않는다.
    assert "이상한파일.txt" not in assignments


def test_validate_rejects_path_traversal(client, sample_folder):
    entries = _scan(client, sample_folder)
    src = entries[0]["relative_path"]

    resp = client.post(
        "/api/assignments/validate",
        json={
            "entries": entries,
            "root": sample_folder,
            "assignments": {src: {"dst": "../outside.txt", "confidence": "높음"}},
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["valid"] == {}
    assert data["rejected"][0]["src"] == src


def test_validate_applies_user_override_and_excludes(client, sample_folder):
    entries = _scan(client, sample_folder)
    template = client.get("/api/templates/default").json()
    classify = client.post(
        "/api/classify",
        json={"entries": entries, "template": template, "model": "unused", "use_ai": False},
    ).json()

    src = "회의록_0212.txt"
    overrides = {src: {"dst": "99_미분류/따로.txt", "excluded": False}}
    resp = client.post(
        "/api/assignments/validate",
        json={
            "entries": entries,
            "root": sample_folder,
            "assignments": classify["assignments"],
            "overrides": overrides,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["merged"][src]["dst"] == "99_미분류/따로.txt"
    assert data["merged"][src]["source"] == "user"

    excluded_resp = client.post(
        "/api/assignments/validate",
        json={
            "entries": entries,
            "root": sample_folder,
            "assignments": classify["assignments"],
            "overrides": {src: {"excluded": True}},
        },
    )
    excluded_data = excluded_resp.json()
    assert src in excluded_data["excluded"]
    assert src not in excluded_data["merged"]

    final_by_path = {row["경로"]: row["상태"] for row in excluded_data["final_state"]}
    assert final_by_path[src] == "제외"
