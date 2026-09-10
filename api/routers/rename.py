from fastapi import APIRouter, HTTPException

from app import rename_tool
from api.serialization import models_to_entries
from api.schemas import (
    AssignmentInfo,
    RenameAssignmentsResponse,
    RenamePreviewRequest,
    RenamePreviewRow,
    RenameSuggestRequest,
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


@router.post("/suggest", response_model=RenameAssignmentsResponse)
def suggest(req: RenameSuggestRequest):
    """AI 없이, "(1)"/복사본/사본 같은 흔적만 규칙 기반으로 지운 정리 이름을 제안한다."""
    entries = models_to_entries(req.entries)
    result = rename_tool.build_suggested_rename_assignments(entries)
    return RenameAssignmentsResponse(
        assignments={src: AssignmentInfo(**info) for src, info in result.items()}
    )
