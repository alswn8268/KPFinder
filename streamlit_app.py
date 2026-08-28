"""AI 폴더 정리 도우미 — Streamlit 데모 앱.

흐름: 스캔 -> AI 분석(요약 + 구조 제안) -> Before/After 비교 -> (승인 시) 적용.
AI는 '적용' 버튼을 누르기 전까지 어떤 파일도 이동/수정/삭제하지 않는다.
"""

import os
from datetime import datetime

import pandas as pd
import streamlit as st

from app import llm_client
from app.file_ops import apply_move_plan, build_move_plan, list_move_logs, undo_move_plan
from app.organizer import propose_structure, status_label, summarize_entries, validate_assignments
from app.report import build_report, render_current_tree, render_proposed_tree
from app.scanner import compute_hashes, find_duplicate_groups, scan_folder
from app.similar import find_similar_documents

st.set_page_config(page_title="AI 폴더 정리 도우미", layout="wide")

for key, default in (
    ("entries", []),
    ("duplicate_groups", {}),
    ("proposal", None),
    ("scan_root", ""),
    ("similar_docs", []),
):
    if key not in st.session_state:
        st.session_state[key] = default

st.title("📁 AI 폴더 정리 도우미")
st.caption(
    "스캔 → AI 제안 → 사람이 확인 → 적용. "
    "AI는 절대 자동으로 파일을 옮기지 않으며, 모든 처리는 로컬에서만 이루어집니다."
)

with st.sidebar:
    st.header("설정")
    folder_path = st.text_input("정리할 폴더 경로", value=st.session_state.scan_root)
    model_name = st.text_input("Ollama 모델", value=llm_client.DEFAULT_MODEL)

    ollama_ok = llm_client.check_connection()
    if ollama_ok:
        st.success("Ollama 연결됨")
    else:
        st.error("Ollama에 연결할 수 없습니다. `ollama serve` 실행 여부를 확인하세요.")

    scan_clicked = st.button("1️⃣ 스캔", use_container_width=True)
    analyze_clicked = st.button(
        "2️⃣ AI 분석", use_container_width=True, disabled=not st.session_state.entries
    )

    st.divider()
    st.caption("실행 취소 (적용된 이동 되돌리기)")
    logs = list_move_logs()
    if logs:
        selected_log = st.selectbox("되돌릴 이동 기록", logs, format_func=os.path.basename)
        if st.button("↩️ 선택한 이동 되돌리기", use_container_width=True):
            restored = undo_move_plan(selected_log)
            st.success(f"{restored}개 파일을 원래 위치로 되돌렸습니다.")
    else:
        st.caption("되돌릴 이동 기록이 없습니다.")

if scan_clicked:
    if not folder_path or not os.path.isdir(folder_path):
        st.error("올바른 폴더 경로를 입력하세요.")
    else:
        with st.spinner("폴더 스캔 중..."):
            scanned_entries = scan_folder(folder_path)
            compute_hashes(scanned_entries)
            dup_groups = find_duplicate_groups(scanned_entries)
        st.session_state.entries = scanned_entries
        st.session_state.duplicate_groups = dup_groups
        st.session_state.scan_root = folder_path
        st.session_state.proposal = None
        st.session_state.similar_docs = []
        st.success(f"{len(scanned_entries)}개 파일을 찾았습니다.")

entries = st.session_state.entries

if not entries:
    st.info("왼쪽에서 폴더 경로를 입력하고 '스캔'을 눌러 시작하세요.")
