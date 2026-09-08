from datetime import datetime
from types import SimpleNamespace

from fastapi import APIRouter
from fastapi.responses import HTMLResponse, Response

from app import __version__ as PROGRAM_VERSION
from app import report as report_module
from api.serialization import models_to_entries
from api.schemas import ReportRequest

router = APIRouter(prefix="/api/report", tags=["report"])


def _duplicate_groups_dict(req: ReportRequest) -> dict:
    return {g.hash: models_to_entries(g.files) for g in req.duplicate_groups}


def _similar_docs(req: ReportRequest) -> list:
    return [
        (SimpleNamespace(relative_path=p.a), SimpleNamespace(relative_path=p.b), p.score)
        for p in req.similar_docs
    ]


@router.post("/json")
def report_json(req: ReportRequest):
    entries = models_to_entries(req.entries)
    body = report_module.build_report(
        entries,
        _duplicate_groups_dict(req),
        req.proposal,
        _similar_docs(req),
        final_state=req.final_state,
        env_items=[e.model_dump() for e in req.env_items],
        model=req.model,
        template_name=req.template_name,
        template_version=req.template_version,
        program_version=PROGRAM_VERSION,
    )
    filename = f"folder_organize_report_{datetime.now():%Y%m%d_%H%M%S}.json"
    return Response(
        content=body,
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/excel")
def report_excel(req: ReportRequest):
    entries = models_to_entries(req.entries)
    data = report_module.build_excel_report(entries, _duplicate_groups_dict(req), req.final_state)
    filename = f"folder_organize_report_{datetime.now():%Y%m%d_%H%M%S}.xlsx"
    return Response(
        content=data,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/html", response_class=HTMLResponse)
def report_html(req: ReportRequest):
    entries = models_to_entries(req.entries)
    meta = {
        "model": req.model,
        "template_name": req.template_name,
        "template_version": req.template_version,
        "program_version": PROGRAM_VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
    }
    return report_module.build_html_report(entries, _duplicate_groups_dict(req), req.final_state, meta)
