"""지원 형식(.txt/.docx/.xlsx/.csv/.pptx/.pdf)에서 텍스트를 추출한다.

.hwp/.hwpx는 v1 범위 밖(P2)이며 is_supported()가 False를 반환한다.
"""

import csv

from app.scanner import SUPPORTED_TEXT_EXTS


class ExtractionError(Exception):
    """텍스트 추출 중 발생한 오류."""


def is_supported(ext: str) -> bool:
    return ext.lower() in SUPPORTED_TEXT_EXTS


def extract_text(path: str, ext: str, max_chars: int = 4000) -> str:
    ext = ext.lower()
    try:
        if ext == ".txt":
            return _extract_txt(path, max_chars)
        if ext == ".docx":
            return _extract_docx(path, max_chars)
        if ext == ".csv":
            return _extract_csv(path, max_chars)
        if ext == ".xlsx":
            return _extract_xlsx(path, max_chars)
        if ext == ".pptx":
            return _extract_pptx(path, max_chars)
        if ext == ".pdf":
            return _extract_pdf(path, max_chars)
    except Exception as exc:  # noqa: BLE001 - 어떤 라이브러리든 실패는 추출 오류로 통일
        raise ExtractionError(f"{ext} 텍스트 추출 실패: {exc}") from exc
    raise ExtractionError(f"지원하지 않는 확장자: {ext}")


def _extract_txt(path: str, max_chars: int) -> str:
    for encoding in ("utf-8", "cp949", "euc-kr"):
        try:
            with open(path, "r", encoding=encoding) as f:
                return f.read(max_chars)
        except (UnicodeDecodeError, LookupError):
            continue
    with open(path, "rb") as f:
        return f.read(max_chars).decode("utf-8", errors="ignore")


def _extract_docx(path: str, max_chars: int) -> str:
    from docx import Document

    doc = Document(path)
    parts = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n".join(parts)[:max_chars]


def _extract_csv(path: str, max_chars: int) -> str:
    for encoding in ("utf-8", "cp949", "euc-kr"):
        try:
            lines = []
            total = 0
            with open(path, "r", encoding=encoding, newline="") as f:
                for row in csv.reader(f):
                    line = ", ".join(row)
                    lines.append(line)
                    total += len(line)
                    if total >= max_chars:
                        break
            return "\n".join(lines)[:max_chars]
        except (UnicodeDecodeError, LookupError):
            continue
    return ""


def _extract_xlsx(path: str, max_chars: int) -> str:
    from openpyxl import load_workbook

    wb = load_workbook(path, read_only=True, data_only=True)
    chunks = []
    total = 0
    for sheet in wb.worksheets:
        chunks.append(f"[시트: {sheet.title}]")
        for row in sheet.iter_rows(values_only=True):
            values = [str(v) for v in row if v is not None]
            if not values:
                continue
            line = ", ".join(values)
            chunks.append(line)
            total += len(line)
            if total >= max_chars:
                break
        if total >= max_chars:
            break
    return "\n".join(chunks)[:max_chars]


def _extract_pptx(path: str, max_chars: int) -> str:
    from pptx import Presentation

    prs = Presentation(path)
    chunks = []
    total = 0
    for i, slide in enumerate(prs.slides, start=1):
        texts = [
            shape.text_frame.text.strip()
            for shape in slide.shapes
            if shape.has_text_frame and shape.text_frame.text.strip()
        ]
        if texts:
            chunk = f"[슬라이드 {i}] " + " / ".join(texts)
            chunks.append(chunk)
            total += len(chunk)
        if total >= max_chars:
            break
    return "\n".join(chunks)[:max_chars]


def _extract_pdf(path: str, max_chars: int) -> str:
    from pypdf import PdfReader

    reader = PdfReader(path)
    chunks = []
    total = 0
    for page in reader.pages:
        text = page.extract_text() or ""
        if text.strip():
            chunks.append(text.strip())
            total += len(text)
        if total >= max_chars:
            break
    return "\n".join(chunks)[:max_chars]
