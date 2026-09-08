from fastapi import APIRouter, HTTPException

from app import version_history
from app.file_ops import undo_move_plan
from api.schemas import RestoreRequest, RestoreResponse, VersionModel

router = APIRouter(prefix="/api/versions", tags=["versions"])


@router.get("", response_model=list[VersionModel])
def list_versions(root: str):
    versions = version_history.list_versions(root)
    result = []
    for v in versions:
        allowed, reason = version_history.can_restore(root, v["version_id"])
        result.append(VersionModel(**v, can_restore=allowed, restore_blocked_reason=reason))
    return result


@router.post("/{version_id}/restore", response_model=RestoreResponse)
def restore(version_id: str, req: RestoreRequest):
    versions = version_history.list_versions(req.root)
    match = next((v for v in versions if v["version_id"] == version_id), None)
    if match is None:
        raise HTTPException(status_code=404, detail="존재하지 않는 버전입니다.")

    allowed, reason = version_history.can_restore(req.root, version_id)
    if not allowed:
        raise HTTPException(status_code=409, detail=reason)

    restored_count = undo_move_plan(match["log_path"])
    version_history.mark_restored(req.root, version_id)
    return RestoreResponse(restored_count=restored_count)
