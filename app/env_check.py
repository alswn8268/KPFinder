"""실행 환경 점검(FR-ENV-01).

Ollama가 꺼져 있어도 프로그램이 죽지 않아야 하므로, 이 모듈은 예외를 던지지 않고
항상 상태 목록을 반환한다. 각 항목은 '정상'/'주의'/'오류' 중 하나이며, 오류 항목에는
사용자가 무엇을 하면 되는지(명령어가 아니라 행동 중심으로) 안내 문구를 함께 담는다.
"""

import importlib
import os
import platform
import shutil

from app import llm_client

OK, WARN, ERROR = "정상", "주의", "오류"

REQUIRED_MODULES = [
    ("streamlit", "streamlit"),
    ("pandas", "pandas"),
    ("requests", "requests"),
    ("python-docx", "docx"),
    ("openpyxl", "openpyxl"),
    ("python-pptx", "pptx"),
    ("pypdf", "pypdf"),
    ("networkx", "networkx"),
    ("matplotlib", "matplotlib"),
    ("olefile", "olefile"),
]

MIN_FREE_SPACE_MB = 200


def _check_python() -> dict:
    import sys

    ok = sys.version_info >= (3, 10)
    return {
        "item": "Python 실행 환경",
        "status": OK if ok else WARN,
        "detail": f"{sys.version.split()[0]}",
        "action": "" if ok else "Python 3.10 이상 사용을 권장합니다.",
    }


def _check_libraries() -> dict:
    missing = []
    for display_name, module_name in REQUIRED_MODULES:
        try:
            importlib.import_module(module_name)
        except ImportError:
            missing.append(display_name)
    if not missing:
        return {"item": "필수 라이브러리", "status": OK, "detail": "모두 설치됨", "action": ""}
    return {
        "item": "필수 라이브러리",
        "status": ERROR,
        "detail": f"누락: {', '.join(missing)}",
        "action": "`pip install -r requirements.txt`를 실행해 누락된 패키지를 설치하세요.",
    }


def _check_ollama(model: str) -> tuple[dict, dict]:
    connected = llm_client.check_connection()
    conn_item = {
        "item": "Ollama 실행 여부",
        "status": OK if connected else ERROR,
        "detail": "연결됨" if connected else "연결할 수 없음",
        "action": "" if connected else "Ollama를 설치하고 `ollama serve`로 실행한 뒤 '다시 확인'을 눌러주세요.",
    }

    if not connected:
        model_item = {
            "item": "AI 모델 설치 여부",
            "status": ERROR,
            "detail": "확인 불가(Ollama 미연결)",
            "action": "Ollama 연결 후 다시 확인하세요.",
        }
        return conn_item, model_item

    try:
        import requests

        resp = requests.get(f"{llm_client.OLLAMA_BASE_URL}/api/tags", timeout=5)
        resp.raise_for_status()
        names = {m.get("name", "") for m in resp.json().get("models", [])}
        installed = any(model == n or n.startswith(model.split(":")[0]) for n in names)
    except Exception:
        installed = False

    model_item = {
        "item": "AI 모델 설치 여부",
        "status": OK if installed else ERROR,
        "detail": "설치됨" if installed else f"'{model}' 모델을 찾을 수 없음",
        "action": "" if installed else f"`ollama pull {model}` 명령으로 모델을 내려받으세요.",
    }
    return conn_item, model_item


def _check_folder(root: str) -> list[dict]:
    if not root:
        return []
    items = []
    readable = os.path.isdir(root) and os.access(root, os.R_OK)
    items.append(
        {
            "item": "대상 폴더 읽기 권한",
            "status": OK if readable else ERROR,
            "detail": root,
            "action": "" if readable else "폴더 경로가 올바른지, 읽기 권한이 있는지 확인하세요.",
        }
    )
    writable = readable and os.access(root, os.W_OK)
    items.append(
        {
            "item": "대상 폴더 쓰기 권한",
            "status": OK if writable else WARN,
            "detail": root,
            "action": "" if writable else "쓰기 권한이 없으면 실제 적용(파일 이동) 단계에서 실패할 수 있습니다.",
        }
    )
    return items


def _check_cache_dir(cache_dir: str) -> dict:
    try:
        os.makedirs(cache_dir, exist_ok=True)
        probe = os.path.join(cache_dir, ".write_probe")
        with open(probe, "w", encoding="utf-8") as f:
            f.write("ok")
        os.remove(probe)
        return {"item": "캐시 저장 위치", "status": OK, "detail": cache_dir, "action": ""}
    except OSError as exc:
        return {
            "item": "캐시 저장 위치",
            "status": ERROR,
            "detail": cache_dir,
            "action": f"캐시 폴더에 쓸 수 없습니다({exc}). 폴더 권한을 확인하세요.",
        }


def _check_disk_space(cache_dir: str) -> dict:
    try:
        check_path = cache_dir if os.path.isdir(cache_dir) else os.path.expanduser("~")
        free_mb = shutil.disk_usage(check_path).free / (1024 * 1024)
        ok = free_mb >= MIN_FREE_SPACE_MB
        return {
            "item": "여유 저장 공간",
            "status": OK if ok else WARN,
            "detail": f"{free_mb:,.0f} MB",
            "action": "" if ok else "여유 공간이 부족하면 리포트/로그 저장이 실패할 수 있습니다.",
        }
    except OSError:
        return {"item": "여유 저장 공간", "status": WARN, "detail": "확인 불가", "action": ""}


def _check_os() -> dict:
    return {
        "item": "운영체제",
        "status": OK,
        "detail": f"{platform.system()} {platform.release()}",
        "action": "",
    }


def check_environment(root: str = "", model: str = None, cache_dir: str = None) -> list[dict]:
    """환경 점검 항목 목록을 반환한다. 항상 예외 없이 끝까지 실행된다."""
    from app.organizer import CACHE_DIR

    model = model or llm_client.DEFAULT_MODEL
    cache_dir = cache_dir or CACHE_DIR

    items = [_check_python(), _check_libraries()]
    conn_item, model_item = _check_ollama(model)
    items.append(conn_item)
    items.append(model_item)
    items.extend(_check_folder(root))
    items.append(_check_cache_dir(cache_dir))
    items.append(_check_disk_space(cache_dir))
    items.append(_check_os())
    return items


def has_blocking_error(items: list[dict]) -> bool:
    """AI 관련 오류를 제외한, 스캔조차 막는 치명적 오류가 있는지 확인한다."""
    ai_related = {"Ollama 실행 여부", "AI 모델 설치 여부"}
    return any(i["status"] == ERROR and i["item"] not in ai_related for i in items)
