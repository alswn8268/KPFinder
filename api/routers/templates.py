import json

from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse

from app import organizer
from app import templates as templates_module
from app.llm_client import OllamaError
from api.serialization import model_to_template, models_to_entries, template_to_model
from api.schemas import (
    AssignmentInfo,
    SuggestStructureRequest,
    SuggestStructureResponse,
    SuggestStructureUpdateRequest,
    TemplateFromAiProposalRequest,
    TemplateFromHybridProposalRequest,
    TemplateFromListRequest,
    TemplateFromStructureRequest,
    TemplateImportRequest,
    TemplateModel,
    TemplateSaveRequest,
)
from sample_data.org_templates import SAMPLE_TEMPLATES

router = APIRouter(prefix="/api/templates", tags=["templates"])


@router.get("", response_model=list[TemplateModel])
def list_templates():
    return [template_to_model(t) for t in templates_module.list_saved_templates()]


@router.get("/default", response_model=TemplateModel)
def get_default_template():
    return template_to_model(templates_module.default_template())


@router.get("/samples", response_model=list[TemplateModel])
def list_sample_templates():
    """개발팀/운영팀/회계팀 등 부서별 샘플 템플릿 — 시연용."""
    return [template_to_model(entry["template"]) for entry in SAMPLE_TEMPLATES.values()]


@router.post("/import", response_model=TemplateModel)
def import_template(req: TemplateImportRequest):
    try:
        tmpl = templates_module.import_template(req.json_text)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail=f"템플릿 JSON을 읽을 수 없습니다: {exc}") from exc
    return template_to_model(tmpl)


@router.post("/save")
def save_template(req: TemplateSaveRequest):
    path = templates_module.save_template(model_to_template(req.template))
    return {"path": path}


@router.post("/export", response_class=PlainTextResponse)
def export_template(template: TemplateModel):
    return templates_module.export_template(model_to_template(template))


@router.post("/from-current-structure", response_model=TemplateModel)
def from_current_structure(req: TemplateFromStructureRequest):
    entries = models_to_entries(req.entries)
    tmpl = templates_module.template_from_current_structure(entries, name=req.name)
    return template_to_model(tmpl)


@router.post("/from-folder-list", response_model=TemplateModel)
def from_folder_list(req: TemplateFromListRequest):
    try:
        tmpl = templates_module.template_from_folder_list(
            req.text, name=req.name, keep_unclassified=req.keep_unclassified
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return template_to_model(tmpl)


@router.post("/suggest", response_model=SuggestStructureResponse)
def suggest_structure(req: SuggestStructureRequest):
    """조직 템플릿과 무관하게 AI가 새 폴더 구조를 제안한다 — 검토용, 아직 템플릿이 아니다.

    hint/adjustment로 "AI 제안 다시 받기"(카테고리 더 적게/많게)를 지원하고, 파일이 많으면
    batch_size 기준으로 나눠 호출한 뒤 organizer가 결과를 합친다.
    """
    entries = models_to_entries(req.entries)
    try:
        result = organizer.suggest_new_structure(
            entries,
            req.model,
            hint=req.hint or None,
            adjustment=req.adjustment or None,
            batch_size=req.batch_size,
        )
    except OllamaError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    assignments = {src: AssignmentInfo(**info) for src, info in result["assignments"].items()}
    return SuggestStructureResponse(
        categories=result.get("categories", []),
        assignments=assignments,
        notes=result.get("notes", ""),
    )


@router.post("/suggest-update", response_model=SuggestStructureResponse)
def suggest_structure_update(req: SuggestStructureUpdateRequest):
    """하이브리드 모드 — 기존 템플릿 폴더를 우선 사용하되, 부족한 카테고리만 AI가 추가 제안한다."""
    entries = models_to_entries(req.entries)
    template = model_to_template(req.template)
    try:
        result = organizer.suggest_structure_update(
            entries,
            template,
            req.model,
            hint=req.hint or None,
            adjustment=req.adjustment or None,
            batch_size=req.batch_size,
        )
    except OllamaError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    assignments = {src: AssignmentInfo(**info) for src, info in result["assignments"].items()}
    return SuggestStructureResponse(
        categories=result.get("categories", []),
        assignments=assignments,
        notes=result.get("notes", ""),
    )


@router.post("/from-ai-proposal", response_model=TemplateModel)
def from_ai_proposal(req: TemplateFromAiProposalRequest):
    try:
        tmpl = templates_module.template_from_ai_proposal(req.categories, name=req.name)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return template_to_model(tmpl)


@router.post("/from-hybrid-proposal", response_model=TemplateModel)
def from_hybrid_proposal(req: TemplateFromHybridProposalRequest):
    base = model_to_template(req.template)
    tmpl = templates_module.template_from_hybrid_proposal(base, req.categories, name=req.name)
    return template_to_model(tmpl)
