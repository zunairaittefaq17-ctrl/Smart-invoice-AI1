import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.database import save_budget, get_budgets
from components.styles import section_header

CATEGORIES = ["Food","Transport","Utilities","Medical","Shopping","Telecom","Education","Travel","Other"]

def show_settings():
    section_header("Settings", "⚙️")

    tab_budget, tab_api, tab_about = st.tabs(["🎯  Budgets", "🔑  API Setup", "ℹ️  About"])

    # ─────────────────────────────────────────────────────────────────────────
    # TAB 1 — BUDGET SETTINGS
    # ─────────────────────────────────────────────────────────────────────────
    with tab_budget:
        st.markdown("""
<div style='color:#94A3B8; font-size:14px; margin-bottom:1.5rem;'>
    Set monthly spending limits per category. Dashboard will show progress bars and alerts.
</div>
""", unsafe_allow_html=True)

        existing = {b["category"]: b["monthly_limit"] for b in get_budgets()}

        with st.form("budget_form"):
            st.markdown("#### Set Monthly Budgets (PKR)")
            cols = st.columns(3)
            budgets_input = {}
            for i, cat in enumerate(CATEGORIES):
                with cols[i % 3]:
                    val = existing.get(cat, 0.0)
                    budgets_input[cat] = st.number_input(
                        cat, min_value=0.0, value=float(val), step=500.0, key=f"budget_{cat}"
                    )

            submitted = st.form_submit_button("💾 Save All Budgets", use_container_width=True)
            if submitted:
                for cat, limit in budgets_input.items():
                    if limit > 0:
                        save_budget(cat, limit)
                st.success("✅ Budgets saved! Check Dashboard to see progress.")

    # ─────────────────────────────────────────────────────────────────────────
    # TAB 2 — API SETUP
    # ─────────────────────────────────────────────────────────────────────────
    with tab_api:
        st.markdown("""
<div class="si-card" style="margin-bottom:1.5rem;">
    <div style="font-size:15px; font-weight:600; color:#00D4AA; margin-bottom:10px;">🔑 Groq API Key Setup</div>
    <div style="color:#94A3B8; font-size:14px; line-height:1.8;">
        SmartInvoice AI uses <strong style="color:#F1F5F9;">Groq LLaMA-3 70B</strong> for intelligent invoice parsing and financial advice.<br><br>
        
        <strong style="color:#F1F5F9;">Step 1:</strong> Go to <a href="https://console.groq.com" target="_blank" style="color:#00D4AA;">console.groq.com</a> → Sign up free → Create API key<br><br>
        
        <strong style="color:#F1F5F9;">Step 2 (for Streamlit Cloud deployment):</strong><br>
        • Go to your app on <a href="https://share.streamlit.io" target="_blank" style="color:#00D4AA;">share.streamlit.io</a><br>
        • Click <strong>⋮ → Settings → Secrets</strong><br>
        • Add this exactly:<br>
    </div>
    <div style="background:#0A0E1A; border:1px solid rgba(0,212,170,0.3); border-radius:8px; padding:12px; margin-top:10px; font-family:monospace; color:#00FFD1; font-size:13px;">
        GROQ_API_KEY = "gsk_your_actual_key_here"
    </div>
    <div style="color:#94A3B8; font-size:13px; margin-top:12px;">
        <strong style="color:#F1F5F9;">Step 3 (for local testing):</strong><br>
        Edit the file <code style="color:#00D4AA;">.streamlit/secrets.toml</code> and add your key there.<br>
        The app works without a key (OCR still works), but AI enhancement and chatbot need it.
    </div>
</div>
""", unsafe_allow_html=True)

        # Test key
        api_key_test = st.text_input("Test your Groq key here:", type="password",
                                     placeholder="gsk_...")
        if st.button("🧪 Test Connection", key="test_key") and api_key_test:
            try:
                from groq import Groq
                client = Groq(api_key=api_key_test)
                r = client.chat.completions.create(
                    model="llama3-70b-8192",
                    messages=[{"role":"user","content":"Reply with just: OK"}],
                    max_tokens=5
                )
                st.success(f"✅ Connected! Model responded: {r.choices[0].message.content}")
            except Exception as e:
                st.error(f"❌ Connection failed: {e}")

    # ─────────────────────────────────────────────────────────────────────────
    # TAB 3 — ABOUT
    # ─────────────────────────────────────────────────────────────────────────
    with tab_about:
        st.markdown("""
<div class="si-card">
    <div style="font-size:22px; font-family:Syne,sans-serif; font-weight:700; color:#00D4AA; margin-bottom:8px;">
        SmartInvoice AI
    </div>
    <div style="color:#94A3B8; font-size:13px; margin-bottom:1.5rem;">
        Final Year Project — AI-Powered Financial Automation Platform
    </div>
    
    <div style="display:grid; grid-template-columns:1fr 1fr; gap:12px; margin-bottom:1.5rem;">
        <div class="si-metric">
            <div class="label">OCR Engine</div>
            <div class="value" style="font-size:16px; color:#60A5FA;">EasyOCR + OpenCV</div>
        </div>
        <div class="si-metric">
            <div class="label">AI Model</div>
            <div class="value" style="font-size:16px; color:#A78BFA;">LLaMA-3 70B via Groq</div>
        </div>
        <div class="si-metric">
            <div class="label">Voice</div>
            <div class="value" style="font-size:16px; color:#34D399;">Google Speech API</div>
        </div>
        <div class="si-metric">
            <div class="label">Database</div>
            <div class="value" style="font-size:16px; color:#FB923C;">SQLite</div>
        </div>
    </div>
    
    <div style="color:#64748B; font-size:12px; line-height:1.8;">
        Features: Multimodal OCR (image/voice/manual) · Automatic data extraction · 
        Fraud detection · Duplicate checking · LLaMA-3 AI enhancement · 
        Financial analytics · Budget tracking · AI chatbot advisor · 
        Spending forecasts · Groq-powered reports
    </div>
</div>
""", unsafe_allow_html=True)
