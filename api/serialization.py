"""app.scanner.FileEntry(데이터클래스) <-> API 스키마 사이의 왕복 변환.

필드명은 FileEntry와 1:1로 맞춰야 한다(드리프트 나면 API가 조용히 필드를 잃는다) —
tests/test_api_serialization.py에서 이 계약을 직접 검증한다.
"""

import dataclasses

from app.scanner import FileEntry
from app.templates import OrgTemplate
from api.schemas import FileEntryModel, TemplateModel


def entry_to_model(entry: FileEntry) -> FileEntryModel:
    return FileEntryModel(**dataclasses.asdict(entry))


def model_to_entry(model: FileEntryModel) -> FileEntry:
    return FileEntry(**model.model_dump())


def entries_to_models(entries: list[FileEntry]) -> list[FileEntryModel]:
    return [entry_to_model(e) for e in entries]


def models_to_entries(models: list[FileEntryModel]) -> list[FileEntry]:
    return [model_to_entry(m) for m in models]


def template_to_model(template: OrgTemplate) -> TemplateModel:
    return TemplateModel(**template.to_dict())


def model_to_template(model: TemplateModel) -> OrgTemplate:
    return OrgTemplate.from_dict(model.model_dump())
