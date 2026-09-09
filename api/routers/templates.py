import json

from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse

from app import templates as templates_module
from api.serialization import model_to_template, models_to_entries, template_to_model
from api.schemas import (
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
