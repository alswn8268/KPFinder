def _scan(client, root):
    return client.post("/api/scan", json={"root": root}).json()["entries"]


def test_rename_preview_shows_old_and_new_names(client, sample_folder):
    entries = _scan(client, sample_folder)
    resp = client.post(
        "/api/rename/preview",
        json={"entries": entries, "rule": {"mode": "prefix", "text": "2026_"}},
    )
    assert resp.status_code == 200
    rows = resp.json()
    changed = [r for r in rows if r["changed"]]
    assert len(changed) == len(entries)
    assert all(r["new_name"].startswith("2026_") for r in changed)


def test_rename_assignments_only_include_changed_files(client, sample_folder):
    entries = _scan(client, sample_folder)
    resp = client.post(
        "/api/rename/assignments",
        json={"entries": entries, "rule": {"mode": "find_replace", "find": "회의록", "replace": "미팅"}},
    )
    assert resp.status_code == 200
    assignments = resp.json()["assignments"]
    assert "회의록_0212.txt" in assignments
    assert "계약서_초안.txt" not in assignments


def test_rename_preview_rejects_unknown_mode(client, sample_folder):
    entries = _scan(client, sample_folder)
    resp = client.post(
        "/api/rename/preview", json={"entries": entries, "rule": {"mode": "not_a_real_mode"}}
    )
    assert resp.status_code == 400


def test_structure_copy_creates_only_folders_no_files(client, tmp_path):
    src = tmp_path / "src"
    (src / "영업" / "실적").mkdir(parents=True)
    (src / "영업" / "실적" / "a.txt").write_text("x", encoding="utf-8")

    entries = _scan(client, str(src))
    dest = tmp_path / "dest"
    resp = client.post("/api/structure/copy", json={"entries": entries, "dest_root": str(dest)})
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] == 2  # 영업, 영업/실적
    assert (dest / "영업" / "실적").is_dir()
    assert not (dest / "영업" / "실적" / "a.txt").exists()  # 폴더만, 파일은 절대 복사하지 않는다
