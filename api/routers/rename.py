from fastapi import APIRouter, HTTPException

from app import rename_tool
from api.serialization import models_to_entries
from api.schemas import (
    AssignmentInfo,
    RenameAssignmentsResponse,
    RenamePreviewRequest,
    RenamePreviewRow,
)

router = APIRouter(prefix="/api/rename", tags=["rename"])


@router.post("/preview", response_model=list[RenamePreviewRow])
def preview(req: RenamePreviewRequest):
    entries = models_to_entries(req.entries)
    try:
        rows = rename_tool.preview_rename(entries, req.rule.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return [RenamePreviewRow(**r) for r in rows]


@router.post("/assignments", response_model=RenameAssignmentsResponse)
def assignments(req: RenamePreviewRequest):
    entries = models_to_entries(req.entries)
    try:
        result = rename_tool.build_rename_assignments(entries, req.rule.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return RenameAssignmentsResponse(
        assignments={src: AssignmentInfo(**info) for src, info in result.items()}
    )
