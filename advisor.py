import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.database import get_summary_stats
from ai.groq_advisor import chat_with_advisor, generate_financial_report
from components.styles import section_header


STARTER_QUESTIONS = [
    "Where am I spending the most money?",
    "How can I reduce my expenses this month?",
    "Give me a tax summary for filing",
    "Which vendors am I overpaying?",
    "What's my budget status across all categories?",
    "Generate a full financial report",
]


def show_advisor():
    section_header("AI Financial Advisor", "🤖")
    st.markdown("""
<div style='color:#94A3B8; font-size:14px; margin-bottom:1.5rem;'>
    Powered by Groq LLaMA-3 70B — your personal finance AI that knows your actual spending data.
</div>
""", unsafe_allow_html=True)

    stats = get_summary_stats()

    # ── Init session state ────────────────────────────────────────────────────
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # ── Quick starter prompts ─────────────────────────────────────────────────
    if not st.session_state.chat_history:
        st.markdown("#### 💡 Quick Questions")
        cols = st.columns(3)
        for i, q in enumerate(STARTER_QUESTIONS):
            with cols[i % 3]:
                if st.button(q, key=f"starter_{i}", use_container_width=True):
                    st.session_state.chat_history.append({"role":"user","content":q})
                    with st.spinner("Thinking..."):
                        reply = chat_with_advisor(q, st.session_state.chat_history[:-1], stats)
                    st.session_state.chat_history.append({"role":"assistant","content":reply})
                    st.rerun()

    # ── Chat messages ─────────────────────────────────────────────────────────
    chat_container = st.container()
    with chat_container:
        for msg in st.session_state.chat_history:
            role = msg["role"]
            content = msg["content"]
            if role == "user":
                st.markdown(f'<div class="chat-bubble chat-user">👤 {content}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="chat-bubble chat-ai">🤖 {content}</div>', unsafe_allow_html=True)

    # ── Input ─────────────────────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    col_inp, col_btn = st.columns([5,1])
    with col_inp:
        user_input = st.text_input(
            "Ask anything about your finances...",
            label_visibility="collapsed",
            placeholder="e.g. How much did I spend on food this month?",
            key="chat_input",
        )
    with col_btn:
        send = st.button("Send ↗", use_container_width=True, key="send_chat")

    if send and user_input.strip():
        user_msg = user_input.strip()
        st.session_state.chat_history.append({"role":"user","content":user_msg})
        with st.spinner("🤖 Analyzing your data..."):
            reply = chat_with_advisor(user_msg, st.session_state.chat_history[:-1], stats)
        st.session_state.chat_history.append({"role":"assistant","content":reply})
        st.rerun()

    # ── Clear + Report buttons ────────────────────────────────────────────────
    col_c, col_r = st.columns(2)
    with col_c:
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.chat_history = []
            st.rerun()
    with col_r:
        if st.button("📊 Generate Full Report", use_container_width=True):
            with st.spinner("Generating AI financial report..."):
                report = generate_financial_report(stats, [])
            st.markdown("---")
            section_header("Financial Report", "📋")
            st.markdown(report)
