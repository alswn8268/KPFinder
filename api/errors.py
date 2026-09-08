"""전역 예외 처리기 등록."""

import json

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.llm_client import OllamaError


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(OllamaError)
    async def ollama_error_handler(request: Request, exc: OllamaError):
        return JSONResponse(status_code=502, content={"detail": str(exc)})

    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError):
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    @app.exception_handler(json.JSONDecodeError)
    async def json_error_handler(request: Request, exc: json.JSONDecodeError):
        return JSONResponse(status_code=400, content={"detail": f"JSON 파싱 실패: {exc}"})
