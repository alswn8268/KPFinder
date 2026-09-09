def _scan(client, root):
    return client.post("/api/scan", json={"root": root}).json()["entries"]


def test_plan_apply_and_restore_round_trip(client, sample_folder):
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

    plan = client.post(
        "/api/plan", json={"root": sample_folder, "assignments": validate["merged"]}
    ).json()
    assert len(plan["plan"]) == len(validate["merged"])

    apply_resp = client.post(
        "/api/apply",
        json={
            "root": sample_folder,
            "assignments": validate["merged"],
            "entries": entries,
            "note": "test",
        },
    )
    assert apply_resp.status_code == 200
    apply_data = apply_resp.json()
    assert apply_data["moved_count"] == len(plan["plan"])

    import os

    moved_dst = plan["plan"][0]["dst"]
    assert os.path.exists(moved_dst)

    version_id = apply_data["version"]["version_id"]
    restore_resp = client.post(
        f"/api/versions/{version_id}/restore", json={"root": sample_folder}
    )
    assert restore_resp.status_code == 200
    assert restore_resp.json()["restored_count"] == apply_data["moved_count"]
    assert not os.path.exists(moved_dst)


def test_restore_blocked_when_later_version_unrestored(client, sample_folder):
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
    first = client.post(
        "/api/apply",
        json={"root": sample_folder, "assignments": validate["merged"], "entries": entries},
    ).json()
    assert first["moved_count"] > 0

    # 두 번째 버전은 방금 옮겨진 파일을 다른 폴더로 한 번 더 옮겨 만든다(실제로 파일이
    # 이동해야 버전이 기록된다 — 같은 목적지로 재적용하면 0건이라 기록되지 않는다).
    entries_after_first = _scan(client, sample_folder)
    moved_entry = next(
        e for e in entries_after_first if e["relative_path"].replace("\\", "/").startswith("08_회의록/")
    )
    second = client.post(
        "/api/apply",
        json={
            "root": sample_folder,
            "assignments": {moved_entry["relative_path"]: {"dst": f"90_보관/{moved_entry['name']}"}},
            "entries": entries_after_first,
        },
    ).json()
    assert second["moved_count"] > 0
    assert second["version"]["version_id"] != first["version"]["version_id"]

    versions = client.get("/api/versions", params={"root": sample_folder}).json()
    older = next(v for v in versions if v["version_id"] == first["version"]["version_id"])
    assert older["can_restore"] is False
    assert older["restore_blocked_reason"]

    blocked = client.post(
        f"/api/versions/{older['version_id']}/restore", json={"root": sample_folder}
    )
    assert blocked.status_code == 409


def test_restore_unknown_version_404s(client, sample_folder):
    resp = client.post("/api/versions/v999/restore", json={"root": sample_folder})
    assert resp.status_code == 404
