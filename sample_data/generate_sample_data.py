"""데모용 '어질러진' 샘플 업무 폴더를 생성한다.

부서별로 이름 규칙이 제각각인 문서들을 무작위 하위 폴더에 흩어 놓고, 내용까지
완전히 동일한 중복 파일 몇 개를 섞어 완전 중복 탐지 데모를 지원한다. 비슷한
제목/내용의 v1, v2, final류 문서도 포함해 유사 문서 탐지 데모도 가능하다.

기본(general_office) 외에 개발팀/운영팀/회계팀 시나리오를 추가로 제공한다 —
각 시나리오의 문서 제목은 sample_data/org_templates.py의 같은 부서 템플릿
키워드 규칙과 맞춰져 있어, AI 없이 규칙 기반 분류만으로도 정리되는 것을
그대로 시연할 수 있다.

사용법:
    python sample_data/generate_sample_data.py [출력경로] [--force] [--dataset KEY]
    (기본 출력경로: sample_data/messy_folder, 기본 데이터셋: general_office)
    출력 폴더가 이미 있으면 기본적으로 삭제하지 않는다. 덮어쓰려면 --force를 붙인다.
"""

import csv
import os
import random
import shutil
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))

OUTPUT_DEFAULT = os.path.join(_HERE, "messy_folder")

FOLDER_CHOICES = ["", "새 폴더", "새 폴더 (2)", "임시", "정리필요", "backup_old"]

# (파일명, 본문) — 일부러 이름 규칙이 제각각이고 비슷한 내용의 버전이 섞여 있다.
DOCS_GENERAL_OFFICE = [
    ("2026년_1분기_영업보고서", "1분기 영업 실적 보고서입니다. 매출은 전년 대비 12% 증가했으며, 신규 거래처는 8곳입니다."),
    ("1분기영업보고서_최종", "1분기 영업 실적 보고서입니다. 매출은 전년 대비 12% 증가했으며, 신규 거래처는 8곳입니다."),
    ("1분기_영업보고서_final_v2", "1분기 영업 실적 보고서 수정본입니다. 매출은 전년 대비 12% 증가, 신규 거래처는 9곳으로 정정되었습니다."),
    ("신입사원_교육자료", "신입사원 온보딩 교육 자료입니다. 사내 시스템 사용법과 보안 정책을 안내합니다."),
    ("2026_신입사원_오리엔테이션", "신입사원 온보딩 교육 자료입니다. 사내 시스템 사용법과 보안 정책을 함께 안내합니다."),
    ("거래처_연락처_목록", "주요 거래처 담당자 연락처와 이메일을 정리한 목록입니다."),
    ("거래처연락처_수정", "주요 거래처 담당자 연락처와 이메일을 정리한 목록입니다. 담당자 2명이 변경되었습니다."),
    ("출장비_정산_양식", "해외 출장비 정산을 위한 양식과 작성 예시를 담은 문서입니다."),
    ("회의록_0212_마케팅팀", "2월 12일 마케팅팀 주간 회의록입니다. 신제품 캠페인 일정을 논의했습니다."),
    ("회의록_0219_마케팅팀", "2월 19일 마케팅팀 주간 회의록입니다. 캠페인 예산안을 확정했습니다."),
    ("연차_사용_규정", "연차 휴가 신청 절차와 사용 규정을 안내하는 문서입니다."),
    ("사내_보안_정책_v3", "사내 정보보안 정책 최신본입니다. 외부 반출 금지 항목을 포함합니다."),
    ("경쟁사_분석_2026", "주요 경쟁사 3곳의 최근 제품 및 가격 전략을 분석한 자료입니다."),
    ("고객_설문_결과_요약", "지난달 진행한 고객 만족도 설문 결과를 요약한 자료입니다."),
    ("신제품_기획안_초안", "신제품 A의 기획 배경과 목표 시장을 정리한 초안입니다."),
    ("신제품_기획안_v2_검토중", "신제품 A의 기획안 2차 수정본입니다. 목표 출시일이 조정되었습니다."),
    ("예산안_2026_하반기", "2026년 하반기 부서별 예산 배정안을 정리한 문서입니다."),
    ("복리후생_안내", "임직원 복리후생 제도 전체를 안내하는 문서입니다."),
    ("협력사_계약서_초안", "신규 협력사와의 계약서 초안입니다. 법무 검토 전 버전입니다."),
    ("팀빌딩_행사_계획", "3분기 팀빌딩 행사 일정과 장소 후보를 정리한 계획안입니다."),
    ("입출금_내역_3월", "3월 법인카드 입출금 내역을 정리한 파일입니다."),
    ("입출금내역_3월_수정", "3월 법인카드 입출금 내역을 정리한 파일입니다. 오류 항목 1건을 수정했습니다."),
    ("워크숍_참가자_명단", "하반기 워크숍 참가 신청자 명단을 정리한 문서입니다."),
    ("사무용품_구매_요청서", "사무용품 구매를 위한 결재 요청서 양식입니다."),
    ("IT_자산_관리대장", "부서별로 지급된 노트북 및 IT 자산을 관리하는 대장입니다."),
    ("연간_행사_일정표", "2026년 사내 연간 행사 및 휴무 일정표입니다."),
    ("퇴사자_인수인계_체크리스트", "퇴사 예정자의 업무 인수인계를 위한 체크리스트 양식입니다."),
    ("고객사_A_제안서_초안", "고객사 A를 대상으로 한 신규 서비스 제안서 초안입니다."),
    ("고객사_A_제안서_v2", "고객사 A 대상 제안서 2차 수정본입니다. 가격 조건이 변경되었습니다."),
    ("품질관리_점검표", "생산 라인의 품질관리 월간 점검표입니다."),
]
DUP_GENERAL_OFFICE = {
    "content": "표준 사업자등록증 사본 요청 양식입니다. 담당 부서에 제출하세요.",
    "targets": [
        ("", "사업자등록증_요청양식.txt"),
        ("임시", "사업자등록증_요청양식_복사본.txt"),
        ("backup_old", "사업자등록증양식(1).txt"),
        ("새 폴더", "사업자등록증_요청양식_최종.txt"),
    ],
}

