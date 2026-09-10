"""API 요청/응답 Pydantic 모델. 도메인이 많아 파일 하나에 모아 관리한다."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class FileEntryModel(BaseModel):
    """app.scanner.FileEntry와 필드명이 1:1로 대응해야 한다."""

    path: str
    relative_path: str
    name: str
    ext: str
    size: int
    modified: datetime
    file_hash: str = ""
    summary: str = ""
    summary_status: str = "pending"


class AssignmentInfo(BaseModel):
    dst: str
    reason: str = ""
    confidence: str = "보통"
    source: str = "ai"


class RejectedItem(BaseModel):
    src: str
    dst: str = ""
    reason: str = ""


class OverrideInfo(BaseModel):
    dst: str | None = None
    excluded: bool = False


# ---- 환경 점검 ----


class EnvItemModel(BaseModel):
    item: str
    status: str
    detail: str
    action: str


class EnvCheckResponse(BaseModel):
    items: list[EnvItemModel]
    has_blocking_error: bool


class OllamaModelModel(BaseModel):
    name: str
    size_mb: int
    parameter_size: str
    quantization: str


class ModelsResponse(BaseModel):
    connected: bool
    models: list[OllamaModelModel]


class RecommendedModelModel(BaseModel):
    name: str
    label: str
    tier: str
    size_gb: float
    description: str
    installed: bool


class PullModelRequest(BaseModel):
    model: str


# ---- 템플릿 ----


class TemplateFolderModel(BaseModel):
    path: str
    description: str = ""


class KeywordRuleModel(BaseModel):
    keywords: list[str]
    target: str


class TemplateModel(BaseModel):
    name: str
    version: str = "1.0"
    author: str = ""
    folders: list[TemplateFolderModel] = Field(default_factory=list)
    keyword_rules: list[KeywordRuleModel] = Field(default_factory=list)


class TemplateImportRequest(BaseModel):
    json_text: str


class TemplateSaveRequest(BaseModel):
    template: TemplateModel


class TemplateFromStructureRequest(BaseModel):
    entries: list[FileEntryModel]
    name: str


class TemplateFromListRequest(BaseModel):
    text: str
    name: str
    keep_unclassified: bool = True


class SuggestStructureRequest(BaseModel):
    entries: list[FileEntryModel]
    model: str
    hint: str = ""


class SuggestStructureResponse(BaseModel):
    categories: list[str]
    assignments: dict[str, AssignmentInfo]
    notes: str


class TemplateFromAiProposalRequest(BaseModel):
    categories: list[str]
    name: str


# ---- 스캔 ----


class ScanRequest(BaseModel):
    root: str
    exclude_dirs: list[str] = Field(default_factory=list)
    exclude_exts: list[str] = Field(default_factory=list)
    include_hidden: bool = False
    max_file_size_mb: float | None = None


class ScanErrorItem(BaseModel):
    path: str
    reason: str


class DuplicateGroupModel(BaseModel):
    hash: str
    files: list[FileEntryModel]


class ScanResponse(BaseModel):
    scan_root: str
    entries: list[FileEntryModel]
    duplicate_groups: list[DuplicateGroupModel]
    errors: list[ScanErrorItem]
    total_files: int


# ---- 캐시 ----


class CacheInfoModel(BaseModel):
    exists: bool
    path: str
    entry_count: int
    created_at: str | None
    models_used: list[str]


class ClearCacheResponse(BaseModel):
    cleared: bool


class ClearAllCachesResponse(BaseModel):
    cleared_count: int


# ---- 분류(규칙+AI) ----


class SummarizeRequest(BaseModel):
    entries: list[FileEntryModel]
    root: str
    model: str


class SummarizeResponse(BaseModel):
    entries: list[FileEntryModel]


class ClassifyRequest(BaseModel):
    entries: list[FileEntryModel]
    template: TemplateModel
    model: str
    use_ai: bool = True
    user_rules: list[KeywordRuleModel] = Field(default_factory=list)


class ClassifyResponse(BaseModel):
    categories: list[str]
    assignments: dict[str, AssignmentInfo]
    notes: str
    ai_failed: bool = False
    error_detail: str = ""


class SimilarRequest(BaseModel):
    entries: list[FileEntryModel]


class SimilarPairModel(BaseModel):
    a: str
    b: str
    score: float


# ---- 제안 편집(검증/병합) ----


class ValidateRequest(BaseModel):
    entries: list[FileEntryModel]
    root: str
    assignments: dict[str, AssignmentInfo]
    overrides: dict[str, OverrideInfo] = Field(default_factory=dict)


class ValidateResponse(BaseModel):
    valid: dict[str, AssignmentInfo]
    merged: dict[str, AssignmentInfo]
    rejected: list[RejectedItem]
    excluded: list[str]
    final_state: list[dict[str, str]]
    tree_before: str
    tree_after: str


# ---- 이름 일괄 변경 ----


class RenameRuleModel(BaseModel):
    mode: str
    find: str = ""
    replace: str = ""
    text: str = ""
    base_name: str = ""
    start: int = 1
    digits: int = 3


class RenamePreviewRequest(BaseModel):
    entries: list[FileEntryModel]
    rule: RenameRuleModel


class RenamePreviewRow(BaseModel):
    src: str
    old_name: str
    new_name: str
    dst: str
    changed: bool


class RenameAssignmentsResponse(BaseModel):
    assignments: dict[str, AssignmentInfo]


class RenameSuggestRequest(BaseModel):
    entries: list[FileEntryModel]


# ---- 이동 계획 / 적용 / 되돌리기 ----


class PlanRequest(BaseModel):
    root: str
    assignments: dict[str, AssignmentInfo]


class PlanItem(BaseModel):
    src: str
    dst: str
    rel_src: str
    rel_dst: str


class PlanResponse(BaseModel):
    plan: list[PlanItem]


class ApplyRequest(BaseModel):
    root: str
    assignments: dict[str, AssignmentInfo]
    entries: list[FileEntryModel]
    note: str = ""


class VersionModel(BaseModel):
    version_id: str
    timestamp: str
    note: str
    files_moved: int
    log_path: str
    restored: bool
    can_restore: bool = True
    restore_blocked_reason: str = ""


class ApplyResponse(BaseModel):
    log_path: str
    moved_count: int
    plan_size: int
    version: VersionModel


class RestoreRequest(BaseModel):
    root: str


class RestoreResponse(BaseModel):
    restored_count: int


# ---- 리포트 ----


class ReportRequest(BaseModel):
    entries: list[FileEntryModel]
    duplicate_groups: list[DuplicateGroupModel] = Field(default_factory=list)
    proposal: dict = Field(default_factory=dict)
    similar_docs: list[SimilarPairModel] = Field(default_factory=list)
    final_state: list[dict[str, str]] = Field(default_factory=list)
    env_items: list[EnvItemModel] = Field(default_factory=list)
    model: str = ""
    template_name: str = ""
    template_version: str = ""


# ---- 그래프 ----


class GraphRequest(BaseModel):
    entries: list[FileEntryModel]
    min_score: float = 0.35
    hide_isolated: bool = True


class GraphNodeModel(BaseModel):
    id: str
    ext: str = ""
    size: int = 0
    file_count: int = 0


class GraphEdgeModel(BaseModel):
    source: str
    target: str
    weight: float


class GraphResponse(BaseModel):
    nodes: list[GraphNodeModel]
    edges: list[GraphEdgeModel]


class TreeNodeModel(BaseModel):
    id: str
    file_count: int
    children: list["TreeNodeModel"] = Field(default_factory=list)


TreeNodeModel.model_rebuild()


# ---- 폴더 구조만 복사 ----


class StructureCopyRequest(BaseModel):
    entries: list[FileEntryModel]
    dest_root: str


class StructureCopyResponse(BaseModel):
    count: int
    created: list[str]
    skipped: list[str]


# ---- 샘플 데이터 ----


class SampleDatasetInfo(BaseModel):
    key: str
    label: str
    description: str
    output_dir: str


class SampleDataRequest(BaseModel):
    output_dir: str | None = None
    force: bool = False
    dataset: str = "general_office"


class SampleDataResponse(BaseModel):
    output_dir: str
    created_count: int
    already_existed: bool
    dataset: str
    label: str


# ---- 정보 ----


class InfoResponse(BaseModel):
    program_version: str
    default_model: str
