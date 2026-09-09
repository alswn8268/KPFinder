"""부서별 조직 표준 폴더 템플릿 샘플.

기본 템플릿(app.templates.default_template)은 부서를 가리지 않는 범용 사무 조직
체계다. 여기서는 시연 시 "우리 회계팀/개발팀/운영팀이라면 이렇게 쓰겠네"를
바로 보여줄 수 있도록, 부서별로 폴더 체계와 키워드 규칙을 다르게 짠 샘플
템플릿을 제공한다. 각 템플릿의 키워드 규칙은 sample_data/generate_sample_data.py의
해당 부서 문서 세트와 1:1로 맞춰져 있어, Ollama 없이 규칙만으로도 대부분의
파일이 올바른 폴더로 분류되는 것을 그대로 시연할 수 있다.
"""

from app.templates import UNCLASSIFIED_FOLDER, OrgTemplate


def _folders(pairs: list[tuple[str, str]]) -> list[dict]:
    folders = [{"path": path, "description": desc} for path, desc in pairs]
    folders.append({"path": UNCLASSIFIED_FOLDER, "description": "규칙/AI로 분류하지 못한 파일"})
    return folders


DEV_TEAM = OrgTemplate(
    name="개발팀 표준 템플릿",
    author="샘플",
    folders=_folders(
        [
            ("01_기획·요구사항", "신규 기능 기획서, 요구사항 정의"),
            ("02_설계·아키텍처", "DB 스키마, 아키텍처 설계서"),
            ("03_API·기술문서", "API 명세서, 기술 문서"),
            ("04_테스트·QA", "테스트 결과, QA 리포트"),
            ("05_배포·운영", "배포 체크리스트, 배포 절차"),
            ("06_장애·인시던트", "장애 리포트, 포스트모템, 온콜"),
            ("07_코드품질·컨벤션", "코드 리뷰 가이드, 기술부채"),
            ("08_회의록·스프린트", "주간 회의록, 스프린트 회고"),
            ("09_온보딩·매뉴얼", "신입 온보딩, 라이선스/환경 점검"),
            ("90_보관", "장기 보관용 자료"),
        ]
    ),
    keyword_rules=[
        {"keywords": ["기획서"], "target": "01_기획·요구사항"},
        {"keywords": ["설계서"], "target": "02_설계·아키텍처"},
        {"keywords": ["명세서"], "target": "03_API·기술문서"},
        {"keywords": ["QA", "테스트_결과"], "target": "04_테스트·QA"},
        {"keywords": ["배포"], "target": "05_배포·운영"},
        {"keywords": ["장애", "포스트모템", "온콜"], "target": "06_장애·인시던트"},
        {"keywords": ["코드리뷰", "기술부채"], "target": "07_코드품질·컨벤션"},
        {"keywords": ["회의록", "스프린트"], "target": "08_회의록·스프린트"},
        {"keywords": ["온보딩", "라이선스", "점검"], "target": "09_온보딩·매뉴얼"},
    ],
)

OPS_TEAM = OrgTemplate(
    name="운영팀 표준 템플릿",
    author="샘플",
    folders=_folders(
        [
            ("01_서비스운영현황", "주간/월간 서비스 운영 현황"),
            ("02_장애대응·포스트모템", "장애 대응 기록, 포스트모템"),
            ("03_모니터링·점검", "모니터링 점검표, 정기 점검"),
            ("04_배포이력", "정기/긴급 배포 이력"),
            ("05_SLA·성능리포트", "SLA 달성 현황, 성능 리포트"),
            ("06_CS이슈대응", "고객 문의/이슈 로그"),
            ("07_온콜·교대관리", "온콜 스케줄, 교대 관리"),
            ("08_벤더·외주관리", "외주/벤더사 점검 및 관리"),
            ("09_운영매뉴얼", "운영 절차 매뉴얼"),
            ("10_회의록", "운영팀 주간 회의록"),
            ("90_보관", "장기 보관용 자료"),
        ]
    ),
    keyword_rules=[
        {"keywords": ["포스트모템"], "target": "02_장애대응·포스트모템"},
        {"keywords": ["매뉴얼"], "target": "09_운영매뉴얼"},
        {"keywords": ["배포_이력", "배포이력"], "target": "04_배포이력"},
        {"keywords": ["운영현황"], "target": "01_서비스운영현황"},
        {"keywords": ["모니터링", "점검표"], "target": "03_모니터링·점검"},
        {"keywords": ["SLA", "성능리포트"], "target": "05_SLA·성능리포트"},
        {"keywords": ["CS_이슈", "이슈_로그"], "target": "06_CS이슈대응"},
        {"keywords": ["온콜", "교대"], "target": "07_온콜·교대관리"},
        {"keywords": ["벤더"], "target": "08_벤더·외주관리"},
        {"keywords": ["회의록"], "target": "10_회의록"},
    ],
)

FINANCE_TEAM = OrgTemplate(
    name="회계팀 표준 템플릿",
    author="샘플",
    folders=_folders(
        [
            ("01_법인카드·경비정산", "법인카드 정산, 출장비, 경비"),
            ("02_세금계산서·부가세", "세금계산서, 부가세 신고자료"),
            ("03_급여·4대보험", "급여명세, 4대보험 신고"),
            ("04_예산·결산·자산관리", "예산 집행, 결산보고서, 고정자산"),
            ("05_감사·내부통제", "내부통제 점검, 외부감사 대응"),
            ("06_계약·계좌관리", "거래처 계약서, 계좌 관리"),
            ("07_회의록", "회계팀 주간 회의록"),
            ("90_보관", "장기 보관용 자료"),
        ]
    ),
    keyword_rules=[
        {"keywords": ["법인카드", "출장비", "경비"], "target": "01_법인카드·경비정산"},
        {"keywords": ["세금계산서", "부가세"], "target": "02_세금계산서·부가세"},
        {"keywords": ["급여", "4대보험"], "target": "03_급여·4대보험"},
        {"keywords": ["예산", "결산", "고정자산"], "target": "04_예산·결산·자산관리"},
        {"keywords": ["내부통제", "외부감사"], "target": "05_감사·내부통제"},
        {"keywords": ["계좌", "거래처_계약서"], "target": "06_계약·계좌관리"},
        {"keywords": ["회의록"], "target": "07_회의록"},
    ],
)

SAMPLE_TEMPLATES: dict[str, dict] = {
    "dev_team": {
        "label": "개발팀 표준 템플릿",
        "description": "기획·설계·API 문서, 배포/장애 대응, 스프린트 회의록 중심 폴더 체계",
        "template": DEV_TEAM,
    },
    "ops_team": {
        "label": "운영팀 표준 템플릿",
        "description": "서비스 운영 현황, 장애·모니터링, SLA/CS 대응 중심 폴더 체계",
        "template": OPS_TEAM,
    },
    "finance_team": {
        "label": "회계팀 표준 템플릿",
        "description": "법인카드·경비, 세금계산서, 급여, 결산·감사 중심 폴더 체계",
        "template": FINANCE_TEAM,
    },
}


def list_sample_templates() -> list[OrgTemplate]:
    return [entry["template"] for entry in SAMPLE_TEMPLATES.values()]


def list_sample_template_meta() -> list[dict]:
    """이름/설명만 가벼운 dict로 (템플릿 상세는 list_sample_templates에서)."""
    return [
        {"key": key, "label": entry["label"], "description": entry["description"]}
        for key, entry in SAMPLE_TEMPLATES.items()
    ]
