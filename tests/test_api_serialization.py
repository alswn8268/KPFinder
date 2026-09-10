import dataclasses

from app.scanner import FileEntry
from api.schemas import FileEntryModel


def test_file_entry_model_fields_match_dataclass_exactly():
    dataclass_fields = {f.name for f in dataclasses.fields(FileEntry)}
    model_fields = set(FileEntryModel.model_fields)
    assert dataclass_fields == model_fields


def test_file_entry_round_trips_through_model(tmp_path):
    from datetime import datetime

    from api.serialization import entry_to_model, model_to_entry

    original = FileEntry(
        path=str(tmp_path / "a.txt"),
        relative_path="a.txt",
        name="a.txt",
        ext=".txt",
        size=123,
        modified=datetime(2026, 1, 1, 12, 0, 0),
        file_hash="abc",
        summary="요약",
        summary_status="ok",
    )
    model = entry_to_model(original)
    restored = model_to_entry(model)
    assert restored == original
