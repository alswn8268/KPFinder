"""FastAPI 진입점.

기존 app/*.py 로직을 감싸는 얇은 API 레이어. 무상태(stateless) — 프런트엔드(Pinia)가
스캔 결과/제안을 들고 있다가 각 호출에 다시 실어 보낸다. 서버 쪽 영속 상태(요약 캐시,
버전 이력, 템플릿)는 지금까지와 동일하게 ~/.ai_folder_organizer/ 에 root 경로 기준으로
저장된다.

실행: uvicorn api.main:app --reload --port 8000
"""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles

from api.errors import register_error_handlers
from api.routers import (
    apply,
    cache,
    classify,
    edit,
    env,
    graphs,
    info,
    models,
    rename,
    report,
    sample_data,
    scan,
    structure_copy,
    templates,
    versions,
)

app = FastAPI(title="K-PathFinder API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1024)

register_error_handlers(app)

for router_module in (
    info,
    env,
    templates,
    scan,
    cache,
    classify,
    edit,
    rename,
    apply,
    versions,
    report,
    graphs,
    structure_copy,
    sample_data,
    models,
):
    app.include_router(router_module.router)

_FRONTEND_DIST = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend", "dist")
if os.path.isdir(_FRONTEND_DIST):
    app.mount("/", StaticFiles(directory=_FRONTEND_DIST, html=True), name="web")
