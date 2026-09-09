"""Ollama 로컬 LLM 연동 모듈.

외부 API를 전혀 사용하지 않고 http://localhost:11434 에서 실행 중인
Ollama 서버(모델: exaone3.5:2.4b, LG AI연구원 제작)에만 접속한다.

실제 리허설 실측(2026-09-08, 로컬 PC): 파일 1개 요약 약 8~20초, 파일 10개를 한 번에
구조화된 JSON(카테고리+파일별 목적지+이유+신뢰도)으로 묶어 제안받는 데는 약 258초
(파일당 약 26초)가 걸렸다. 하드웨어에 따라 크게 달라지므로(GPU 유무 등), 요약보다
폴더 구조 제안 쪽에 훨씬 넉넉한 타임아웃(STRUCTURE_TIMEOUT)을 둔다.
"""

import json
import re

import requests

OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_CHAT_URL = f"{OLLAMA_BASE_URL}/api/chat"
DEFAULT_MODEL = "exaone3.5:2.4b"
DEFAULT_TIMEOUT = 120
# 폴더 구조 제안은 파일이 여러 개일 때 한 번에 훨씬 긴 구조화된 JSON을 생성해야 하므로
# 단순 요약(DEFAULT_TIMEOUT)보다 훨씬 넉넉한 타임아웃이 필요하다 — 실제 Ollama 연동
# 리허설에서 10개 파일 기준 180초로는 부족한 것을 확인하고 늘렸다.
STRUCTURE_TIMEOUT = 600


class OllamaError(Exception):
    """Ollama 호출 중 발생한 오류."""


# 사양별로 바로 받을 수 있도록 미리 골라 둔 모델 목록 — 용량이 작은 순서.
# EXAONE 계열은 한국어 문서 요약에 강해 이 앱의 주 용도(사내 업무 문서 정리)에 잘
# 맞으므로 기본값으로 유지하고, 그보다 더 가벼운/무거운 대안을 양 끝에 하나씩 둔다.
RECOMMENDED_MODELS = [
    {
        "name": "qwen2.5:1.5b",
        "label": "Qwen2.5 1.5B",
        "tier": "최소 사양",
        "size_gb": 1.0,
        "description": "가장 가볍고 빠릅니다. GPU가 없거나 RAM이 8GB 이하인 PC에 적합하지만, 한국어 요약 품질은 EXAONE보다 떨어질 수 있습니다.",
    },
    {
        "name": DEFAULT_MODEL,
        "label": "EXAONE 3.5 2.4B (기본 추천)",
        "tier": "일반 사양",
        "size_gb": 1.6,
        "description": "이 앱의 기본 모델입니다. LG AI연구원이 한국어에 맞춰 학습해 업무 문서 요약에 적합하고, 일반적인 사무용 PC에서 무난하게 동작합니다.",
    },
    {
        "name": "exaone3.5:7.8b",
        "label": "EXAONE 3.5 7.8B (고성능)",
        "tier": "고사양",
        "size_gb": 4.8,
        "description": "더 크고 정교한 모델로 분류 품질이 좋아지지만, 다운로드 용량이 크고 GPU가 없으면 느릴 수 있습니다.",
    },
]


def list_recommended_models(base_url: str = OLLAMA_BASE_URL) -> list[dict]:
    """사양별 추천 모델 목록에, 이 PC에 이미 설치돼 있는지 여부를 표시해 반환한다."""
    installed_names = {m["name"] for m in list_installed_models(base_url)}
    return [
        {**model, "installed": model["name"] in installed_names} for model in RECOMMENDED_MODELS
    ]


def pull_model_stream(model: str, base_url: str = OLLAMA_BASE_URL):
    """모델을 다운로드하며 Ollama가 보내는 진행 상황을 한 줄(JSON 문자열)씩 그대로 넘긴다.

    각 줄은 최소 {"status": "..."}이고, 다운로드 중에는 {"status": "downloading",
    "digest": "...", "total": <bytes>, "completed": <bytes>}가 반복해서 온다.
    큰 모델은 수 분 걸릴 수 있으므로 타임아웃을 걸지 않는다 — 대신 호출자가 스트림을
    끝까지 소비하지 않고 연결을 끊으면(예: 사용자가 페이지를 벗어남) 자연히 중단된다.
    """
    resp = requests.post(
        f"{base_url}/api/pull", json={"name": model, "stream": True}, stream=True, timeout=None
    )
    resp.raise_for_status()
    for line in resp.iter_lines():
        if line:
            yield line.decode("utf-8")


