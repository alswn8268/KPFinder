from fastapi import APIRouter

from app import organizer, report
from api.serialization import models_to_entries
from api.schemas import AssignmentInfo, RejectedItem, ValidateRequest, ValidateResponse

router = APIRouter(prefix="/api", tags=["edit"])


@router.post("/assignments/validate", response_model=ValidateResponse)
def validate(req: ValidateRequest):
    entries = models_to_entries(req.entries)
    assignments = {src: info.model_dump() for src, info in req.assignments.items()}
    overrides = {src: ov.model_dump() for src, ov in req.overrides.items()}

    valid, merged, rejected, excluded = organizer.merge_overrides(
        entries, assignments, overrides, req.root
    )

    final_state = report.build_final_state(entries, merged, excluded, rejected)
    tree_before = report.render_current_tree(entries)
    tree_after = report.render_proposed_tree(merged)

    return ValidateResponse(
        valid={src: AssignmentInfo(**info) for src, info in valid.items()},
        merged={src: AssignmentInfo(**info) for src, info in merged.items()},
        rejected=[RejectedItem(**r) for r in rejected],
        excluded=sorted(excluded),
        final_state=final_state,
        tree_before=tree_before,
        tree_after=tree_after,
    )