else:
    tab_scan, tab_dup, tab_ai, tab_apply = st.tabs(
        ["📋 스캔 결과", "🧬 중복 파일", "🤖 AI 분석 & 제안 구조", "🚀 적용"]
    )

    with tab_scan:
        df = pd.DataFrame(
            [
                {
                    "경로": e.relative_path,
                    "이름": e.name,
                    "확장자": e.ext or "(없음)",
                    "크기(KB)": round(e.size / 1024, 1),
                    "수정일": e.modified.strftime("%Y-%m-%d %H:%M"),
                }
                for e in entries
            ]
        )
        st.dataframe(df, use_container_width=True, hide_index=True)

        st.subheader("확장자별 파일 수")
        st.bar_chart(df["확장자"].value_counts())

        st.subheader("폴더별 파일 수")
        folder_of = df["경로"].apply(lambda p: os.path.dirname(p) or "(최상위)")
        st.bar_chart(folder_of.value_counts())

    with tab_dup:
        dup_groups = st.session_state.duplicate_groups
        if not dup_groups:
            st.info("완전 중복 파일이 없습니다.")
        else:
            total_dup_files = sum(len(v) for v in dup_groups.values())
            wasted_kb = sum(v[0].size * (len(v) - 1) for v in dup_groups.values()) / 1024
            st.warning(
                f"완전 중복 그룹 {len(dup_groups)}개, 중복 파일 {total_dup_files}개 "
                f"(불필요하게 차지하는 용량 약 {wasted_kb:.1f} KB)"
            )
            for group in dup_groups.values():
                with st.expander(f"동일 파일 {len(group)}개 — {group[0].name}"):
                    for e in group:
                        st.write(
                            f"- `{e.relative_path}` "
                            f"({round(e.size / 1024, 1)} KB, {e.modified:%Y-%m-%d})"
                        )

    with tab_ai:
        if analyze_clicked:
            if not ollama_ok:
                st.error("Ollama 연결을 먼저 확인하세요.")
            else:
                progress = st.progress(0.0, text="AI 분석 준비 중...")

                def on_progress(i: int, total: int, entry) -> None:
                    progress.progress(i / total, text=f"({i}/{total}) {entry.name} 요약 중...")

                summarize_entries(
                    entries, st.session_state.scan_root, model_name, progress_cb=on_progress
                )

                progress.progress(1.0, text="요약 완료. 폴더 구조 제안 생성 중...")
                try:
                    st.session_state.proposal = propose_structure(entries, model_name)
                except llm_client.OllamaError as exc:
                    st.error(f"폴더 구조 제안 생성 실패: {exc}")
                    st.session_state.proposal = None

                st.session_state.similar_docs = find_similar_documents(entries)
                progress.empty()
                st.success("AI 분석이 완료되었습니다.")

        if any(e.summary_status != "pending" for e in entries):
            st.subheader("파일별 요약")
            summary_df = pd.DataFrame(
                [
                    {
                        "경로": e.relative_path,
                        "상태": status_label(e.summary_status),
                        "요약": e.summary or "-",
                    }
                    for e in entries
                ]
            )
            st.dataframe(summary_df, use_container_width=True, hide_index=True)

        if st.session_state.similar_docs:
            st.subheader("🔎 유사 문서 (버전이 다를 수 있는 파일)")
            for a, b, score in st.session_state.similar_docs[:20]:
                st.write(f"- `{a.relative_path}` ↔ `{b.relative_path}` (유사도 {score:.0%})")

        proposal = st.session_state.proposal
        if proposal:
            assignments = validate_assignments(entries, proposal.get("assignments", {}))

            st.subheader("Before / After 폴더 구조 비교")
            col_before, col_after = st.columns(2)
            with col_before:
                st.markdown("**현재 구조**")
                st.code(render_current_tree(entries), language="text")
            with col_after:
                st.markdown("**제안된 구조**")
                st.code(render_proposed_tree(assignments), language="text")

            if proposal.get("notes"):
                st.info(proposal["notes"])

            report_json = build_report(
                entries, st.session_state.duplicate_groups, proposal, st.session_state.similar_docs
            )
            st.download_button(
                "📥 리포트 다운로드 (JSON)",
                data=report_json,
                file_name=f"folder_organize_report_{datetime.now():%Y%m%d_%H%M%S}.json",
                mime="application/json",
            )

    with tab_apply:
        proposal = st.session_state.proposal
        assignments = validate_assignments(entries, (proposal or {}).get("assignments", {}))
        if not assignments:
            st.info("먼저 'AI 분석' 탭에서 제안 구조를 생성하세요.")
        else:
            plan = build_move_plan(st.session_state.scan_root, assignments)
            st.warning(f"{len(plan)}개 파일이 이동됩니다. 적용 전 아래 내용을 반드시 확인하세요.")
            plan_df = pd.DataFrame(
                [{"기존 경로": p["rel_src"], "새 경로": p["rel_dst"]} for p in plan]
            )
            st.dataframe(plan_df, use_container_width=True, hide_index=True)

            confirm = st.checkbox("위 이동 계획을 확인했으며, 실제로 파일을 이동하는 데 동의합니다.")
            if st.button("🚀 적용 (실제 파일 이동)", type="primary", disabled=not confirm):
                log_path = apply_move_plan(plan)
                st.success(f"{len(plan)}개 파일 이동을 완료했습니다. 이동 기록: `{log_path}`")
                st.info("문제가 있다면 사이드바의 '실행 취소' 기능으로 되돌릴 수 있습니다.")
