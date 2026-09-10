// 한글 상태/신뢰도/출처 문자열 -> 배지 색 토큰/아이콘 매핑. 백엔드가 그대로 한글 문자열을
// 내려주므로(§7.11 등 명세서 표기를 그대로 따름) 여기서 표시용 스타일만 입힌다.

export type BadgeTone = 'success' | 'warning' | 'danger' | 'info' | 'neutral' | 'accent'

export const CONFIDENCE_TONE: Record<string, BadgeTone> = {
  높음: 'success',
  보통: 'info',
  낮음: 'warning',
}

export const FINAL_STATE_TONE: Record<string, BadgeTone> = {
  이동: 'accent',
  유지: 'neutral',
  제외: 'neutral',
  '검토 필요': 'warning',
  충돌: 'danger',
  차단: 'danger',
  오류: 'danger',
}

export const SOURCE_LABEL: Record<string, string> = {
  rule: '규칙',
  ai: 'AI',
  user: '사용자',
  fallback: '미분류',
  rename: '이름변경',
}

export const SUMMARY_STATUS_LABEL: Record<string, string> = {
  pending: '대기',
  ok: '완료',
  empty: '내용 없음',
  unsupported: '미지원 형식',
  failed: '요약 불가',
  hwp: '파일명 기반 분류',
  encrypted: '암호화 문서',
  ocr_needed: 'OCR 필요',
}

export const ENV_STATUS_TONE: Record<string, BadgeTone> = {
  정상: 'success',
  주의: 'warning',
  오류: 'danger',
}
