"""파일 요약 오케스트레이션(+캐싱)과 폴더 구조 제안(규칙 우선 + AI 보조)."""

import hashlib
import json
import os
from datetime import datetime

from app import llm_client, path_safety, templates
from app.scanner import FileEntry
from app.text_extractor import (
    EncryptedDocumentError,
    ExtractionError,
    HwpParseError,
    OcrNeededError,
    extract_text,
    is_supported,
)

CACHE_DIR = os.path.join(os.path.expanduser("~"), ".ai_folder_organizer")

_STATUS_LABELS = {
    "ok": "완료",
    "empty": "내용 없음",
    "unsupported": "미지원 형식",
    "failed": "요약 불가",
    "pending": "대기",
    "hwp": "파일명 기반 분류",
    "encrypted": "암호화 문서",
    "ocr_needed": "OCR 필요",
}


def status_label(status: str) -> str:
    return _STATUS_LABELS.get(status, status)


def _cache_path_for(root: str) -> str:
    os.makedirs(CACHE_DIR, exist_ok=True)
    key = hashlib.sha256(os.path.abspath(root).encode("utf-8")).hexdigest()[:16]
    return os.path.join(CACHE_DIR, f"summary_cache_{key}.json")


def load_cache(root: str) -> dict:
    path = _cache_path_for(root)
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def save_cache(root: str, cache: dict) -> None:
    path = _cache_path_for(root)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


def clear_cache(root: str) -> bool:
    """이 폴더(root)의 요약 캐시만 지운다. 지울 캐시가 있었으면 True."""
    path = _cache_path_for(root)
    if os.path.exists(path):
        os.remove(path)
        return True
    return False


def clear_all_caches() -> int:
    """모든 폴더의 요약 캐시를 지운다. 지운 파일 수를 반환한다."""
    if not os.path.isdir(CACHE_DIR):
        return 0
    removed = 0
    for name in os.listdir(CACHE_DIR):
        if name.startswith("summary_cache_") and name.endswith(".json"):
            try:
                os.remove(os.path.join(CACHE_DIR, name))
                removed += 1
            except OSError:
                continue
    return removed


def cache_metadata(root: str) -> dict:
    """캐시 저장 위치, 생성 시각, 항목 수, 사용된 모델 목록을 사용자에게 보여주기 위한 정보."""
    path = _cache_path_for(root)
    if not os.path.exists(path):
        return {"exists": False, "path": path, "entry_count": 0, "created_at": None, "models_used": []}
    cache = load_cache(root)
    models = sorted({entry.get("model", "") for entry in cache.values() if entry.get("model")})
    created_at = datetime.fromtimestamp(os.path.getmtime(path)).isoformat(timespec="seconds")
    return {
        "exists": True,
        "path": path,
        "entry_count": len(cache),
        "created_at": created_at,
        "models_used": models,
    }


def _cache_key(entry: FileEntry) -> str:
    # 해시+크기가 같으면 같은 파일 내용으로 간주해 재요약을 건너뛴다(속도 최적화).
    return f"{entry.file_hash}:{entry.size}"


