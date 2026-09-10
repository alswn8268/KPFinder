from fastapi import APIRouter

from app import __version__ as PROGRAM_VERSION
from app import llm_client
from api.schemas import InfoResponse

router = APIRouter(prefix="/api", tags=["info"])


@router.get("/info", response_model=InfoResponse)
def get_info():
    return InfoResponse(program_version=PROGRAM_VERSION, default_model=llm_client.DEFAULT_MODEL)
