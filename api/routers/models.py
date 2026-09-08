"""사용자 PC에 실제로 설치된 Ollama 모델 목록 — 사양에 맞는 모델을 직접 고를 수 있게 한다."""

from fastapi import APIRouter

from app import llm_client
from api.schemas import ModelsResponse

router = APIRouter(prefix="/api", tags=["models"])


@router.get("/models", response_model=ModelsResponse)
def list_models():
    connected = llm_client.check_connection()
    models = llm_client.list_installed_models() if connected else []
    return ModelsResponse(connected=connected, models=models)