def summarize_entries(
    entries: list[FileEntry], root: str, model: str, progress_cb=None
) -> None:
    """각 FileEntry.summary / summary_status를 채운다. 캐시가 있으면 LLM 호출을 건너뛴다.

    .hwp는 OLE 레코드를 직접 해석하는 best-effort 추출을 시도하고, 성공하면 다른 형식과
    똑같이 LLM 요약을 호출한다(status="ok"). 추출 자체가 실패했을 때만(HwpParseError)
    LLM을 호출하지 않고 파일명/상위 폴더 기반의 안내 문구로 대체한다(status="hwp").
    암호화 문서, 이미지형 PDF는 각각 구분된 상태로 표시한다.
    """
    cache = load_cache(root)
    total = len(entries)
    for i, entry in enumerate(entries, start=1):
        key = _cache_key(entry)
        cached = cache.get(key)
        if cached:
            entry.summary = cached["summary"]
            entry.summary_status = cached["status"]
        elif not is_supported(entry.ext):
            entry.summary = ""
            entry.summary_status = "unsupported"
        else:
            try:
                text = extract_text(entry.path, entry.ext)
                if not text.strip():
                    entry.summary = ""
                    entry.summary_status = "empty"
                else:
                    entry.summary = llm_client.summarize_text(text, model=model)
                    entry.summary_status = "ok"
            except EncryptedDocumentError as exc:
                entry.summary = str(exc)
                entry.summary_status = "encrypted"
            except OcrNeededError as exc:
                entry.summary = str(exc)
                entry.summary_status = "ocr_needed"
            except HwpParseError:
                folder = os.path.dirname(entry.relative_path) or "(최상위)"
                entry.summary = (
                    f"HWP 본문을 읽지 못했습니다. 파일명과 상위 폴더({folder})를 기준으로 "
                    "임시 분류합니다."
                )
                entry.summary_status = "hwp"
            except (ExtractionError, llm_client.OllamaError, OSError) as exc:
                entry.summary = f"요약 불가: {exc}"
                entry.summary_status = "failed"
            cache[key] = {"summary": entry.summary, "status": entry.summary_status, "model": model}
            save_cache(root, cache)
        if progress_cb:
            progress_cb(i, total, entry)


def propose_structure(
    entries: list[FileEntry], model: str, allowed_folders: list[str] | None = None
) -> dict:
    """규칙에 걸리지 않은 파일 중 요약이 있는 것만 AI에 보내 제안을 받는다.

    규칙으로 이미 확실히 분류된 파일이나, 파일명만으로 판단 가능한 파일까지 매번
    AI에 보내지 않도록 호출자(classify_entries)가 이미 대상을 추려서 넘긴다.
    """
    summarized = [
        {"relative_path": e.relative_path, "ext": e.ext, "summary": e.summary or "(요약 없음)"}
        for e in entries
        if e.summary_status in ("ok", "empty")
    ]
    if not summarized:
        notes = (
            "규칙만으로 모든 파일을 분류해 AI 호출이 필요하지 않았습니다."
            if not entries
            else "규칙에 걸리지 않은 파일이 있지만 요약이 없어(지원하지 않는 형식 등) AI에 보낼 수 "
            "없습니다. 제안 편집에서 파일별로 직접 지정해 주세요."
        )
        return {"categories": [], "assignments": {}, "notes": notes}
    return llm_client.propose_folder_structure(
        summarized, model=model, allowed_folders=allowed_folders
    )


DEFAULT_SUGGEST_BATCH_SIZE = 15

# "AI 제안 다시 받기"에서 쓰는 조정 문구. 실측(README 참고)상 파일당 약 26초가 걸려 파일이
# 많으면 카테고리가 지나치게 세분화되거나 뭉뚱그려지기 쉬운데, 사용자가 매번 힌트를 직접
# 타이핑하지 않고도 "더 적게/많게"만 눌러 재시도할 수 있게 문구를 한 곳에 모아둔다.
STRUCTURE_ADJUSTMENTS: dict[str, str] = {
    "fewer": "카테고리 개수를 지금 제안보다 줄여서 더 큰 범주로 묶어 다시 제안해라.",
    "more": "카테고리를 지금 제안보다 더 세분화해서 다시 제안해라.",
}


def _combine_hint(hint: str | None, adjustment: str | None) -> str | None:
    extra = STRUCTURE_ADJUSTMENTS.get(adjustment or "", "")
    combined = f"{hint or ''} {extra}".strip()
    return combined or None


