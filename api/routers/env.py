from fastapi import APIRouter

from app import env_check
from api.schemas import EnvCheckResponse

router = APIRouter(prefix="/api/env", tags=["env"])


@router.get("/check", response_model=EnvCheckResponse)
def check_environment(root: str = "", model: str | None = None):
    items = env_check.check_environment(root=root, model=model)
    return EnvCheckResponse(items=items, has_blocking_error=env_check.has_blocking_error(items))