DOCS_DEV_TEAM = [
    ("API_명세서_v1", "회원 인증 API 명세서 초안입니다. 로그인/토큰 재발급 엔드포인트를 정의합니다."),
    ("API_명세서_최종", "회원 인증 API 명세서입니다. 로그인/토큰 재발급 엔드포인트를 정의합니다. 리뷰 반영 완료."),
    ("배포_체크리스트", "운영 배포 전 확인해야 할 항목을 정리한 체크리스트입니다."),
    ("장애리포트_0304_결제모듈", "3월 4일 결제 모듈 장애의 원인과 재발 방지 대책을 정리한 포스트모템입니다."),
    ("스프린트_회고_3월2주차", "3월 2주차 스프린트 회고 내용입니다. 잘한 점과 개선할 점을 정리했습니다."),
    ("코드리뷰_가이드", "팀 내 코드 리뷰 시 지켜야 할 규칙과 체크포인트를 정리한 가이드입니다."),
    ("DB_스키마_설계서_v2", "주문/결제 도메인 DB 스키마 설계서 2차 수정본입니다. 인덱스 전략이 추가되었습니다."),
    ("DB_스키마_설계서_초안", "주문/결제 도메인 DB 스키마 설계서 초안입니다."),
    ("온콜_대응_매뉴얼", "야간 온콜 발생 시 대응 절차와 에스컬레이션 기준을 정리한 매뉴얼입니다."),
    ("오픈소스_라이선스_점검표", "프로젝트에서 사용 중인 오픈소스 라이브러리의 라이선스를 점검한 표입니다."),
    ("신규기능_기획서_추천시스템", "추천 시스템 신규 기능의 배경과 목표를 정리한 기획서입니다."),
    ("테스트_결과_회원가입_QA", "회원가입 플로우에 대한 QA 테스트 결과 보고서입니다."),
    ("회의록_0306_백엔드팀", "3월 6일 백엔드팀 주간 회의록입니다. API 일정과 우선순위를 논의했습니다."),
    ("회의록_0313_백엔드팀", "3월 13일 백엔드팀 주간 회의록입니다. DB 마이그레이션 일정을 확정했습니다."),
    ("성능개선_리포트_검색기능", "검색 기능 응답 속도 개선 작업 결과를 정리한 리포트입니다."),
    ("신입_개발자_온보딩_가이드", "신입 개발자를 위한 개발 환경 세팅과 사내 컨벤션 안내 가이드입니다."),
    ("서버_점검_안내_0310", "3월 10일 새벽 정기 서버 점검 안내 공지입니다."),
    ("기술부채_정리_계획", "우선순위가 높은 기술부채 항목과 정리 계획을 정리한 문서입니다."),
]
DUP_DEV_TEAM = {
    "content": "사내 VPN 접속 신청 양식입니다. 팀장 승인 후 IT팀에 제출하세요.",
    "targets": [
        ("", "VPN_접속_신청서.txt"),
        ("backup_old", "VPN_접속_신청서_구버전.txt"),
        ("임시", "VPN_접속_신청서_복사본.txt"),
        ("새 폴더", "VPN_접속_신청서(1).txt"),
    ],
}

