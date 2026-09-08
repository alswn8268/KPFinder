from fastapi import APIRouter

from app.structure_copy import copy_structure_only
from api.serialization import models_to_entries
from api.schemas import StructureCopyRequest, StructureCopyResponse

router = APIRouter(prefix="/api/structure", tags=["structure"])


@router.post("/copy", response_model=StructureCopyResponse)
def copy_structure(req: StructureCopyRequest):
    entries = models_to_entries(req.entries)
    count, created, skipped = copy_structure_only(entries, req.dest_root)
    return StructureCopyResponse(count=count, created=created, skipped=skipped)
