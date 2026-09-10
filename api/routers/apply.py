from fastapi import APIRouter

from app import organizer, version_history
from app.file_ops import apply_move_plan, build_move_plan
from api.serialization import models_to_entries
from api.schemas import ApplyRequest, ApplyResponse, PlanItem, PlanRequest, PlanResponse, VersionModel

router = APIRouter(prefix="/api", tags=["apply"])


def _build_plan(root: str, assignments) -> list[dict]:
    plain = organizer.plain_destinations({src: info.model_dump() for src, info in assignments.items()})
    return build_move_plan(root, plain)


@router.post("/plan", response_model=PlanResponse)
def plan(req: PlanRequest):
    plan_items = _build_plan(req.root, req.assignments)
    return PlanResponse(plan=[PlanItem(**p) for p in plan_items])


@router.post("/apply", response_model=ApplyResponse)
def apply(req: ApplyRequest):
    entries = models_to_entries(req.entries)
    plan_items = _build_plan(req.root, req.assignments)
    log_path, moved_count = apply_move_plan(plan_items, entries)
    version = version_history.record_version(req.root, log_path, req.note, moved_count)

    return ApplyResponse(
        log_path=log_path,
        moved_count=moved_count,
        plan_size=len(plan_items),
        version=VersionModel(**version, can_restore=True, restore_blocked_reason=""),
    )
