import os

from fastapi import APIRouter, HTTPException

from app.scanner import compute_hashes, find_duplicate_groups, scan_folder
from api.serialization import entries_to_models
from api.schemas import DuplicateGroupModel, ScanErrorItem, ScanRequest, ScanResponse

router = APIRouter(prefix="/api", tags=["scan"])


@router.post("/scan", response_model=ScanResponse)
def scan(req: ScanRequest):
    if not req.root or not os.path.isdir(req.root):
        raise HTTPException(status_code=400, detail="올바른 폴더 경로를 입력하세요.")

    errors: list[ScanErrorItem] = []

    def on_error(path: str, reason: str) -> None:
        errors.append(ScanErrorItem(path=path, reason=reason))

    entries = scan_folder(
        req.root,
        exclude_dirs=set(req.exclude_dirs) or None,
        exclude_exts=set(req.exclude_exts) or None,
        include_hidden=req.include_hidden,
        max_file_size_mb=req.max_file_size_mb,
        on_error=on_error,
    )
    compute_hashes(entries)
    dup_groups = find_duplicate_groups(entries)

    return ScanResponse(
        scan_root=req.root,
        entries=entries_to_models(entries),
        duplicate_groups=[
            DuplicateGroupModel(hash=h, files=entries_to_models(group))
            for h, group in dup_groups.items()
        ],
        errors=errors,
        total_files=len(entries),
    )