DOCS_OPS_TEAM = [
    ("장애_포스트모템_0228_로그인지연", "2월 28일 로그인 지연 장애의 타임라인과 원인, 재발 방지 대책을 정리한 포스트모템입니다."),
    ("주간_서비스운영현황_3월1주", "3월 1주차 서비스 가동률과 주요 이슈를 정리한 운영 현황 보고서입니다."),
    ("주간_서비스운영현황_3월2주", "3월 2주차 서비스 가동률과 주요 이슈를 정리한 운영 현황 보고서입니다."),
    ("배포_이력_2026_1분기", "1분기 정기/긴급 배포 이력을 정리한 문서입니다."),
    ("모니터링_점검표_일일", "매일 아침 확인해야 할 모니터링 대시보드 점검 항목표입니다."),
    ("SLA_성능리포트_2월", "2월 서비스 응답시간과 가동률 SLA 달성 현황 리포트입니다."),
    ("CS_이슈_로그_결제오류", "결제 오류 관련 고객 문의 이슈 로그와 처리 현황입니다."),
    ("온콜_교대_스케줄_3월", "3월 온콜 담당자 교대 스케줄표입니다."),
    ("벤더_점검_보고서_CDN사", "CDN 벤더사 정기 점검 결과 보고서입니다."),
    ("운영_매뉴얼_배포절차_v2", "서비스 배포 절차 운영 매뉴얼 2차 수정본입니다. 롤백 절차가 추가되었습니다."),
    ("운영_매뉴얼_배포절차_초안", "서비스 배포 절차 운영 매뉴얼 초안입니다."),
    ("회의록_0305_운영팀", "3월 5일 운영팀 주간 회의록입니다. 장애 대응 프로세스를 개선하기로 했습니다."),
    ("회의록_0312_운영팀", "3월 12일 운영팀 주간 회의록입니다. 신규 모니터링 도구 도입을 논의했습니다."),
    ("재해복구_훈련_결과보고", "분기별 재해복구(DR) 훈련 결과와 개선 사항을 정리한 보고서입니다."),
    ("용량_증설_계획_스토리지", "스토리지 용량 증설 계획과 예상 비용을 정리한 문서입니다."),
    ("보안_점검_결과_3월", "3월 정기 보안 취약점 점검 결과 요약입니다."),
    ("긴급_공지_서비스점검_0309", "3월 9일 새벽 긴급 서비스 점검 공지문입니다."),
]
DUP_OPS_TEAM = {
    "content": "서버 접근 권한 신청 양식입니다. 보안팀 승인 후 계정이 발급됩니다.",
    "targets": [
        ("", "서버_접근권한_신청서.txt"),
        ("backup_old", "서버_접근권한_신청서_구양식.txt"),
        ("정리필요", "서버_접근권한_신청서_사본.txt"),
        ("새 폴더 (2)", "서버_접근권한_신청서_최종.txt"),
    ],
}