def _propose_in_batches(
    summarized: list[dict],
    model: str,
    user_hint: str | None,
    batch_size: int,
    allowed_folders: list[str] | None = None,
    existing_folders: list[str] | None = None,
    progress_cb=None,
) -> dict:
    """summarized가 batch_size를 넘으면 여러 번 나눠 호출해 결과를 합친다.

    파일이 많으면(수십~수백 개) 한 번의 AI 호출로는 STRUCTURE_TIMEOUT(600초)도 빠듯할 수
    있다. 배치마다 서로 다른 이름의 카테고리가 생기는 것을 줄이기 위해, 이전 배치가 만든
    카테고리를 다음 배치의 힌트에 "가능하면 재사용해라"로 덧붙인다(강제하지는 않는다 —
    allowed_folders처럼 걸러내면 이번 배치 파일이 이전 배치의 카테고리에 안 맞을 때 갈 곳이
    없어지기 때문이다). progress_cb(batch_index, total_batches)는 배치가 끝날 때마다
    호출된다(Streamlit UI의 진행률 표시용, summarize_entries의 progress_cb와 같은 패턴).
    """
    if len(summarized) <= batch_size:
        return llm_client.propose_folder_structure(
            summarized,
            model=model,
            allowed_folders=allowed_folders,
            existing_folders=existing_folders,
            user_hint=user_hint,
        )

    categories: list[str] = []
    seen_categories: set[str] = set()
    assignments: dict[str, dict] = {}
    notes_parts: list[str] = []
    total_batches = (len(summarized) + batch_size - 1) // batch_size

    for batch_index, i in enumerate(range(0, len(summarized), batch_size), start=1):
        batch = summarized[i : i + batch_size]
        batch_hint = user_hint or ""
        if categories:
            batch_hint = (
                f"{batch_hint} 가능하면 다음 기존 카테고리를 재사용해라: {', '.join(categories)}."
            ).strip()
        result = llm_client.propose_folder_structure(
            batch,
            model=model,
            allowed_folders=allowed_folders,
            existing_folders=existing_folders,
            user_hint=batch_hint or None,
        )
        for c in result.get("categories", []):
            if c and c not in seen_categories:
                seen_categories.add(c)
                categories.append(c)
        assignments.update(result.get("assignments", {}))
        if result.get("notes"):
            notes_parts.append(result["notes"])
        if progress_cb:
            progress_cb(batch_index, total_batches)

    return {"categories": categories, "assignments": assignments, "notes": " / ".join(notes_parts)}


def suggest_new_structure(
    entries: list[FileEntry],
    model: str,
    hint: str | None = None,
    adjustment: str | None = None,
    batch_size: int | None = None,
    progress_cb=None,
) -> dict:
    """조직 템플릿에 얽매이지 않고 AI가 완전히 새로운 폴더 구조를 자유롭게 제안한다.

    propose_structure()는 항상 template.allowed_paths()로 AI를 제약하지만, 이 함수는
    allowed_folders=None으로 호출해 AI가 categories 자체를 새로 지어내게 한다. hint를
    주면("부서별로 나눠줘" 등) 그 방향을 반영하고, adjustment("fewer"/"more")를 주면
    "AI 제안 다시 받기"에서 카테고리를 줄이거나 늘리는 방향으로 재시도할 수 있다. 파일
    수가 batch_size(기본 DEFAULT_SUGGEST_BATCH_SIZE)를 넘으면 여러 번 나눠 호출해 결과를
    합친다. 결과는 바로 템플릿이 되지 않으며, 사람이 검토한 뒤
    templates.template_from_ai_proposal()로 템플릿을 만들어야 한다.
    """
    summarized = [
        {"relative_path": e.relative_path, "ext": e.ext, "summary": e.summary or "(요약 없음)"}
        for e in entries
        if e.summary_status in ("ok", "empty")
    ]
    if not summarized:
        return {
            "categories": [],
            "assignments": {},
            "notes": "요약된 파일이 없어 AI에 보낼 수 없습니다. 먼저 파일을 요약한 뒤 다시 시도하세요.",
        }
    combined_hint = _combine_hint(hint, adjustment)
    return _propose_in_batches(
        summarized,
        model,
        combined_hint,
        batch_size or DEFAULT_SUGGEST_BATCH_SIZE,
        progress_cb=progress_cb,
    )