def list_installed_models(base_url: str = OLLAMA_BASE_URL, timeout: int = 5) -> list[dict]:
    """이 PC에 이미 받아져 있는 Ollama 모델 목록을 크기순(작은 것부터)으로 반환한다.

    사양이 낮은 PC일수록 작은 모델을 고를 수 있도록, 사용자가 직접 판단할 수 있는
    최소한의 정보(이름, 용량, 파라미터 크기)만 담는다. Ollama가 꺼져 있으면 빈 목록.
    """
    try:
        resp = requests.get(f"{base_url}/api/tags", timeout=timeout)
        resp.raise_for_status()
        raw_models = resp.json().get("models", [])
    except (requests.RequestException, ValueError):
        return []

    models = []
    for m in raw_models:
        details = m.get("details", {})
        models.append(
            {
                "name": m.get("name", ""),
                "size_mb": round(m.get("size", 0) / (1024 * 1024)),
                "parameter_size": details.get("parameter_size", ""),
                "quantization": details.get("quantization_level", ""),
            }
        )
    return sorted(models, key=lambda m: m["size_mb"])


def check_connection(base_url: str = OLLAMA_BASE_URL, timeout: int = 5) -> bool:
    try:
        resp = requests.get(f"{base_url}/api/tags", timeout=timeout)
        return resp.status_code == 200
    except requests.RequestException:
        return False


def chat(
    messages: list[dict],
    model: str = DEFAULT_MODEL,
    timeout: int = DEFAULT_TIMEOUT,
    temperature: float = 0.2,
) -> str:
    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {"temperature": temperature},
    }
    try:
        resp = requests.post(OLLAMA_CHAT_URL, json=payload, timeout=timeout)
        resp.raise_for_status()
    except requests.Timeout as exc:
        raise OllamaError(f"Ollama 응답 시간 초과 ({timeout}초)") from exc
    except requests.RequestException as exc:
        raise OllamaError(f"Ollama 호출 실패: {exc}") from exc

    try:
        data = resp.json()
        return data["message"]["content"]
    except (ValueError, KeyError, TypeError) as exc:
        raise OllamaError(f"Ollama 응답 형식이 예상과 다릅니다: {resp.text[:300]}") from exc


def summarize_text(text: str, model: str = DEFAULT_MODEL, max_chars: int = 2000) -> str:
    snippet = text.strip()[:max_chars]
    if not snippet:
        return ""
    messages = [
        {
            "role": "system",
            "content": (
                "너는 회사 문서를 정리하는 보조원이다. "
                "주어진 문서 내용을 한국어로 1~2문장으로 간결하게 요약해라. "
                "문서 종류와 핵심 주제가 드러나게 요약하고, 다른 설명은 덧붙이지 마라."
            ),
        },
        {"role": "user", "content": snippet},
    ]
    return chat(messages, model=model).strip()


