"""AI 폴더 정리 도우미 — Streamlit 데모 앱.

흐름: 스캔 -> (검색/그래프 탐색) -> AI 분석(요약 + 구조 제안) -> Before/After 비교 -> (승인 시) 적용.
AI는 '적용' 버튼을 누르기 전까지 어떤 파일도 이동/수정/삭제하지 않는다.
적용 후에는 버전 히스토리에 기록되어 언제든 되돌릴 수 있다.
"""

import os
from datetime import datetime

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from app import llm_client
from app.content_graph import GraphTooLargeError, render_content_graph
from app.directory_graph import render_directory_relation_graph, render_directory_tree
from app.file_ops import apply_move_plan, build_move_plan, undo_move_plan
from app.organizer import propose_structure, status_label, summarize_entries, validate_assignments
from app.report import build_report, render_current_tree, render_proposed_tree
from app.scanner import compute_hashes, find_duplicate_groups, scan_folder
from app.search import search_entries
from app.similar import find_similar_documents
from app.version_history import list_versions, mark_restored, record_version

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
    st.caption("실제로 파일을 이동한 뒤 되돌리려면 '🕘 버전 관리' 탭을 확인하세요.")

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
    (
        tab_scan,
        tab_dup,
        tab_dir_graph,
        tab_content_graph,
        tab_ai,
        tab_apply,
        tab_versions,
    ) = st.tabs(
        [
            "📋 스캔 결과",
            "🧬 중복 파일",
            "🗂️ 디렉토리 구조/연관도",
            "🕸️ 파일 연관도",
            "🤖 AI 분석 & 제안 구조",
            "🚀 적용",
            "🕘 버전 관리",
        ]
    )

    with tab_scan:
        st.subheader("🔍 검색")
        search_col, ext_col = st.columns([3, 1])
        with search_col:
            query = st.text_input(
                "파일명 / 경로 / AI 요약 내용으로 검색", key="search_query", placeholder="예: 영업보고서"
            )
        all_exts = sorted({e.ext or "(없음)" for e in entries})
        with ext_col:
            selected_exts = st.multiselect("확장자 필터", all_exts)

        if selected_exts:
            wanted_exts = {e for e in selected_exts if e != "(없음)"}
            include_no_ext = "(없음)" in selected_exts
            ext_filtered = [
                e for e in entries if (e.ext in wanted_exts) or (include_no_ext and not e.ext)
            ]
        else:
            ext_filtered = entries
        filtered = search_entries(ext_filtered, query=query)

        st.caption(f"전체 {len(entries)}개 중 {len(filtered)}개 표시")
        df = pd.DataFrame(
            [
                {
                    "경로": e.relative_path,
                    "이름": e.name,
                    "확장자": e.ext or "(없음)",
                    "크기(KB)": round(e.size / 1024, 1),
                    "수정일": e.modified.strftime("%Y-%m-%d %H:%M"),
                    "AI 요약": e.summary or "-",
                }
                for e in filtered
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

    with tab_dir_graph:
        st.caption(
            "Obsidian의 그래프 뷰에서 착안한 폴더 단위 시각화입니다. "
            "왼쪽은 폴더 계층 구조, 오른쪽은 서로 다른 폴더에 흩어진 파일들이 "
            "내용상 얼마나 비슷한지를 보여줍니다(병합 후보 힌트)."
        )
        col_tree, col_relation = st.columns(2)
        with col_tree:
            st.markdown("**폴더 구조도**")
            fig_tree = render_directory_tree(entries)
            st.pyplot(fig_tree)
            plt.close(fig_tree)
        with col_relation:
            st.markdown("**폴더 간 연관도**")
            relation_threshold = st.slider(
                "연관도 임계값", 0.1, 0.9, 0.4, 0.05, key="dir_relation_threshold"
            )
            fig_relation = render_directory_relation_graph(entries, min_score=relation_threshold)
            st.pyplot(fig_relation)
            plt.close(fig_relation)
            if not any(e.summary_status == "ok" for e in entries):
                st.caption("아직 AI 분석 전이라 파일명 유사도만 반영되어 있습니다. AI 분석 후 더 정확해집니다.")

    with tab_content_graph:
        st.caption(
            "노드 = 파일, 선 = 파일명/AI 요약 유사도. 임베딩 모델 없이 가볍게 추정한 값이라 "
            "완벽하지는 않지만, 어떤 문서끼리 관련 있어 보이는지 한눈에 훑어보는 용도입니다."
        )
        c1, c2, c3 = st.columns(3)
        with c1:
            content_threshold = st.slider("연관도 임계값", 0.1, 0.9, 0.35, 0.05, key="content_threshold")
        with c2:
            show_labels = st.checkbox("파일명 라벨 표시", value=True)
        with c3:
            hide_isolated = st.checkbox("연결 없는 파일 숨기기", value=True)

        try:
            fig_content, edges = render_content_graph(
                entries, min_score=content_threshold, show_labels=show_labels, hide_isolated=hide_isolated
            )
            st.pyplot(fig_content)
            plt.close(fig_content)
            st.caption(f"임계값 {content_threshold:.2f} 이상인 연결 {len(edges)}개")
        except GraphTooLargeError as exc:
            st.warning(str(exc))

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
                st.success("AI 분석이 완료되었습니다. '디렉토리 구조/연관도'와 '파일 연관도' 탭도 더 정확해집니다.")

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
                record_version(
                    st.session_state.scan_root,
                    log_path,
                    note=(proposal or {}).get("notes", ""),
                    files_moved=len(plan),
                )
                st.success(f"{len(plan)}개 파일 이동을 완료했습니다.")
                st.info("문제가 있다면 '🕘 버전 관리' 탭에서 이 작업을 되돌릴 수 있습니다.")

    with tab_versions:
        st.caption("'적용'을 누를 때마다 새로운 버전이 기록됩니다. 언제든 특정 버전을 골라 되돌릴 수 있습니다.")
        versions = list_versions(st.session_state.scan_root)
        if not versions:
            st.info("이 폴더에 대해 아직 적용된 정리 작업이 없습니다.")
        else:
            for v in reversed(versions):
                status = "✅ 적용됨" if not v["restored"] else "↩️ 되돌려짐"
                with st.expander(
                    f"{v['version_id']} — {v['timestamp']} ({v['files_moved']}개 파일 이동) [{status}]"
                ):
                    if v.get("note"):
                        st.write(v["note"])
                    if not v["restored"]:
                        if st.button("이 버전 되돌리기", key=f"restore_{v['version_id']}"):
                            restored = undo_move_plan(v["log_path"])
                            mark_restored(st.session_state.scan_root, v["version_id"])
                            st.success(f"{restored}개 파일을 원래 위치로 되돌렸습니다.")
                            st.rerun()
                    else:
                        st.caption("이미 되돌려진 버전입니다.")
