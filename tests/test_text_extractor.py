import zipfile

import pytest

from app.text_extractor import HwpParseError, extract_text, is_supported


def test_is_supported_includes_hwp_and_hwpx():
    assert is_supported(".hwpx")
    assert is_supported(".hwp")
    assert is_supported(".txt")
    assert not is_supported(".zip")


def test_extract_hwpx_reads_section_text(tmp_path):
    path = tmp_path / "sample.hwpx"
    section_xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<hp:sec xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph">'
        "<hp:p><hp:run><hp:t>연차 휴가 신청 절차 안내</hp:t></hp:run></hp:p>"
        "</hp:sec>"
    )
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("Contents/section0.xml", section_xml)
        zf.writestr("Contents/content.hpf", "<dummy/>")

    text = extract_text(str(path), ".hwpx")
    assert "연차 휴가 신청 절차 안내" in text


def test_extract_hwp_falls_back_gracefully_on_garbage_bytes(tmp_path):
    path = tmp_path / "broken.hwp"
    path.write_bytes(b"not a real hwp file")

    with pytest.raises(HwpParseError):
        extract_text(str(path), ".hwp")
