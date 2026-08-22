import os
from datetime import datetime
import streamlit as st

from agents import plan_sub_questions, research_sub_question, synthesize_report, critique_report
from config import GEMINI_API_KEY, GROQ_API_KEY, OPENROUTER_API_KEY, SAVE_REPORTS_TO, GROQ_MODEL, GEMINI_MODEL, CRITIC_MODEL


st.set_page_config(
    page_title="AI Research System",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)


class AIResearchApp:

    def __init__(self):
        self.setup_session_state()
        self.inject_css()

    def setup_session_state(self):
        if "chats" not in st.session_state:
            st.session_state.chats = {}
        if "current_chat" not in st.session_state:
            self.create_new_chat()

    def create_new_chat(self):
        chat_id = f"chat_{len(st.session_state.chats) + 1}"
        st.session_state.chats[chat_id] = {
            "title": "New Research",
            "query": "",
            "result": "",
            "sources": [],
            "review": ""
        }
        st.session_state.current_chat = chat_id

    def inject_css(self):
        st.markdown(
            """
            <style>
            .stApp { background-color: #193459; color: #FAF8F2; }
            .block-container { padding-top: 2rem; padding-bottom: 4rem; }
            section[data-testid="stSidebar"] { background-color: #161B22; border-right: 1px solid #30363D; }
            .sidebar-title { font-size: 1.25rem; font-weight: 700; color: #F3F4F6; margin-bottom: 2px; }
            .sidebar-subtitle { font-size: 0.75rem; color: #9CA3AF; }
            .new-chat-button { margin-top: 12px; margin-bottom: 10px; }
            .history-title {
                color: #9CA3AF; font-size: 0.72rem; font-weight: 600;
                text-transform: uppercase; letter-spacing: 0.08em;
                margin-top: 14px; margin-bottom: 8px;
            }
            .history-item {
                background-color: #1F2937; border: 1px solid #30363D; border-radius: 7px;
                padding: 7px 9px; margin-bottom: 5px; color: #D1D5DB; font-size: 0.78rem;
                overflow: hidden; white-space: nowrap; text-overflow: ellipsis;
            }
            .sidebar-bottom { position: fixed; bottom: 15px; width: 260px; padding-right: 18px; }
            .compact-section {
                background-color: #1A2029; border: 1px solid #30363D; border-radius: 7px;
                padding: 7px 9px; margin-top: 5px;
            }
            .compact-title { font-size: 0.72rem; font-weight: 600; color: #D1D5DB; margin-bottom: 5px; }
            .api-row {
                display: flex; justify-content: space-between; align-items: center;
                font-size: 0.68rem; color: #9CA3AF; margin: 3px 0;
            }
            .status-dot { width: 6px; height: 6px; background-color: #10B981; border-radius: 50%; display: inline-block; }
            .status-dot.missing { background-color: #EF4444; }
            .model-row {
                display: flex; justify-content: space-between; align-items: center;
                font-size: 0.65rem; color: #9CA3AF; margin: 3px 0;
            }
            .model-name { color: #D1D5DB; font-size: 0.64rem; }
            .main-title {
                text-align: center; color: #FAF8F2; font-size: 2.2rem; font-weight: 700;
                margin-top: 5vh; margin-bottom: 8px; letter-spacing: -0.03em;
            }
            .main-subtitle { text-align: center; color: #AAB4C3; font-size: 0.9rem; margin-bottom: 35px; }
            .search-wrapper {
                position: relative; max-width: 720px; margin: auto; padding: 2px; border-radius: 22px;
                background: linear-gradient(90deg, #4285F4, #9B72CB, #D96570, #4285F4);
                background-size: 300% 300%; animation: gradientMove 5s ease infinite;
            }
            .search-wrapper::before {
                content: ""; position: absolute; inset: -3px; border-radius: 25px;
                background: linear-gradient(90deg, #4285F4, #9B72CB, #D96570, #4285F4);
                background-size: 300% 300%; filter: blur(10px); opacity: 0.35;
                z-index: -1; animation: gradientMove 5s ease infinite;
            }
            @keyframes gradientMove {
                0% { background-position: 0% 50%; }
                50% { background-position: 100% 50%; }
                100% { background-position: 0% 50%; }
            }
            .stTextArea textarea {
                background-color: #111827 !important; color: #F3F4F6 !important; border: none !important;
                border-radius: 20px !important; min-height: 95px !important; padding: 15px 18px !important;
                font-size: 0.9rem !important; box-shadow: none !important;
            }
            .stTextArea textarea:focus { border: none !important; box-shadow: none !important; }
            .run-button-container { display: flex; justify-content: center; margin-top: 15px; margin-bottom: 35px; }
            .stButton > button {
                background: linear-gradient(135deg, #2563EB, #1D4ED8); color: white; border: none;
                border-radius: 18px; padding: 0.5rem 2.2rem; font-size: 0.85rem; font-weight: 600;
                transition: all 0.2s ease;
            }
            .stButton > button:hover { transform: translateY(-1px); box-shadow: 0px 5px 15px rgba(37, 99, 235, 0.35); }
            .result-card { background-color: #161B22; border: 1px solid #30363D; border-radius: 10px; padding: 18px; margin-top: 15px; }
            .copyright {
                position: fixed; bottom: 8px; left: 50%; transform: translateX(-50%);
                color: #7F8A9A; font-size: 0.65rem; text-align: center; z-index: 999;
            }
            </style>
            """,
            unsafe_allow_html=True
        )

    def render_sidebar(self):
        with st.sidebar:
            st.markdown('<div class="sidebar-title">🔬 AI Research</div>', unsafe_allow_html=True)
            st.markdown('<div class="sidebar-subtitle">Multi-Agent Research System</div>', unsafe_allow_html=True)

            st.markdown('<div class="new-chat-button">', unsafe_allow_html=True)
            if st.button("＋ New Chat", use_container_width=True):
                self.create_new_chat()
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

            st.markdown('<div class="history-title">Chat History</div>', unsafe_allow_html=True)

            for chat_id, chat in st.session_state.chats.items():
                title = chat["title"]
                if st.button(f"💬 {title}", key=f"history_{chat_id}", use_container_width=True):
                    st.session_state.current_chat = chat_id
                    st.rerun()

            st.markdown('<div class="sidebar-bottom">', unsafe_allow_html=True)

            gemini_dot = "" if GEMINI_API_KEY else " missing"
            groq_dot = "" if GROQ_API_KEY else " missing"
            openrouter_dot = "" if OPENROUTER_API_KEY else " missing"

            st.markdown(
                f"""
                <div class="compact-section">
                <div class="compact-title">API Status</div>
                <div class="api-row"><span>Gemini API</span><span class="status-dot{gemini_dot}"></span></div>
                <div class="api-row"><span>Groq API</span><span class="status-dot{groq_dot}"></span></div>
                <div class="api-row"><span>OpenRouter API</span><span class="status-dot{openrouter_dot}"></span></div>
                </div>
                """,
                unsafe_allow_html=True
            )

            critic_short = CRITIC_MODEL.split("/")[-1] if "/" in CRITIC_MODEL else CRITIC_MODEL
            st.markdown(
                f"""
                <div class="compact-section">
                <div class="compact-title">Model Config</div>
                <div class="model-row"><span>Planner</span><span class="model-name">{GROQ_MODEL}</span></div>
                <div class="model-row"><span>Synthesizer</span><span class="model-name">{GEMINI_MODEL}</span></div>
                <div class="model-row"><span>Critic</span><span class="model-name">{critic_short}</span></div>
                </div>
                """,
                unsafe_allow_html=True
            )

            st.markdown('</div>', unsafe_allow_html=True)

    def render_main_page(self):
        st.markdown('<div class="main-title">AI Research System</div>', unsafe_allow_html=True)
        st.markdown('<div class="main-subtitle">Autonomous multi-agent research and synthesis</div>', unsafe_allow_html=True)

        st.markdown('<div class="search-wrapper">', unsafe_allow_html=True)
        query = st.text_area(
            "Research Topic / Prompt",
            placeholder="Ask anything you want to research...",
            height=95,
            label_visibility="collapsed"
        )
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="run-button-container">', unsafe_allow_html=True)
        run_clicked = st.button("Run", key="run_research")
        st.markdown('</div>', unsafe_allow_html=True)

        if run_clicked:
            self.execute_research(query)

        st.markdown(
            """
            <div class="copyright">
                © 2026 AI Research System · All Rights Reserved
            </div>
            """,
            unsafe_allow_html=True
        )

    def execute_research(self, query):
        if not query.strip():
            st.warning("Please enter a valid research question.")
            return

        missing_keys = []
        if not GEMINI_API_KEY:
            missing_keys.append("GEMINI_API_KEY")
        if not GROQ_API_KEY:
            missing_keys.append("GROQ_API_KEY")
        if not OPENROUTER_API_KEY:
            missing_keys.append("OPENROUTER_API_KEY")

        if missing_keys:
            st.error(f"Missing keys: {', '.join(missing_keys)}")
            return

        chat_id = st.session_state.current_chat
        current_chat = st.session_state.chats[chat_id]

        current_chat["query"] = query
        current_chat["title"] = query[:28] + "..." if len(query) > 28 else query

        with st.status("Running research...", expanded=True) as status:

            st.write("📋 **Planner:** Breaking prompt into target sub-queries...")
            sub_questions = plan_sub_questions(query)
            st.write(f"   → {sub_questions}")

            st.write("🔍 **Researcher:** Gathering web sources...")
            research_data = []
            for i, q in enumerate(sub_questions, 1):
                st.write(f"   ({i}/{len(sub_questions)}) {q}")
                research_data.append(research_sub_question(q))

            st.write("✍️ **Synthesizer:** Generating research synthesis...")
            report = synthesize_report(query, research_data)

            st.write("⚖️ **Critic:** Validating content and citations...")
            review = critique_report(query, report)

            status.update(label="Research Complete!", state="complete", expanded=False)

        current_chat["result"] = report

        all_sources = []
        for item in research_data:
            for src in item["sources"]:
                all_sources.append({"title": src["title"], "url": src["url"]})
        current_chat["sources"] = all_sources

        current_chat["review"] = review

        os.makedirs(SAVE_REPORTS_TO, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{SAVE_REPORTS_TO}/report_{timestamp}.md"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"# Research Report\n\n**Question:** {query}\n\n---\n\n{report}\n\n---\n\n## Critique\n\n{review}\n")

        st.rerun()

    def render_chat_result(self):
        chat = st.session_state.chats[st.session_state.current_chat]

        if not chat["result"]:
            return

        st.divider()

        tab_report, tab_sources, tab_review = st.tabs(["📄 Final Report", "🔗 Sources", "🔬 Critic"])

        with tab_report:
            st.markdown('<div class="result-card">', unsafe_allow_html=True)
            st.markdown(chat["result"])
            st.markdown('</div>', unsafe_allow_html=True)

            st.download_button(
                "⬇️ Download report (.md)",
                chat["result"],
                file_name="research_report.md",
                key=f"download_{st.session_state.current_chat}"
            )

        with tab_sources:
            st.markdown("### Retrieved Sources")
            if chat["sources"]:
                for src in chat["sources"]:
                    st.markdown(f"- [{src['title']}]({src['url']})")
            else:
                st.info("No sources retrieved.")

        with tab_review:
            st.markdown("### Agent Evaluation")
            st.markdown(chat["review"])

    def run(self):
        self.render_sidebar()
        self.render_main_page()
        self.render_chat_result()


app = AIResearchApp()
app.run()