def propose_folder_structure(
    file_entries: list[dict],
    model: str = DEFAULT_MODEL,
    allowed_folders: list[str] | None = None,
    timeout: int = STRUCTURE_TIMEOUT,
) -> dict:
    """파일별 요약을 바탕으로 새 폴더 구조와 파일별 이동 위치를 제안받는다.

    allowed_folders를 주면 AI가 그 목록 안에서만 목적지를 고르도록 제약한다
    (조직 표준 템플릿 밖의 임의 카테고리 생성을 막기 위함).

    반환값: {"categories": [...],
             "assignments": {"기존 상대경로": {"dst": "새경로", "reason": "...", "confidence": "높음|보통|낮음"}},
             "notes": "..."}
    """
    file_list_text = "\n".join(
        f"- {e['relative_path']} | 확장자: {e['ext']} | 요약: {e['summary']}"
        for e in file_entries
    )
    folder_constraint = ""
    if allowed_folders:
        folder_list_text = ", ".join(allowed_folders)
        folder_constraint = (
            "목적지 폴더는 반드시 다음 목록 중 하나로만 시작해야 한다(새 폴더명을 임의로 "
            f"만들지 마라): {folder_list_text}. "
        )
    messages = [
        {
            "role": "system",
            "content": (
                "너는 회사 업무 폴더를 정리하는 보조원이다. "
                "아래는 폴더 안 파일들의 경로와 요약이다. "
                "내용과 문서 종류를 기준으로 각 파일을 어느 폴더로 옮기면 좋을지 결정해라. "
                + folder_constraint
                + "파일별로 분류 이유(reason)와 신뢰도(confidence: 높음/보통/낮음)도 함께 제시해라. "
                "신뢰도는 파일명·내용·규칙이 모두 일치하면 '높음', 내용은 일치하지만 "
                "직접적인 규칙이 없으면 '보통', 본문이 불완전하거나 여러 카테고리로 "
                "해석될 수 있으면 '낮음'으로 판단해라. "
                "반드시 JSON 객체 하나만 출력해라. 다른 설명 문장은 출력하지 마라. "
                "JSON 형식: "
                '{"categories": ["카테고리명", ...], '
                '"assignments": {"기존 상대경로": {"dst": "새카테고리/파일명", '
                '"reason": "분류 이유", "confidence": "높음|보통|낮음"}}, '
                '"notes": "제안에 대한 한두 문장 설명"}'
            ),
        },
        {"role": "user", "content": file_list_text},
    ]
    content = chat(messages, model=model, timeout=timeout)
    raw = _parse_json_response(content)
    raw["assignments"] = normalize_assignments(raw.get("assignments"))
    return raw


def normalize_assignments(raw_assignments) -> dict[str, dict]:
    """AI 응답의 assignments를 {src: {"dst","reason","confidence"}} 형태로 통일한다.

    모델이 형식을 지키지 않고 문자열만 반환하는 경우에도 대비한다.
    """
    normalized: dict[str, dict] = {}
    for src, value in (raw_assignments or {}).items():
        if isinstance(value, dict):
            dst = value.get("dst") or value.get("path") or value.get("target") or ""
            reason = value.get("reason", "")
            confidence = value.get("confidence") or "보통"
        elif isinstance(value, str):
            dst, reason, confidence = value, "", "보통"
        else:
            continue
        if confidence not in ("높음", "보통", "낮음"):
            confidence = "보통"
        normalized[src] = {
            "dst": dst,
            "reason": reason,
            "confidence": confidence,
            "source": "ai",
        }
    return normalized


# Windows 상대경로(예: "backup_old\사내_보안_정책.txt")를 모델이 JSON 문자열 안에 그대로
# 베껴 쓰면서 백슬래시를 이스케이프하지 않는 경우가 실제 있었다(실기 리허설에서 재현) —
# 유효한 JSON 이스케이프(\" \\ \/ \b \f \n \r \t \uXXXX)가 아닌 나 홀로 백슬래시만 골라
# \\ 로 고쳐서 재시도한다.
_INVALID_ESCAPE_RE = re.compile(r'\\(?!["\\/bfnrtu])')


def _repair_invalid_escapes(text: str) -> str:
    return _INVALID_ESCAPE_RE.sub(r"\\\\", text)


def _parse_json_response(content: str) -> dict:
    text = content.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if "\n" in text:
            first_line, rest = text.split("\n", 1)
            text = rest if first_line.strip().lower() in ("json", "") else text
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise OllamaError(f"JSON 응답을 찾을 수 없습니다: {content[:200]}")
    json_text = text[start : end + 1]
    try:
        return json.loads(json_text)
    except json.JSONDecodeError:
        pass
    try:
        return json.loads(_repair_invalid_escapes(json_text))
    except json.JSONDecodeError as exc:
        raise OllamaError(f"JSON 파싱 실패: {exc}. 원본 일부: {content[:500]}") from exc
