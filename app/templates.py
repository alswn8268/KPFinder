"""조직 표준 폴더 템플릿과 규칙 기반 1차 분류.

AI가 매번 다른 이름의 폴더를 만들어내는 것을 막기 위해, 조직이 정한 표준 폴더
체계와 키워드 규칙을 먼저 적용한다. 분류 우선순위는 다음과 같다.

    강제 제외 규칙 -> 조직 고정 규칙 -> 사용자 지정 규칙 -> 파일명 기반 분류
    -> (남는 파일만) 문서 내용 기반 AI 분류 -> 미분류 처리

규칙만으로 확실히 분류되는 파일은 AI 호출 없이도 결과가 나오므로, 이 모듈은
Ollama 연결 여부와 무관하게 항상 동작한다("AI 없이 사용할 수 있는 모드"의 기반).
"""

import glob
import hashlib
import json
import os
from dataclasses import dataclass, field

from app.scanner import FileEntry

CACHE_DIR = os.path.join(os.path.expanduser("~"), ".ai_folder_organizer")
TEMPLATE_DIR = os.path.join(CACHE_DIR, "templates")

UNCLASSIFIED_FOLDER = "99_미분류"

DEFAULT_FOLDERS = [
    {"path": "01_경영지원", "description": "경영 전반, 총무"},
    {"path": "02_인사", "description": "인사, 채용, 교육"},
    {"path": "03_재무·회계", "description": "예산, 정산, 회계"},
    {"path": "04_계약·법무", "description": "계약서, 협약서, 법무 검토"},
    {"path": "05_사업기획", "description": "사업계획, 기획안"},
    {"path": "06_영업", "description": "영업 실적, 거래처"},
    {"path": "07_마케팅·홍보", "description": "마케팅, 홍보, 캠페인"},
    {"path": "08_회의록", "description": "회의록, 주간 회의"},
    {"path": "09_교육자료", "description": "교육, 온보딩 자료"},
    {"path": "10_양식", "description": "각종 신청/결재 양식"},
    {"path": "90_보관", "description": "장기 보관용 자료"},
    {"path": UNCLASSIFIED_FOLDER, "description": "규칙/AI로 분류하지 못한 파일"},
]

# 규칙: 이름 키워드가 파일명 또는 요약에 있으면 target으로 분류(높은 신뢰도).
DEFAULT_KEYWORD_RULES = [
    {"keywords": ["회의록", "주간회의"], "target": "08_회의록"},
    {"keywords": ["계약서", "협약서"], "target": "04_계약·법무"},
    {"keywords": ["예산", "정산", "회계", "입출금"], "target": "03_재무·회계"},
    {"keywords": ["채용", "인사", "온보딩", "교육자료", "오리엔테이션"], "target": "09_교육자료"},
    {"keywords": ["영업", "거래처", "실적"], "target": "06_영업"},
    {"keywords": ["마케팅", "홍보", "캠페인"], "target": "07_마케팅·홍보"},
    {"keywords": ["사업계획", "기획안", "제안서"], "target": "05_사업기획"},
    {"keywords": ["양식", "신청서", "요청서"], "target": "10_양식"},
]

# 파일명에 이 키워드가 있으면 분류와 무관하게 "중복 검토 대상"으로 표시만 한다(이동 규칙 아님).
DUPLICATE_HINT_KEYWORDS = ["복사본", "(1)", "final", "최종", "_v2", "_v3"]


@dataclass
class OrgTemplate:
    name: str
    version: str = "1.0"
    author: str = ""
    folders: list = field(default_factory=lambda: [dict(f) for f in DEFAULT_FOLDERS])
    keyword_rules: list = field(default_factory=lambda: [dict(r) for r in DEFAULT_KEYWORD_RULES])

    def allowed_paths(self) -> list[str]:
        return [f["path"] for f in self.folders]

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "version": self.version,
            "author": self.author,
            "folders": self.folders,
            "keyword_rules": self.keyword_rules,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "OrgTemplate":
        return cls(
            name=data.get("name", "이름 없음"),
            version=data.get("version", "1.0"),
            author=data.get("author", ""),
            folders=data.get("folders") or [dict(f) for f in DEFAULT_FOLDERS],
            keyword_rules=data.get("keyword_rules") or [],
        )


def default_template() -> OrgTemplate:
    return OrgTemplate(name="기본 조직 템플릿")


def _template_path(name: str) -> str:
    os.makedirs(TEMPLATE_DIR, exist_ok=True)
    key = hashlib.sha256(name.encode("utf-8")).hexdigest()[:16]
    return os.path.join(TEMPLATE_DIR, f"{key}.json")


def save_template(template: OrgTemplate) -> str:
    path = _template_path(template.name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(template.to_dict(), f, ensure_ascii=False, indent=2)
    return path


def list_saved_templates() -> list[OrgTemplate]:
    if not os.path.isdir(TEMPLATE_DIR):
        return []
    result = []
    for path in sorted(glob.glob(os.path.join(TEMPLATE_DIR, "*.json"))):
        try:
            with open(path, "r", encoding="utf-8") as f:
                result.append(OrgTemplate.from_dict(json.load(f)))
        except (json.JSONDecodeError, OSError):
            continue
    return result


def import_template(json_text: str) -> OrgTemplate:
    data = json.loads(json_text)
    return OrgTemplate.from_dict(data)


def export_template(template: OrgTemplate) -> str:
    return json.dumps(template.to_dict(), ensure_ascii=False, indent=2)


def template_from_current_structure(entries: list[FileEntry], name: str) -> OrgTemplate:
    """현재 폴더의 최상위 하위 폴더들을 그대로 템플릿 폴더 목록으로 삼는다."""
    top_dirs = sorted(
        {
            e.relative_path.replace("\\", "/").split("/")[0]
            for e in entries
            if "/" in e.relative_path.replace("\\", "/")
        }
    )
    folders = [{"path": d, "description": ""} for d in top_dirs] or [
        dict(f) for f in DEFAULT_FOLDERS
    ]
    if not any(f["path"] == UNCLASSIFIED_FOLDER for f in folders):
        folders.append({"path": UNCLASSIFIED_FOLDER, "description": "규칙/AI로 분류하지 못한 파일"})
    return OrgTemplate(name=name, folders=folders, keyword_rules=[])


def duplicate_hint(entry: FileEntry) -> bool:
    name_lower = entry.name.lower()
    return any(kw.lower() in name_lower for kw in DUPLICATE_HINT_KEYWORDS)


def classify_by_rules(
    entries: list[FileEntry], template: OrgTemplate, user_rules: list[dict] | None = None
) -> dict[str, dict]:
    """규칙만으로 분류 가능한 파일에 대해 (신뢰도 '높음') 배정 결과를 만든다.

    규칙에 걸리지 않은 파일은 결과 dict에 포함되지 않는다(호출자가 AI 또는
    미분류 처리로 넘겨야 함). 반환값: {rel_path: {"dst", "reason", "confidence", "source"}}
    """
    rules = list(user_rules or []) + template.keyword_rules
    result: dict[str, dict] = {}
    for entry in entries:
        haystack = f"{entry.name} {entry.summary or ''}".lower()
        for rule in rules:
            keywords = rule.get("keywords", [])
            if any(kw.lower() in haystack for kw in keywords):
                target = rule["target"]
                filename = os.path.basename(entry.relative_path)
                result[entry.relative_path] = {
                    "dst": f"{target}/{filename}",
                    "reason": f"파일명/요약에 '{[kw for kw in keywords if kw.lower() in haystack][0]}' 키워드 포함",
                    "confidence": "높음",
                    "source": "rule",
                }
                break
    return result
