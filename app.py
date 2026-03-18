"""Streamlit GUI 界面 - 论文参考文献智能生成工具"""
import sys
import os
import tempfile
from pathlib import Path

os.environ["PYTHONIOENCODING"] = "utf-8"

sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st
from main import process_paper
from modules.formatter import format_single_reference_markdown


st.set_page_config(page_title="论文参考文献智能生成", page_icon="📚", layout="wide")

st.title("📚 论文参考文献智能生成工具")
st.markdown(r"上传含角标（如 \[1\], \[2,3\], \[4-6\]）的 Word 文档，自动匹配真实学术论文并生成 GB/T 7714 格式参考文献列表。")

col_left, col_right = st.columns([1, 2])

with col_left:
    st.subheader("输入设置")


    upload_tab, text_tab = st.tabs(["上传文档", "粘贴文本"])

    with upload_tab:
        uploaded_file = st.file_uploader("上传 Word 文档 (.docx)", type=["docx"])

    with text_tab:
        text_input = st.text_area(
            "粘贴包含角标的论文段落",
            placeholder="近年来，基于Transformer架构的大语言模型取得了显著突破[1]。...",
            height=200,
        )

    st.divider()

    c1, c2 = st.columns(2)
    with c1:
        year_start = st.number_input("起始年份", value=2021, min_value=2000, max_value=2026)
    with c2:
        year_end = st.number_input("结束年份", value=2026, min_value=2000, max_value=2030)

    cn_ratio_pct = st.slider(
        "中文文献占比 (%)",
        min_value=0, max_value=100, value=25, step=5,
        help="25% = 中英文 1:3 比例",
    )

    results_per = st.slider(
        "每源检索数",
        min_value=1, max_value=10, value=5,
        help="增加可提高匹配质量，但会变慢",
    )

    run_btn = st.button("🚀 生成参考文献", type="primary", use_container_width=True)

with col_right:
    if run_btn:
        docx_path = None

        if uploaded_file is not None:
            tmp = tempfile.NamedTemporaryFile(suffix=".docx", delete=False)
            tmp.write(uploaded_file.getvalue())
            tmp.close()
            docx_path = tmp.name
        elif text_input and text_input.strip():
            from docx import Document
            doc = Document()
            for para in text_input.strip().split("\n"):
                if para.strip():
                    doc.add_paragraph(para.strip())
            tmp = tempfile.NamedTemporaryFile(suffix=".docx", delete=False)
            doc.save(tmp.name)
            tmp.close()
            docx_path = tmp.name
        else:
            st.error("请上传 Word 文档或粘贴论文文本")
            st.stop()

        progress_bar = st.progress(0, text="正在解析文档...")
        log_container = st.expander("运行日志", expanded=False)
        log_lines = []

        def log_callback(msg):
            log_lines.append(msg)
            with log_container:
                st.text(msg)

        cn_ratio = cn_ratio_pct / 100.0

        with st.spinner("正在处理中，请耐心等待..."):
            try:
                refs, md_output, plain_output = process_paper(
                    docx_path=docx_path,
                    year_start=int(year_start),
                    year_end=int(year_end),
                    results_per_source=int(results_per),
                    cn_ratio=cn_ratio,
                    callback=log_callback,
                )
            except Exception as e:
                st.error(f"处理出错: {e}")
                st.stop()

        progress_bar.progress(100, text="完成！")

        if not refs:
            st.warning("未找到任何角标或匹配结果")
        else:
            cn_count = sum(1 for p in refs.values()
                          if sum(1 for c in (p.title or "") if '\u4e00' <= c <= '\u9fff') / max(len(p.title or "x"), 1) > 0.3)
            en_count = len(refs) - cn_count

            st.success(f"✅ {len(refs)} 条参考文献已生成（中文 {cn_count} + 英文 {en_count}）")

            st.subheader("参考文献列表")
            st.markdown(md_output)

            st.subheader("详细匹配结果")
            for idx in sorted(refs.keys()):
                p = refs[idx]
                with st.container(border=True):
                    doi_link = f"[{p.doi}](https://doi.org/{p.doi})" if p.doi else "无"
                    st.markdown(f"**[{idx}]** {p.title}")
                    st.markdown(f"📖 {p.journal or 'N/A'} · {p.year or 'N/A'} · DOI: {doi_link} · 被引: {p.citation_count or 'N/A'} · 来源: {p.source}")

            st.divider()
            st.download_button(
                "📥 下载参考文献 (Markdown)",
                data=md_output,
                file_name="references.md",
                mime="text/markdown",
                use_container_width=True,
            )
            st.download_button(
                "📥 下载参考文献 (纯文本)",
                data=plain_output,
                file_name="references.txt",
                mime="text/plain",
                use_container_width=True,
            )
    else:
        st.info("👈 请在左侧上传文档或粘贴文本，然后点击「生成参考文献」")
