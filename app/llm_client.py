"""Ollama 로컬 LLM 연동 모듈.

외부 API를 전혀 사용하지 않고 http://localhost:11434 에서 실행 중인
Ollama 서버(모델: exaone3.5:2.4b, LG AI연구원 제작)에만 접속한다.
GPU 없는 환경에서는 응답이 느릴 수 있어(문단 하나당 약 40~80초) 넉넉한 타임아웃을 둔다.
"""

import json

import requests

OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_CHAT_URL = f"{OLLAMA_BASE_URL}/api/chat"
DEFAULT_MODEL = "exaone3.5:2.4b"
DEFAULT_TIMEOUT = 120


class OllamaError(Exception):
    """Ollama 호출 중 발생한 오류."""


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


def propose_folder_structure(file_entries: list[dict], model: str = DEFAULT_MODEL) -> dict:
    """파일별 요약을 바탕으로 새 폴더 구조와 파일별 이동 위치를 제안받는다.

    반환값: {"categories": [...], "assignments": {"기존 상대경로": "새 경로"}, "notes": "..."}
    """
    file_list_text = "\n".join(
        f"- {e['relative_path']} | 확장자: {e['ext']} | 요약: {e['summary']}"
        for e in file_entries
    )
    messages = [
        {
            "role": "system",
            "content": (
                "너는 회사 업무 폴더를 정리하는 보조원이다. "
                "아래는 폴더 안 파일들의 경로와 요약이다. "
                "내용과 문서 종류를 기준으로 논리적인 폴더 구조(카테고리)를 제안하고, "
                "각 파일을 어느 새 폴더로 옮기면 좋을지 결정해라. "
                "폴더 구조는 2단계(카테고리/파일명)를 넘지 않도록 하고, "
                "반드시 JSON 객체 하나만 출력해라. 다른 설명 문장은 출력하지 마라. "
                "JSON 형식: "
                '{"categories": ["카테고리명", ...], '
                '"assignments": {"기존 상대경로": "새카테고리/파일명"}, '
                '"notes": "제안에 대한 한두 문장 설명"}'
            ),
        },
        {"role": "user", "content": file_list_text},
    ]
    content = chat(messages, model=model, timeout=180)
    return _parse_json_response(content)


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
    except json.JSONDecodeError as exc:
        raise OllamaError(f"JSON 파싱 실패: {exc}. 원본 일부: {content[:500]}") from exc