def suggest_structure_update(
    entries: list[FileEntry],
    template: templates.OrgTemplate,
    model: str,
    hint: str | None = None,
    adjustment: str | None = None,
    batch_size: int | None = None,
    progress_cb=None,
) -> dict:
    """기존 템플릿은 유지한 채, 부족한 카테고리만 AI가 추가로 제안하는 하이브리드 모드.

    suggest_new_structure()(완전 자유)와 classify_entries()가 쓰는 propose_structure()
    (완전 제약) 사이의 중간이다 — template.allowed_paths()를 existing_folders로 넘겨
    "우선 사용하되 부족하면 새로 추가"하게 한다. 결과를 템플릿에 반영할 때는
    templates.template_from_hybrid_proposal()을 써야 한다 — AI가 응답에서 기존 폴더를
    빠뜨리고 새 카테고리만 돌려주더라도 기존 템플릿이 손상되지 않도록 그 함수가 기존
    folders를 그대로 보존한다.
    """
    summarized = [
        {"relative_path": e.relative_path, "ext": e.ext, "summary": e.summary or "(요약 없음)"}
        for e in entries
        if e.summary_status in ("ok", "empty")
    ]
    if not summarized:
        return {
            "categories": [],
            "assignments": {},
            "notes": "요약된 파일이 없어 AI에 보낼 수 없습니다. 먼저 파일을 요약한 뒤 다시 시도하세요.",
        }
    combined_hint = _combine_hint(hint, adjustment)
    return _propose_in_batches(
        summarized,
        model,
        combined_hint,
        batch_size or DEFAULT_SUGGEST_BATCH_SIZE,
        existing_folders=template.allowed_paths(),
        progress_cb=progress_cb,
    )


def classify_entries(
    entries: list[FileEntry],
    template: templates.OrgTemplate,
    model: str,
    use_ai: bool = True,
    user_rules: list[dict] | None = None,
) -> dict:
    """조직 규칙과 AI를 결합해 파일별 분류를 만든다.

    우선순위: 조직/사용자 규칙(신뢰도 '높음', AI 호출 없이 즉시 결정)
             -> 규칙에 안 걸린 파일 중 요약이 있는 것만 AI 분류
             -> 그래도 안 걸린 파일은 미분류 폴더로.
    Ollama가 꺼져 있어도(use_ai=False) 규칙 + 미분류 결과만으로 항상 동작한다.
    """
    rule_assignments = templates.classify_by_rules(entries, template, user_rules=user_rules)

    remaining = [e for e in entries if e.relative_path not in rule_assignments]
    ai_result = {"categories": [], "assignments": {}, "notes": ""}
    if use_ai:
        ai_result = propose_structure(remaining, model, allowed_folders=template.allowed_paths())

    # AI는 프롬프트로만 template.allowed_paths() 안에서 고르도록 "부탁"받을 뿐, 강제되지
    # 않는다(작은 로컬 모델은 종종 지시를 무시하고 목록에 없는 폴더를 지어낸다). 여기서
    # 실제로 걸러야만 "AI가 템플릿 밖 임의 폴더를 만들 수 없다"는 안전 원칙이 지켜진다.
    allowed = set(template.allowed_paths())
    assignments = dict(rule_assignments)
    for src, info in ai_result.get("assignments", {}).items():
        if src in assignments:
            continue
        dst = info.get("dst", "")
        folder = dst.rsplit("/", 1)[0] if "/" in dst else dst
        if folder not in allowed:
            continue  # 템플릿 밖 폴더 제안은 무시하고 아래 미분류 처리로 넘긴다.
        assignments[src] = info

    unclassified_target = templates.UNCLASSIFIED_FOLDER
    for entry in entries:
        if entry.relative_path in assignments:
            continue
        if entry.summary_status not in ("ok", "empty"):
            continue  # 미지원/실패/hwp 등은 사용자가 직접 목적지를 지정하도록 비워 둔다.
        filename = os.path.basename(entry.relative_path)
        assignments[entry.relative_path] = {
            "dst": f"{unclassified_target}/{filename}",
            "reason": "규칙과 AI 어느 쪽으로도 분류하지 못했습니다.",
            "confidence": "낮음",
            "source": "fallback",
        }

    return {
        "categories": ai_result.get("categories", []),
        "assignments": assignments,
        "notes": ai_result.get("notes", ""),
    }


