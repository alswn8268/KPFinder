"""데모용 '어질러진' 샘플 업무 폴더를 생성한다.

이름 규칙이 제각각인 문서 30여 개를 무작위 하위 폴더에 흩어 놓고,
내용까지 완전히 동일한 중복 파일 몇 개를 섞어 완전 중복 탐지 데모를 지원한다.
비슷한 제목/내용의 v1, v2, final류 문서도 포함해 유사 문서 탐지 데모도 가능하다.

사용법:
    python sample_data/generate_sample_data.py [출력경로]
    (기본 출력경로: sample_data/messy_folder)
"""

import csv
import os
import random
import shutil
import sys

OUTPUT_DEFAULT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "messy_folder")

# (파일명, 본문) — 일부러 이름 규칙이 제각각이고 비슷한 내용의 버전이 섞여 있다.
DOCS = [
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

FOLDER_CHOICES = ["", "새 폴더", "새 폴더 (2)", "임시", "정리필요", "backup_old"]


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


def generate(output_dir: str, seed: int = 42) -> int:
    random.seed(seed)
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir, exist_ok=True)

    created = 0
    for i, (title, content) in enumerate(DOCS):
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

    # 완전 중복 파일(내용까지 동일)을 서로 다른 폴더/이름으로 4개 생성
    dup_content = "표준 사업자등록증 사본 요청 양식입니다. 담당 부서에 제출하세요."
    for folder, name in [
        ("", "사업자등록증_요청양식.txt"),
        ("임시", "사업자등록증_요청양식_복사본.txt"),
        ("backup_old", "사업자등록증양식(1).txt"),
        ("새 폴더", "사업자등록증_요청양식_최종.txt"),
    ]:
        target_dir = os.path.join(output_dir, folder) if folder else output_dir
        _write_txt(target_dir, name, dup_content)
        created += 1

    print(f"샘플 폴더 생성 완료: {output_dir} ({created}개 파일)")
    return created


if __name__ == "__main__":
    out_dir = sys.argv[1] if len(sys.argv) > 1 else OUTPUT_DEFAULT
    generate(out_dir)
