

import os
import sys
from datetime import datetime
from pathlib import Path

import streamlit as st

# UTF-8 safety for Windows terminals
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Page config (must be first Streamlit call)
st.set_page_config(
    page_title="HYBRID AI System",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Project imports after page config
from agents import (
    plan_sub_questions,
    research_sub_question,
    synthesize_report,
    critique_report,
)
from config import (
    SAVE_REPORTS_TO,
    GEMINI_API_KEY, GROQ_API_KEY, OPENROUTER_API_KEY,
    GEMINI_MODEL, GROQ_MODEL, CRITIC_MODEL,
    MAX_SUB_QUESTIONS, RESULTS_PER_QUERY,
)

# ── SIDEBAR ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("🔬 AI Research")
    st.caption("Multi-agent research pipeline")
    st.divider()

    # API key status
    st.subheader("🔑 API Keys")
    for label, key in [
        ("Gemini", GEMINI_API_KEY),
        ("Groq", GROQ_API_KEY),
        ("OpenRouter", OPENROUTER_API_KEY),
    ]:
        if key:
            st.success(f"{label} ✓", icon="✅")
        else:
            st.error(f"{label} missing", icon="❌")

    st.divider()

    # Model info
    st.subheader("🤖 Models")
    critic_short = CRITIC_MODEL.split("/")[-1] if "/" in CRITIC_MODEL else CRITIC_MODEL
    st.markdown(f"""
| Agent | Model |
|---|---|
| Planner | `{GROQ_MODEL}` |
| Synthesizer | `{GEMINI_MODEL}` |
| Critic | `{critic_short}` |
""")
    st.divider()

    # Settings
    st.subheader("⚙️ Settings")
    st.markdown(f"- Max sub-questions: **{MAX_SUB_QUESTIONS}**")
    st.markdown(f"- Results per query: **{RESULTS_PER_QUERY}**")
    st.divider()

    # Past reports browser
    st.subheader("📂 Past Reports")
    reports_dir = Path(SAVE_REPORTS_TO)
    if reports_dir.exists():
        report_files = sorted(reports_dir.glob("report_*.md"), reverse=True)
        if report_files:
            selected = st.selectbox(
                "Load a past report",
                options=report_files,
                format_func=lambda p: p.stem.replace("report_", ""),
                index=None,
                placeholder="Choose a report…",
            )
            if selected:
                st.session_state["loaded_report"] = selected.read_text(encoding="utf-8")
                st.session_state["loaded_report_name"] = selected.name
        else:
            st.caption("No saved reports yet.")
    else:
        st.caption("No saved reports yet.")

# ── MAIN HEADER ───────────────────────────────────────────────────────────────
st.title("🔬 AI Research System")
st.caption(
    "Ask a research question → **Planner** (Groq) breaks it into sub-queries → "
    "**Researcher** (DuckDuckGo) gathers sources → **Synthesizer** (Gemini) writes "
    "the report → **Critic** (OpenRouter) reviews it."
)

# API key guard
missing = [name for name, key in [
    ("GEMINI_API_KEY", GEMINI_API_KEY),
    ("GROQ_API_KEY", GROQ_API_KEY),
    ("OPENROUTER_API_KEY", OPENROUTER_API_KEY),
] if not key]
if missing:
    st.error(
        f"⛔ Missing API keys: **{', '.join(missing)}**\n\n"
        "Add them to your `.env` file and restart the app."
    )
    st.stop()

# ── LOADED PAST REPORT ────────────────────────────────────────────────────────
if "loaded_report" in st.session_state:
    st.info(f"📄 Showing saved report: `{st.session_state['loaded_report_name']}`")
    st.markdown(st.session_state["loaded_report"])
    if st.button("✖ Clear and start new research"):
        del st.session_state["loaded_report"]
        del st.session_state["loaded_report_name"]
        st.rerun()
    st.stop()

# ── INPUT FORM ────────────────────────────────────────────────────────────────
with st.form("research_form"):
    query = st.text_input(
        "Research question",
        placeholder="e.g. What are the risks of AI-generated misinformation in elections?",
    )
    submitted = st.form_submit_button("🚀 Run Research", type="primary", use_container_width=True)

if submitted and not query.strip():
    st.warning("⚠️ Please enter a research question.")
    st.stop()

# ── PIPELINE ──────────────────────────────────────────────────────────────────
if submitted and query.strip():

    # Stage 1 — Planner
    with st.status("🧠 Stage 1 / 4 — Planner (Groq)", expanded=True) as s:
        st.write("Breaking your question into focused sub-queries…")
        sub_questions = plan_sub_questions(query)
        st.write(f"Generated **{len(sub_questions)}** sub-question(s):")
        for i, q in enumerate(sub_questions, 1):
            st.markdown(f"&nbsp;&nbsp;`{i}.` {q}")
        s.update(label="✅ Planner done", state="complete", expanded=False)

    # Stage 2 — Researcher
    research_data = []
    with st.status("🔎 Stage 2 / 4 — Researcher (DuckDuckGo)", expanded=True) as s:
        for i, q in enumerate(sub_questions, 1):
            st.write(f"({i}/{len(sub_questions)}) Searching: *{q}*")
            result = research_sub_question(q)
            research_data.append(result)
            st.caption(f"  → {len(result['sources'])} source(s) gathered")
        s.update(label="✅ Research done", state="complete", expanded=False)

    # Stage 3 — Synthesizer
    with st.status("✍️ Stage 3 / 4 — Synthesizer (Gemini)", expanded=True) as s:
        st.write("Writing report from all gathered evidence…")
        report = synthesize_report(query, research_data)
        s.update(label="✅ Report written", state="complete", expanded=False)

    # Stage 4 — Critic
    with st.status("🔬 Stage 4 / 4 — Critic (OpenRouter)", expanded=True) as s:
        st.write("Reviewing for gaps, contradictions, and unsupported claims…")
        critique = critique_report(query, report)
        s.update(label="✅ Critique complete", state="complete", expanded=False)

    st.success("🎉 Research pipeline complete!")
    st.divider()

    # ── Results ───────────────────────────────────────────────────────────────
    col_report, col_right = st.columns([7, 3], gap="large")

    with col_report:
        st.subheader("📄 Report")
        st.markdown(report)

    with col_right:
        st.subheader("🔬 Critique")
        with st.container(border=True):
            st.markdown(critique)

        st.subheader("📚 Sources")
        for item in research_data:
            with st.expander(item["question"], expanded=False):
                for src in item["sources"]:
                    title = src["title"] or src["url"]
                    snippet = (src.get("snippet") or "")[:160]
                    st.markdown(f"**[{title}]({src['url']})**")
                    if snippet:
                        st.caption(snippet + "…")

    # ── Save & download ────────────────────────────────────────────────────────
    st.divider()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs(SAVE_REPORTS_TO, exist_ok=True)
    filename = f"{SAVE_REPORTS_TO}/report_{timestamp}.md"

    sq_list = "\n".join(f"- {q}" for q in sub_questions)
    sources_md = ""
    for item in research_data:
        sources_md += f"### {item['question']}\n"
        for src in item["sources"]:
            sources_md += f"- [{src['title']}]({src['url']})\n"
        sources_md += "\n"

    full_md = (
        f"# Research Report\n\n**Question:** {query}\n\n"
        f"**Sub-questions explored:**\n{sq_list}\n\n---\n\n"
        f"{report}\n\n---\n\n## Critique / Review\n\n{critique}\n\n"
        f"---\n\n## Sources\n\n{sources_md}"
    )
    with open(filename, "w", encoding="utf-8") as f:
        f.write(full_md)

    col_info, col_dl = st.columns(2)
    with col_info:
        st.info(f"💾 Saved to `{filename}`")
    with col_dl:
        st.download_button(
            label="⬇️ Download report (.md)",
            data=full_md,
            file_name=f"report_{timestamp}.md",
            mime="text/markdown",
            use_container_width=True,
        )
