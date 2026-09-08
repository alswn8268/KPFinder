"""AI 폴더 정리 도우미 — Streamlit 데모 앱.

흐름: 환경 점검 -> 스캔 -> (검색/그래프 탐색) -> 규칙+AI 분류 -> 사람이 파일별로 검토/수정
-> 최종 상태 미리보기 -> (승인 시) 적용.
AI는 '적용' 버튼을 누르기 전까지 어떤 파일도 이동/수정/삭제하지 않으며, Ollama가 꺼져 있어도
조직 규칙 기반 분류로 핵심 기능을 계속 사용할 수 있다.
적용 후에는 버전 히스토리에 기록되어 언제든 되돌릴 수 있다.
"""

import os
from datetime import datetime

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from app import env_check, llm_client, rename_tool, structure_copy, templates
from app.content_graph import GraphTooLargeError, render_content_graph
from app.directory_graph import render_directory_relation_graph, render_directory_tree
from app.file_ops import apply_move_plan, build_move_plan, undo_move_plan
from app.organizer import (
    classify_entries,
    plain_destinations,
    status_label,
    summarize_entries,
    validate_assignments,
)
from app.report import (
    build_excel_report,
    build_final_state,
    build_report,
    render_current_tree,
    render_proposed_tree,
)
from app.scanner import compute_hashes, find_duplicate_groups, scan_folder
from app.search import search_entries
from app.similar import find_similar_documents
from app.version_history import can_restore, list_versions, mark_restored, record_version
from sample_data.generate_sample_data import OUTPUT_DEFAULT as SAMPLE_DATA_OUTPUT_DEFAULT
from sample_data.generate_sample_data import generate as generate_sample_data

st.set_page_config(page_title="AI 폴더 정리 도우미", layout="wide")

for key, default in (
    ("entries", []),
    ("duplicate_groups", {}),
    ("proposal", None),
    ("scan_root", ""),
    ("similar_docs", []),
    ("template", templates.default_template()),
    ("user_overrides", {}),
    ("edit_history", []),
    ("env_items", None),
):
    if key not in st.session_state:
        st.session_state[key] = default

st.title("📁 AI 폴더 정리 도우미")
st.caption(
    "환경 점검 → 스캔 → 규칙/AI 분류 → 사람이 확인·수정 → 적용. "
    "AI는 절대 자동으로 파일을 옮기지 않으며, 모든 처리는 로컬에서만 이루어집니다."
)


def _reset_analysis_state() -> None:
    st.session_state.proposal = None
    st.session_state.similar_docs = []
    st.session_state.user_overrides = {}
    st.session_state.edit_history = []


def _do_scan(path: str) -> None:
    """폴더를 스캔해 세션 상태를 갱신한다. 적용 완료 직후 자동 재스캔에도 재사용된다."""
    with st.spinner("폴더 스캔 중..."):
        scanned_entries = scan_folder(path)
        compute_hashes(scanned_entries)
        dup_groups = find_duplicate_groups(scanned_entries)
    st.session_state.entries = scanned_entries
    st.session_state.duplicate_groups = dup_groups
    st.session_state.scan_root = path
    _reset_analysis_state()


def _merged_assignments(entries, proposal, root):
    """AI/규칙 제안에 사용자 수정 사항을 반영하고 다시 안전성 검증을 거친다."""
    valid, rejected = validate_assignments(entries, (proposal or {}).get("assignments", {}), root)

    excluded: set = set()
    combined = {}
    for src, info in valid.items():
        ov = st.session_state.user_overrides.get(src)
        if ov and ov.get("excluded"):
            excluded.add(src)
            continue
        if ov and ov.get("dst") and ov["dst"] != info["dst"]:
            combined[src] = {**info, "dst": ov["dst"], "reason": "사용자가 직접 수정", "source": "user"}
        else:
            combined[src] = info

    revalidated, extra_rejected = validate_assignments(entries, combined, root)
    return valid, revalidated, rejected + extra_rejected, excluded