DOCS_FINANCE_TEAM = [
    ("3월_법인카드_정산내역", "3월 법인카드 사용 내역과 정산 결과를 정리한 문서입니다."),
    ("3월_법인카드_정산내역_수정", "3월 법인카드 사용 내역 정산 결과입니다. 오류 항목 2건을 수정했습니다."),
    ("2026_1분기_예산집행_현황", "1분기 부서별 예산 집행 현황을 정리한 보고서입니다."),
    ("세금계산서_발행목록_2월", "2월 발행한 세금계산서 목록과 금액을 정리한 문서입니다."),
    ("급여명세_요약_2월", "2월 전체 급여 지급 요약 내역입니다. 개인정보는 마스킹 처리되었습니다."),
    ("4대보험_신고_체크리스트", "매월 4대보험 신고 시 확인해야 할 항목 체크리스트입니다."),
    ("결산보고서_초안_2025", "2025년 연간 결산보고서 초안입니다."),
    ("결산보고서_v2_2025", "2025년 연간 결산보고서 2차 수정본입니다. 감사 의견이 반영되었습니다."),
    ("부가세_신고자료_1분기", "1분기 부가가치세 신고를 위한 매입/매출 자료입니다."),
    ("계좌_변경_신청서", "거래처 정산 계좌 변경을 위한 신청서 양식입니다."),
    ("내부통제_점검표_3월", "3월 회계 내부통제 점검 항목표입니다."),
    ("외부감사_대응_자료", "외부 회계감사 대응을 위해 준비한 자료 목록입니다."),
    ("회의록_0307_회계팀", "3월 7일 회계팀 주간 회의록입니다. 결산 일정을 논의했습니다."),
    ("회의록_0314_회계팀", "3월 14일 회계팀 주간 회의록입니다. 세무조사 대비 자료를 점검했습니다."),
    ("거래처_계약서_보관목록", "회계팀이 보관 중인 거래처 계약서 목록입니다."),
    ("출장비_정산_규정_개정안", "출장비 정산 규정 개정안입니다. 한도 금액이 조정되었습니다."),
    ("고정자산_관리대장", "회사 보유 고정자산 목록과 감가상각 현황을 관리하는 대장입니다."),
]
DUP_FINANCE_TEAM = {
    "content": "경비 정산 신청 양식입니다. 영수증을 첨부해 팀장 결재 후 제출하세요.",
    "targets": [
        ("", "경비_정산_신청서.txt"),
        ("backup_old", "경비_정산_신청서_구버전.txt"),
        ("임시", "경비_정산_신청서_복사본.txt"),
        ("정리필요", "경비_정산_신청서(1).txt"),
    ],
}

DATASETS: dict[str, dict] = {
    "general_office": {
        "label": "일반 사무팀 (총무·영업·마케팅 혼재)",
        "description": "부서 구분 없이 뒤섞인 전형적인 '어질러진 공유폴더' — 처음 시연할 때 기본으로 쓰기 좋습니다.",
        "output_dir": OUTPUT_DEFAULT,
        "docs": DOCS_GENERAL_OFFICE,
        "duplicates": DUP_GENERAL_OFFICE,
    },
    "dev_team": {
        "label": "개발팀",
        "description": "기획/설계/API 문서, 배포·장애 대응, 스프린트 회의록이 섞인 개발팀 폴더.",
        "output_dir": os.path.join(_HERE, "messy_folder_dev"),
        "docs": DOCS_DEV_TEAM,
        "duplicates": DUP_DEV_TEAM,
    },
    "ops_team": {
        "label": "운영팀",
        "description": "서비스 운영 현황, 장애 포스트모템, 모니터링/SLA 리포트가 섞인 운영팀 폴더.",
        "output_dir": os.path.join(_HERE, "messy_folder_ops"),
        "docs": DOCS_OPS_TEAM,
        "duplicates": DUP_OPS_TEAM,
    },
    "finance_team": {
        "label": "회계팀",
        "description": "법인카드·경비 정산, 세금계산서, 급여, 결산 자료가 섞인 회계팀 폴더.",
        "output_dir": os.path.join(_HERE, "messy_folder_finance"),
        "docs": DOCS_FINANCE_TEAM,
        "duplicates": DUP_FINANCE_TEAM,
    },
}


