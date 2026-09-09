"""사용자 PC에 실제로 설치된 Ollama 모델 목록 — 사양에 맞는 모델을 직접 고를 수 있게 한다.

또한 사양별 추천 모델을 앱 안에서 바로 받을 수 있도록 다운로드 진행 상황을
스트리밍으로 전달한다(처음 Ollama를 설치해 모델이 하나도 없는 사용자를 위한 것).
"""

import json

import requests
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app import llm_client
from api.schemas import ModelsResponse, PullModelRequest, RecommendedModelModel

router = APIRouter(prefix="/api", tags=["models"])


@router.get("/models", response_model=ModelsResponse)
def list_models():
    connected = llm_client.check_connection()
    models = llm_client.list_installed_models() if connected else []
    return ModelsResponse(connected=connected, models=models)


@router.get("/models/recommended", response_model=list[RecommendedModelModel])
def recommended_models():
    return llm_client.list_recommended_models()


@router.post("/models/pull")
def pull_model(req: PullModelRequest):
    """Ollama의 다운로드 진행 상황을 한 줄씩(NDJSON) 그대로 클라이언트에 흘려보낸다."""

    def generate():
        try:
            for line in llm_client.pull_model_stream(req.model):
                yield line + "\n"
        except requests.RequestException as exc:
            yield json.dumps({"status": "error", "error": str(exc)}) + "\n"

    return StreamingResponse(generate(), media_type="application/x-ndjson")