with st.sidebar:
    st.header("설정")
    folder_path = st.text_input(
        "정리할 폴더 경로", value=st.session_state.scan_root, key="folder_path_input"
    )

    with st.expander("🧪 시연용 샘플 데이터"):
        st.caption(
            "이름 규칙이 제각각인 문서 30여 개와 완전 중복 파일 4개를 포함한 어질러진 폴더를 "
            "한 번에 만듭니다. 이미 있는 폴더는 덮어쓰지 않습니다."
        )
        if st.button("샘플 데이터 만들기", use_container_width=True):
            already_existed = os.path.exists(SAMPLE_DATA_OUTPUT_DEFAULT)
            created = generate_sample_data(SAMPLE_DATA_OUTPUT_DEFAULT)
            if already_existed and created == 0:
                st.session_state["_sample_already_exists"] = True
            else:
                st.session_state["_sample_already_exists"] = False
                st.session_state["folder_path_input"] = SAMPLE_DATA_OUTPUT_DEFAULT
                st.success(f"시연용 샘플 폴더를 만들었습니다 ({created}개 파일).")
                st.rerun()
        if st.session_state.get("_sample_already_exists"):
            st.warning("이미 샘플 폴더가 있습니다. 다시 만들려면 아래 버튼을 눌러 덮어쓰세요.")
            if st.button("덮어쓰고 다시 만들기", use_container_width=True):
                created = generate_sample_data(SAMPLE_DATA_OUTPUT_DEFAULT, force=True)
                st.session_state["_sample_already_exists"] = False
                st.session_state["folder_path_input"] = SAMPLE_DATA_OUTPUT_DEFAULT
                st.success(f"시연용 샘플 폴더를 다시 만들었습니다 ({created}개 파일).")
                st.rerun()

    ollama_ok = llm_client.check_connection()
    if ollama_ok:
        st.success("Ollama 연결됨")
        installed_models = llm_client.list_installed_models()
    else:
        st.warning("Ollama에 연결할 수 없습니다. 규칙 기반 분류만으로도 계속 사용할 수 있습니다.")
        installed_models = []

    if installed_models:
        def _format_model_option(name: str) -> str:
            info = next((m for m in installed_models if m["name"] == name), None)
            if not info:
                return name
            size = (
                f"{info['size_mb'] / 1024:.1f}GB"
                if info["size_mb"] >= 1024
                else f"{info['size_mb']}MB"
            )
            extra = f" · {info['parameter_size']}" if info["parameter_size"] else ""
            return f"{name} · {size}{extra}"

        model_names = [m["name"] for m in installed_models]
        # 목록은 크기순(작은 것부터) 정렬되어 있으므로, 기본 모델이 없으면 가장
        # 가벼운 모델(index 0)을 골라 사양을 잘 모르는 사용자도 안전하게 시작하게 한다.
        default_index = (
            model_names.index(llm_client.DEFAULT_MODEL)
            if llm_client.DEFAULT_MODEL in model_names
            else 0
        )
        model_name = st.selectbox(
            "Ollama 모델 (용량이 작을수록 사양 낮은 PC에 유리)",
            options=model_names,
            index=default_index,
            format_func=_format_model_option,
        )
    else:
        model_name = st.text_input(
            "Ollama 모델", value=llm_client.DEFAULT_MODEL, disabled=not ollama_ok
        )

    use_ai = st.checkbox("AI 분류 사용", value=ollama_ok, disabled=not ollama_ok)
    if ollama_ok:
        st.caption(
            "PC 사양이 낮다면 위 체크를 꺼서 AI 없이 규칙 기반으로만 정리하거나, "
            "가장 용량이 작은 모델을 고르세요."
        )

    with st.expander("🩺 실행 환경 점검"):
        if st.button("환경 점검 실행/새로고침", use_container_width=True) or st.session_state.env_items is None:
            st.session_state.env_items = env_check.check_environment(
                root=folder_path, model=model_name
            )
        for item in st.session_state.env_items:
            icon = {"정상": "✅", "주의": "⚠️", "오류": "❌"}.get(item["status"], "•")
            st.write(f"{icon} **{item['item']}** — {item['detail']}")
            if item["action"]:
                st.caption(item["action"])

    with st.expander("🗂️ 조직 표준 템플릿"):
        template = st.session_state.template
        st.caption(f"현재 템플릿: **{template.name}** (버전 {template.version})")
        st.code("\n".join(f["path"] for f in template.folders), language="text")
        uploaded = st.file_uploader("템플릿 JSON 가져오기", type=["json"], key="template_upload")
        if uploaded is not None:
            try:
                st.session_state.template = templates.import_template(
                    uploaded.getvalue().decode("utf-8")
                )
                st.success(f"템플릿 '{st.session_state.template.name}'을(를) 불러왔습니다.")
            except Exception as exc:
                st.error(f"템플릿을 읽을 수 없습니다: {exc}")
        if st.button("기본 템플릿으로 되돌리기", use_container_width=True):
            st.session_state.template = templates.default_template()
        if st.session_state.entries and st.button(
            "현재 폴더 구조로 템플릿 만들기", use_container_width=True
        ):
            st.session_state.template = templates.template_from_current_structure(
                st.session_state.entries, name=f"{os.path.basename(folder_path) or '폴더'} 템플릿"
            )
            st.success("현재 폴더 구조를 템플릿으로 만들었습니다.")

        st.caption("원하는 폴더 구조를 한 줄에 하나씩 직접 입력해서 템플릿으로 만들 수도 있습니다.")
        custom_template_name = st.text_input("새 템플릿 이름", value="내 템플릿", key="custom_template_name")
        custom_folder_text = st.text_area(
            "폴더 목록(한 줄에 하나씩, 예: 영업/실적)",
            placeholder="01_경영지원\n02_인사\n영업/실적",
            key="custom_folder_text",
            height=120,
        )
        if st.button("이 목록으로 템플릿 만들기", use_container_width=True, disabled=not custom_folder_text):
            try:
                st.session_state.template = templates.template_from_folder_list(
                    custom_folder_text, name=custom_template_name or "내 템플릿"
                )
                st.success(f"템플릿 '{st.session_state.template.name}'을(를) 만들었습니다.")
            except ValueError as exc:
                st.error(str(exc))

    with st.expander("📐 폴더 구조만 복사 (내용 없이)"):
        st.caption("스캔된 폴더의 하위 폴더 체계만, 파일 내용 없이 다른 위치에 그대로 만듭니다.")
        copy_dest = st.text_input("생성할 위치(대상 폴더)", key="structure_copy_dest")
        if st.button(
            "구조만 복사하기", use_container_width=True,
            disabled=not (st.session_state.entries and copy_dest),
        ):
            try:
                count, created, skipped = structure_copy.copy_structure_only(
                    st.session_state.entries, copy_dest
                )
                st.success(f"{count}개 폴더를 만들었습니다: {copy_dest}")
                if skipped:
                    st.warning("일부 폴더는 건너뛰었습니다:\n" + "\n".join(f"- {s}" for s in skipped))
            except OSError as exc:
                st.error(f"폴더를 만들 수 없습니다: {exc}")

    scan_clicked = st.button("1️⃣ 스캔", use_container_width=True)
    classify_label = "2️⃣ 분류 실행 (규칙 + AI)" if use_ai else "2️⃣ 분류 실행 (규칙 기반, AI 미사용)"
    classify_clicked = st.button(
        classify_label, use_container_width=True, disabled=not st.session_state.entries
    )

    st.divider()
    st.caption("실제로 파일을 이동한 뒤 되돌리려면 '🕘 버전 관리' 탭을 확인하세요.")


