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

    def apply_once():
        classify = client.post(
            "/api/classify",
            json={"entries": entries, "template": template, "model": "unused", "use_ai": False},
        ).json()
        validate = client.post(
            "/api/assignments/validate",
            json={"entries": entries, "root": sample_folder, "assignments": classify["assignments"]},
        ).json()
        return client.post(
            "/api/apply",
            json={"root": sample_folder, "assignments": validate["merged"], "entries": entries},
        ).json()

    first = apply_once()
    # 두 번째 적용은 이미 옮겨진 파일이라 계획이 비어 있을 수 있으므로, 버전 자체는
    # record_version이 항상 새로 기록한다는 점만 확인하면 충분하다.
    second = apply_once()
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
