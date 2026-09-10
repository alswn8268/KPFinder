import os

from sample_data.generate_sample_data import DATASETS


def test_generate_creates_files_in_requested_dir(client, tmp_path):
    out_dir = str(tmp_path / "demo")
    resp = client.post("/api/sample-data/generate", json={"output_dir": out_dir})
    assert resp.status_code == 200
    data = resp.json()
    assert data["output_dir"] == out_dir
    assert data["created_count"] > 0
    assert data["already_existed"] is False
    assert os.path.isdir(out_dir)
    assert len(os.listdir(out_dir)) > 0


def test_generate_does_not_overwrite_without_force(client, tmp_path):
    out_dir = str(tmp_path / "demo")
    client.post("/api/sample-data/generate", json={"output_dir": out_dir})
    marker = os.path.join(out_dir, "내가_추가한_파일.txt")
    with open(marker, "w", encoding="utf-8") as f:
        f.write("건드리면 안 됨")

    resp = client.post("/api/sample-data/generate", json={"output_dir": out_dir})
    data = resp.json()
    assert data["already_existed"] is True
    assert data["created_count"] == 0
    assert os.path.exists(marker)  # 덮어쓰지 않았으므로 그대로 남아 있어야 한다


def test_generate_with_force_overwrites(client, tmp_path):
    out_dir = str(tmp_path / "demo")
    client.post("/api/sample-data/generate", json={"output_dir": out_dir})
    marker = os.path.join(out_dir, "내가_추가한_파일.txt")
    with open(marker, "w", encoding="utf-8") as f:
        f.write("사라져야 함")

    resp = client.post("/api/sample-data/generate", json={"output_dir": out_dir, "force": True})
    data = resp.json()
    assert data["already_existed"] is False
    assert data["created_count"] > 0
    assert not os.path.exists(marker)  # force=True라 폴더가 통째로 다시 생성됨


def test_list_datasets_returns_all_registered_scenarios(client):
    resp = client.get("/api/sample-data/datasets")
    assert resp.status_code == 200
    data = resp.json()
    keys = {d["key"] for d in data}
    assert keys == set(DATASETS.keys())
    for d in data:
        assert d["label"]
        assert d["output_dir"]


def test_generate_accepts_department_dataset(client, tmp_path):
    out_dir = str(tmp_path / "dev_demo")
    resp = client.post(
        "/api/sample-data/generate", json={"output_dir": out_dir, "dataset": "dev_team"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["dataset"] == "dev_team"
    assert data["label"] == DATASETS["dev_team"]["label"]
    assert data["created_count"] > 0
    assert os.path.isdir(out_dir)


def test_generate_rejects_unknown_dataset(client, tmp_path):
    resp = client.post(
        "/api/sample-data/generate",
        json={"output_dir": str(tmp_path / "x"), "dataset": "no_such_team"},
    )
    assert resp.status_code == 400
