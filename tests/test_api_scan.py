import os


def test_scan_returns_entries_and_duplicate_groups(client, tmp_path):
    (tmp_path / "a.txt").write_text("hello", encoding="utf-8")
    (tmp_path / "b.txt").write_text("hello", encoding="utf-8")  # 완전 중복
    (tmp_path / "c.txt").write_text("world", encoding="utf-8")

    resp = client.post("/api/scan", json={"root": str(tmp_path)})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_files"] == 3
    assert len(data["duplicate_groups"]) == 1
    assert len(data["duplicate_groups"][0]["files"]) == 2
    assert data["errors"] == []


def test_scan_rejects_nonexistent_folder(client):
    resp = client.post("/api/scan", json={"root": "C:/definitely/not/a/real/path/xyz"})
    assert resp.status_code == 400


def test_scan_respects_exclude_dirs_and_exts(client, tmp_path):
    (tmp_path / "keep.txt").write_text("x", encoding="utf-8")
    (tmp_path / "skip.log").write_text("x", encoding="utf-8")
    excluded_dir = tmp_path / "node_modules"
    excluded_dir.mkdir()
    (excluded_dir / "inner.txt").write_text("x", encoding="utf-8")

    resp = client.post(
        "/api/scan",
        json={
            "root": str(tmp_path),
            "exclude_dirs": ["node_modules"],
            "exclude_exts": [".log"],
        },
    )
    assert resp.status_code == 200
    paths = {e["relative_path"] for e in resp.json()["entries"]}
    assert paths == {"keep.txt"}


def test_scan_reports_unreadable_files_instead_of_dropping_silently(client, tmp_path, monkeypatch):
    (tmp_path / "a.txt").write_text("x", encoding="utf-8")

    real_stat = os.stat

    def flaky_stat(path, *a, **kw):
        if str(path).endswith("a.txt"):
            raise OSError("permission denied (simulated)")
        return real_stat(path, *a, **kw)

    monkeypatch.setattr(os, "stat", flaky_stat)
    resp = client.post("/api/scan", json={"root": str(tmp_path)})
    assert resp.status_code == 200
    data = resp.json()
    assert data["entries"] == []
    assert len(data["errors"]) == 1
    assert "a.txt" in data["errors"][0]["path"]