def list_datasets() -> list[dict]:
    """생성 가능한 데이터셋 목록(키/라벨/설명/기본 출력 경로)을 반환한다."""
    return [
        {
            "key": key,
            "label": spec["label"],
            "description": spec["description"],
            "output_dir": spec["output_dir"],
        }
        for key, spec in DATASETS.items()
    ]


def _write_txt(target_dir: str, filename: str, content: str) -> None:
    os.makedirs(target_dir, exist_ok=True)
    with open(os.path.join(target_dir, filename), "w", encoding="utf-8") as f:
        f.write(content + "\n\n작성자: 기획팀\n작성일: 2026\n")


def _write_csv(target_dir: str, filename: str, content: str) -> None:
    os.makedirs(target_dir, exist_ok=True)
    with open(os.path.join(target_dir, filename), "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["항목", "내용"])
        writer.writerow(["요약", content])
        writer.writerow(["상태", "임시"])


def _write_docx(target_dir: str, filename: str, content: str) -> bool:
    try:
        from docx import Document
    except ImportError:
        return False
    os.makedirs(target_dir, exist_ok=True)
    doc = Document()
    for line in content.split("\n"):
        doc.add_paragraph(line)
    doc.save(os.path.join(target_dir, filename))
    return True


def generate(
    output_dir: str | None = None,
    seed: int = 42,
    force: bool = False,
    dataset: str = "general_office",
) -> int:
    if dataset not in DATASETS:
        raise ValueError(f"알 수 없는 샘플 데이터셋입니다: {dataset} (선택 가능: {', '.join(DATASETS)})")
    spec = DATASETS[dataset]
    output_dir = output_dir or spec["output_dir"]

    random.seed(seed)
    if os.path.exists(output_dir):
        if not force:
            print(f"이미 존재하는 폴더입니다: {output_dir} (덮어쓰려면 --force 옵션을 사용하세요)")
            return 0
        shutil.rmtree(output_dir)
    os.makedirs(output_dir, exist_ok=True)

    created = 0
    for i, (title, content) in enumerate(spec["docs"]):
        folder = random.choice(FOLDER_CHOICES)
        target_dir = os.path.join(output_dir, folder) if folder else output_dir

        choice = i % 4
        if choice == 0:
            _write_txt(target_dir, f"{title}.txt", content)
        elif choice == 1:
            if not _write_docx(target_dir, f"{title}.docx", content):
                _write_txt(target_dir, f"{title}.txt", content)
        elif choice == 2:
            _write_csv(target_dir, f"{title}.csv", content)
        else:
            _write_txt(target_dir, f"{title}.txt", content)
        created += 1

    # 완전 중복 파일(내용까지 동일)을 서로 다른 폴더/이름으로 여러 개 생성
    dup = spec["duplicates"]
    for folder, name in dup["targets"]:
        target_dir = os.path.join(output_dir, folder) if folder else output_dir
        _write_txt(target_dir, name, dup["content"])
        created += 1

    print(f"샘플 폴더 생성 완료: {output_dir} ({created}개 파일, 데이터셋: {dataset})")
    return created


if __name__ == "__main__":
    raw_args = sys.argv[1:]
    force_flag = "--force" in raw_args
    dataset_key = "general_office"
    if "--dataset" in raw_args:
        idx = raw_args.index("--dataset")
        dataset_key = raw_args[idx + 1]
        del raw_args[idx : idx + 2]
    positional = [a for a in raw_args if a != "--force"]
    out_dir = positional[0] if positional else None
    generate(out_dir, force=force_flag, dataset=dataset_key)