def validate_assignments(
    entries: list[FileEntry], assignments: dict, root: str
) -> tuple[dict, list[dict]]:
    """규칙/AI가 만들어낸 assignments를 검증한다.

    각 값은 {"dst","reason","confidence","source"} 형태(과거 호환을 위해 단순 문자열도
    허용)이며, 원본 파일이 실제 스캔 목록에 있는지, 목적지가 대상 폴더(root) 내부의
    안전한 경로인지, 대소문자만 다른 목적지끼리 충돌하지 않는지 확인한다.
    반환값은 (통과한 항목, 거부된 항목과 사유) 튜플이다. 통과한 항목의 값도 항상
    {"dst","reason","confidence","source"} 형태로 정규화된다.
    """
    valid_paths = {e.relative_path for e in entries}
    valid: dict[str, dict] = {}
    rejected: list[dict] = []
    seen_casefold: dict[str, str] = {}

    for src, raw in (assignments or {}).items():
        if isinstance(raw, dict):
            dst = raw.get("dst", "")
            reason = raw.get("reason", "")
            confidence = raw.get("confidence", "보통")
            source = raw.get("source", "ai")
        else:
            dst, reason, confidence, source = (raw or ""), "", "보통", "ai"

        if src not in valid_paths:
            rejected.append({"src": src, "dst": dst, "reason": "스캔 목록에 없는 원본 파일입니다."})
            continue
        ok, path_reason = path_safety.is_safe_destination(root, dst or "")
        if not ok:
            rejected.append({"src": src, "dst": dst, "reason": path_reason})
            continue
        key = dst.casefold()
        if key in seen_casefold:
            rejected.append(
                {
                    "src": src,
                    "dst": dst,
                    "reason": f"'{seen_casefold[key]}'와 대소문자만 다른 목적지가 충돌합니다.",
                }
            )
            continue
        seen_casefold[key] = dst
        valid[src] = {"dst": dst, "reason": reason, "confidence": confidence, "source": source}

    return valid, rejected


def plain_destinations(assignments: dict) -> dict[str, str]:
    """검증된 assignments({"dst",...} 형태)를 file_ops가 쓰는 {src: dst} 평문 dict로 바꾼다."""
    return {src: info["dst"] for src, info in assignments.items()}


def merge_overrides(
    entries: list[FileEntry], assignments: dict, overrides: dict, root: str
) -> tuple[dict, dict, list[dict], set]:
    """AI/규칙 제안(assignments)에 사용자 수정(overrides)을 반영하고 다시 검증한다.

    overrides: {src: {"dst": str, "excluded": bool}}. 사용자가 목적지를 직접 고치거나
    제외 처리한 뒤에도 안전성(경로 이탈, 대소문자 충돌 등)을 다시 검증해야 하므로
    validate_assignments를 두 번(원본, 병합 후) 호출한다.

    반환값: (원본 검증 결과 valid, 병합·재검증된 merged, 두 단계 거부 사유를 합친 rejected,
             사용자가 제외한 src 집합)
    """
    valid, rejected = validate_assignments(entries, assignments, root)

    excluded: set = set()
    combined: dict[str, dict] = {}
    for src, info in valid.items():
        ov = (overrides or {}).get(src)
        if ov and ov.get("excluded"):
            excluded.add(src)
            continue
        if ov and ov.get("dst") and ov["dst"] != info["dst"]:
            combined[src] = {**info, "dst": ov["dst"], "reason": "사용자가 직접 수정", "source": "user"}
        else:
            combined[src] = info

    revalidated, extra_rejected = validate_assignments(entries, combined, root)
    return valid, revalidated, rejected + extra_rejected, excluded