if scan_clicked:
    if not folder_path or not os.path.isdir(folder_path):
        st.error("올바른 폴더 경로를 입력하세요.")
    else:
        _do_scan(folder_path)
        # 스캔 직후 사이드바를 다시 그려야 '분류 실행' 버튼의 비활성화 상태가
        # (방금 채워진 entries를 반영해) 곧바로 갱신된다. st.toast는 rerun 이후에도 표시된다.
        st.toast(f"{len(st.session_state.entries)}개 파일을 찾았습니다.")
        st.rerun()

entries = st.session_state.entries

if not entries:
    st.info("왼쪽에서 폴더 경로를 입력하고 '스캔'을 눌러 시작하세요.")
else:
    (
        tab_scan,
        tab_dup,
        tab_rename,
        tab_dir_graph,
        tab_content_graph,
        tab_ai,
        tab_edit,
        tab_apply,
        tab_versions,
    ) = st.tabs(
        [
            "📋 스캔 결과",
            "🧬 중복 파일",
            "✂️ 이름 일괄 변경",
            "🗂️ 디렉토리 구조/연관도",
            "🕸️ 파일 연관도",
            "🤖 AI 분석",
            "📝 제안 편집",
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

        if not filtered:
            st.info("검색 조건에 맞는 파일이 없습니다. 검색어 또는 필터를 변경해 주세요.")
        else:
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

    with tab_rename:
        st.caption(
            "선택한 파일들의 이름을 규칙에 따라 한 번에 바꿉니다. 실제로는 '같은 폴더로 이름만 "
            "바꿔 이동'하는 것과 같아서, 이동 계획과 똑같은 안전성 검사(경로 보호, 덮어쓰기 금지, "
            "실패 시 자동 복구)와 되돌리기가 그대로 적용됩니다."
        )
        rc1, rc2 = st.columns([1, 1])
        with rc1:
            rename_ext_filter = st.multiselect(
                "대상 확장자(비워두면 전체)", sorted({e.ext or "(없음)" for e in entries}),
                key="rename_ext_filter",
            )
        with rc2:
            rename_query = st.text_input("파일명/경로 검색(비워두면 전체)", key="rename_query")

        rename_targets = entries
        if rename_ext_filter:
            wanted = {e for e in rename_ext_filter if e != "(없음)"}
            include_no_ext = "(없음)" in rename_ext_filter
            rename_targets = [
                e for e in rename_targets if (e.ext in wanted) or (include_no_ext and not e.ext)
            ]
        if rename_query:
            rename_targets = search_entries(rename_targets, query=rename_query)

        st.caption(f"대상 파일 {len(rename_targets)}개")

        mode_labels = {
            rename_tool.MODE_FIND_REPLACE: "찾기/바꾸기",
            rename_tool.MODE_PREFIX: "앞에 문구 추가",
            rename_tool.MODE_SUFFIX: "뒤에 문구 추가",
            rename_tool.MODE_NUMBERING: "일련번호로 통일",
        }
        mode = st.radio(
            "변경 방식", list(mode_labels.keys()), format_func=lambda m: mode_labels[m],
            key="rename_mode", horizontal=True,
        )

        rule = {"mode": mode}
        if mode == rename_tool.MODE_FIND_REPLACE:
            fc1, fc2 = st.columns(2)
            rule["find"] = fc1.text_input("찾을 문자열", key="rename_find")
            rule["replace"] = fc2.text_input("바꿀 문자열", key="rename_replace")
        elif mode in (rename_tool.MODE_PREFIX, rename_tool.MODE_SUFFIX):
            rule["text"] = st.text_input("추가할 문구", key="rename_text")
        elif mode == rename_tool.MODE_NUMBERING:
            nc1, nc2, nc3 = st.columns(3)
            rule["base_name"] = nc1.text_input("기본 이름(비워두면 원래 이름 유지)", key="rename_base")
            rule["start"] = nc2.number_input("시작 번호", min_value=0, value=1, key="rename_start")
            rule["digits"] = nc3.number_input("자릿수", min_value=1, max_value=6, value=3, key="rename_digits")

        if rename_targets:
            preview_rows = rename_tool.preview_rename(rename_targets, rule)
            changed_rows = [r for r in preview_rows if r["changed"]]
            preview_df = pd.DataFrame(
                [{"기존 이름": r["old_name"], "새 이름": r["new_name"]} for r in preview_rows]
            )
            st.dataframe(preview_df, use_container_width=True, hide_index=True)

            if not changed_rows:
                st.info("규칙을 입력하면 미리보기가 표시됩니다.")
            else:
                st.warning(f"{len(changed_rows)}개 파일의 이름이 바뀝니다. 적용 전 위 내용을 확인하세요.")
                rename_confirm = st.checkbox(
                    "위 이름 변경 계획을 확인했으며, 실제로 적용하는 데 동의합니다.", key="rename_confirm"
                )
                if st.button("✂️ 이름 일괄 변경 적용", type="primary", disabled=not rename_confirm):
                    rename_assignments = rename_tool.build_rename_assignments(rename_targets, rule)
                    valid, rejected = validate_assignments(
                        entries, rename_assignments, st.session_state.scan_root
                    )
                    if rejected:
                        st.warning(
                            "일부 항목은 안전성 검사에서 제외되었습니다:\n"
                            + "\n".join(f"- `{r['src']}`: {r['reason']}" for r in rejected)
                        )
                    plan = build_move_plan(st.session_state.scan_root, plain_destinations(valid))
                    log_path, moved_count = apply_move_plan(plan, entries)
                    record_version(
                        st.session_state.scan_root,
                        log_path,
                        note="파일명 일괄 변경",
                        files_moved=moved_count,
                    )
                    st.success(f"{moved_count}개 파일의 이름을 변경했습니다.")
                    st.info("문제가 있다면 '🕘 버전 관리' 탭에서 이 작업을 되돌릴 수 있습니다.")
                    _do_scan(st.session_state.scan_root)
                    st.rerun()

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
        if classify_clicked:
            effective_use_ai = use_ai and ollama_ok
            if effective_use_ai:
                progress = st.progress(0.0, text="분류 준비 중...")

                def on_progress(i: int, total: int, entry) -> None:
                    progress.progress(i / total, text=f"({i}/{total}) {entry.name} 요약 중...")

                summarize_entries(
                    entries, st.session_state.scan_root, model_name, progress_cb=on_progress
                )
                progress.progress(1.0, text="요약 완료. 규칙/AI 분류 생성 중...")
            else:
                progress = None

            try:
                st.session_state.proposal = classify_entries(
                    entries,
                    st.session_state.template,
                    model_name,
                    use_ai=effective_use_ai,
                )
            except llm_client.OllamaError as exc:
                st.error(f"AI 분류 생성 실패: {exc}")
                st.session_state.proposal = classify_entries(
                    entries, st.session_state.template, model_name, use_ai=False
                )

            st.session_state.user_overrides = {}
            st.session_state.edit_history = []
            st.session_state.similar_docs = find_similar_documents(entries)
            if progress:
                progress.empty()
            if effective_use_ai:
                st.success("규칙 + AI 분류가 완료되었습니다. '📝 제안 편집' 탭에서 파일별로 확인·수정하세요.")
            else:
                st.success(
                    "AI 없이 규칙 기반으로만 분류했습니다. 규칙에 걸리지 않은 파일은 "
                    "'📝 제안 편집' 탭에서 직접 목적지를 지정하세요."
                )

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
        if proposal and proposal.get("notes"):
            st.info(proposal["notes"])

    with tab_edit:
        proposal = st.session_state.proposal
        if not proposal:
            st.info("먼저 왼쪽에서 '분류 실행'을 눌러 규칙/AI 제안을 생성하세요.")
        else:
            root = st.session_state.scan_root
            original_valid, _rejected0 = validate_assignments(
                entries, proposal.get("assignments", {}), root
            )

            st.caption(
                "AI/규칙이 제안한 파일별 목적지입니다. 적용 여부를 끄거나 목적지를 직접 고쳐 쓸 수 있습니다."
            )

            source_label = {"rule": "규칙", "ai": "AI", "fallback": "미분류", "user": "사용자"}
            rows = []
            for src, info in original_valid.items():
                ov = st.session_state.user_overrides.get(src, {})
                rows.append(
                    {
                        "적용": not ov.get("excluded", False),
                        "경로": src,
                        "신뢰도": info["confidence"],
                        "추천 이유": info["reason"],
                        "출처": source_label.get(info["source"], info["source"]),
                        "최종 폴더": ov.get("dst", info["dst"]),
                    }
                )
            edit_df = pd.DataFrame(rows)

            f1, f2, f3 = st.columns(3)
            with f1:
                conf_filter = st.multiselect(
                    "신뢰도 필터", ["높음", "보통", "낮음"], key="edit_conf_filter"
                )
            with f2:
                source_filter = st.multiselect(
                    "출처 필터", list(source_label.values()), key="edit_source_filter"
                )
            with f3:
                modified_only = st.checkbox("수정된 항목만 보기", key="edit_modified_only")

            display_df = edit_df
            if conf_filter:
                display_df = display_df[display_df["신뢰도"].isin(conf_filter)]
            if source_filter:
                display_df = display_df[display_df["출처"].isin(source_filter)]
            if modified_only:
                modified_srcs = set(st.session_state.user_overrides.keys())
                display_df = display_df[display_df["경로"].isin(modified_srcs)]

            if display_df.empty:
                st.info("조건에 맞는 파일이 없습니다.")
            else:
                edited = st.data_editor(
                    display_df,
                    use_container_width=True,
                    hide_index=True,
                    disabled=["경로", "신뢰도", "추천 이유", "출처"],
                    key="proposal_editor",
                )
                for _, row in edited.iterrows():
                    src = row["경로"]
                    base = original_valid[src]
                    is_excluded = not row["적용"]
                    new_dst = row["최종 폴더"]
                    changed = is_excluded or new_dst != base["dst"]
                    if changed:
                        prev = st.session_state.user_overrides.get(src)
                        if prev != {"dst": new_dst, "excluded": is_excluded}:
                            st.session_state.user_overrides[src] = {
                                "dst": new_dst,
                                "excluded": is_excluded,
                            }
                            st.session_state.edit_history.append(
                                {
                                    "경로": src,
                                    "AI/규칙 제안": base["dst"],
                                    "사용자 최종": "(제외)" if is_excluded else new_dst,
                                    "수정 시각": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                }
                            )
                    elif src in st.session_state.user_overrides:
                        del st.session_state.user_overrides[src]

                with st.expander("일괄 수정"):
                    bulk_target = st.text_input(
                        "현재 필터에 표시된 모든 항목의 새 목적지 폴더", key="bulk_target"
                    )
                    bcol1, bcol2 = st.columns(2)
                    with bcol1:
                        if st.button("일괄 폴더 변경 적용", disabled=not bulk_target):
                            for src in display_df["경로"]:
                                filename = os.path.basename(src)
                                st.session_state.user_overrides[src] = {
                                    "dst": f"{bulk_target}/{filename}",
                                    "excluded": False,
                                }
                            st.rerun()
                    with bcol2:
                        if st.button("표시된 항목을 AI/규칙 제안으로 되돌리기"):
                            for src in display_df["경로"]:
                                st.session_state.user_overrides.pop(src, None)
                            st.rerun()

            if st.session_state.edit_history:
                with st.expander(f"✏️ 수정 내역 ({len(st.session_state.edit_history)}건)"):
                    st.dataframe(
                        pd.DataFrame(st.session_state.edit_history),
                        use_container_width=True,
                        hide_index=True,
                    )

            _, merged, rejected, excluded = _merged_assignments(entries, proposal, root)
            st.subheader("Before / After 폴더 구조 비교")
            col_before, col_after = st.columns(2)
            with col_before:
                st.markdown("**현재 구조**")
                st.code(render_current_tree(entries), language="text")
            with col_after:
                st.markdown("**적용 시 최종 구조(요약)**")
                st.code(render_proposed_tree(merged), language="text")

            st.subheader("최종 상태 미리보기 (실제로 적용됐을 때)")
            final_state = build_final_state(entries, merged, excluded, rejected)
            status_counts = pd.Series([r["상태"] for r in final_state]).value_counts()
            st.write(
                " · ".join(f"{status}: {count}개" for status, count in status_counts.items())
            )
            st.dataframe(pd.DataFrame(final_state), use_container_width=True, hide_index=True)

            report_json = build_report(
                entries,
                st.session_state.duplicate_groups,
                proposal,
                st.session_state.similar_docs,
                final_state=final_state,
                env_items=st.session_state.env_items,
            )
            st.download_button(
                "📥 리포트 다운로드 (JSON)",
                data=report_json,
                file_name=f"folder_organize_report_{datetime.now():%Y%m%d_%H%M%S}.json",
                mime="application/json",
            )
            excel_bytes = build_excel_report(entries, st.session_state.duplicate_groups, final_state)
            st.download_button(
                "📊 리포트 다운로드 (엑셀)",
                data=excel_bytes,
                file_name=f"folder_organize_report_{datetime.now():%Y%m%d_%H%M%S}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

    with tab_apply:
        proposal = st.session_state.proposal
        root = st.session_state.scan_root
        if not proposal:
            st.info("먼저 왼쪽에서 '분류 실행'을 눌러 제안 구조를 생성하세요.")
        else:
            _, merged, rejected, excluded = _merged_assignments(entries, proposal, root)
            final_state = build_final_state(entries, merged, excluded, rejected)
            status_counts = pd.Series([r["상태"] for r in final_state]).value_counts()

            st.subheader("적용 결과 요약(예상)")
            st.write(
                " · ".join(f"**{status}**: {count}개" for status, count in status_counts.items())
            )

            if rejected:
                st.warning(
                    f"안전성 검사에서 제외된 항목 {len(rejected)}건:\n\n"
                    + "\n".join(f"- `{r['src']}` → `{r['dst']}`: {r['reason']}" for r in rejected)
                )

            if not merged:
                st.info("적용할 이동 항목이 없습니다. '📝 제안 편집' 탭에서 목적지를 지정하세요.")
            else:
                plan = build_move_plan(root, plain_destinations(merged))
                st.warning(f"{len(plan)}개 파일이 이동됩니다. 적용 전 아래 내용을 반드시 확인하세요.")
                plan_df = pd.DataFrame(
                    [{"기존 경로": p["rel_src"], "새 경로": p["rel_dst"]} for p in plan]
                )
                st.dataframe(plan_df, use_container_width=True, hide_index=True)

                st.info(
                    f"{len(plan)}개 파일을 위에 표시된 최종 경로로 이동합니다. "
                    "기존 파일은 덮어쓰지 않으며, 오류가 발생하면 이미 이동한 파일을 자동으로 복구합니다. "
                    "적용 후 '🕘 버전 관리' 탭에서 이 작업을 되돌릴 수 있습니다."
                )
                confirm = st.checkbox("위 이동 계획을 확인했으며, 실제로 파일을 이동하는 데 동의합니다.")
                if st.button("🚀 적용 (실제 파일 이동)", type="primary", disabled=not confirm):
                    log_path, moved_count = apply_move_plan(plan, entries)
                    record_version(
                        root,
                        log_path,
                        note=(proposal or {}).get("notes", ""),
                        files_moved=moved_count,
                    )
                    if moved_count == len(plan):
                        st.success(f"{moved_count}개 파일 이동을 완료했습니다.")
                    elif moved_count == 0:
                        st.error("이동 중 오류가 발생해 모든 변경 사항을 자동으로 복구했습니다. 원본 상태가 유지됩니다.")
                    else:
                        st.warning(
                            f"{moved_count}개 파일만 이동되었습니다 "
                            f"(계획 {len(plan)}건 중 일부는 변경 감지 등으로 건너뛰었습니다)."
                        )
                    st.info("문제가 있다면 '🕘 버전 관리' 탭에서 이 작업을 되돌릴 수 있습니다.")
                    _do_scan(root)
                    st.rerun()

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
                        allowed, reason = can_restore(st.session_state.scan_root, v["version_id"])
                        if st.button(
                            "이 버전 되돌리기",
                            key=f"restore_{v['version_id']}",
                            disabled=not allowed,
                        ):
                            restored = undo_move_plan(v["log_path"])
                            mark_restored(st.session_state.scan_root, v["version_id"])
                            st.success(f"{restored}개 파일을 원래 위치로 되돌렸습니다.")
                            st.rerun()
                        if not allowed:
                            st.caption(reason)
                    else:
                        st.caption("이미 되돌려진 버전입니다.")
