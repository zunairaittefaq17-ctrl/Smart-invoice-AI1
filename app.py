import streamlit as st
import sys, os

# ── Path setup ────────────────────────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ── Page config (MUST be first Streamlit call) ────────────────────────────────
st.set_page_config(
    page_title="SmartInvoice AI",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Imports after page config ─────────────────────────────────────────────────
from utils.database import init_db
from components.styles import inject_global_css
from pages.dashboard import show_dashboard
from pages.upload    import show_upload
from pages.history   import show_history
from pages.advisor   import show_advisor
from pages.settings  import show_settings

# ── Database init ─────────────────────────────────────────────────────────────
init_db()

# ── Global CSS ────────────────────────────────────────────────────────────────
inject_global_css()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    # Logo / Brand
    st.markdown("""
<div style="text-align:center; padding:1.5rem 0 2rem;">
    <div style="font-size:40px; margin-bottom:8px;">💎</div>
    <div style="font-family:'Syne',sans-serif; font-size:20px; font-weight:800; 
                background:linear-gradient(135deg,#00D4AA,#60A5FA); 
                -webkit-background-clip:text; -webkit-text-fill-color:transparent;">
        SmartInvoice AI
    </div>
    <div style="font-size:11px; color:#64748B; margin-top:4px; letter-spacing:0.1em;">
        FINANCIAL INTELLIGENCE
    </div>
</div>
""", unsafe_allow_html=True)

    # Navigation
    nav_items = {
        "📊  Dashboard":     "dashboard",
        "📤  Upload Invoice": "upload",
        "🗂️  Invoice History": "history",
        "🤖  AI Advisor":    "advisor",
        "⚙️  Settings":      "settings",
    }

    if "page" not in st.session_state:
        st.session_state.page = "dashboard"

    for label, page_key in nav_items.items():
        is_active = st.session_state.page == page_key
        btn_style = """
<style>
div[data-testid="stButton"]:has(button[aria-label="{label}"]) button {{
    background: rgba(0,212,170,0.15) !important;
    color: #00D4AA !important;
    border-color: rgba(0,212,170,0.3) !important;
}}
</style>""".format(label=label)

        if is_active:
            st.markdown(f"""
<div style="background:rgba(0,212,170,0.1); border:1px solid rgba(0,212,170,0.25);
     border-radius:10px; padding:10px 14px; margin:3px 0;
     color:#00D4AA; font-size:14px; font-weight:600; cursor:default;">
    {label}
</div>""", unsafe_allow_html=True)
        else:
            if st.button(label, key=f"nav_{page_key}", use_container_width=True):
                st.session_state.page = page_key
                st.rerun()

    # Sidebar footer
    st.markdown("""
<div style="position:fixed; bottom:0; left:0; width:240px; padding:1rem;
     background:#111827; border-top:1px solid rgba(0,212,170,0.1);
     font-size:11px; color:#475569; text-align:center;">
    SmartInvoice AI &nbsp;·&nbsp; FYP 2024<br>
    <span style="color:#00D4AA;">Powered by LLaMA-3 + EasyOCR</span>
</div>
""", unsafe_allow_html=True)


# ── Page Router ───────────────────────────────────────────────────────────────
page = st.session_state.get("page", "dashboard")

if page == "dashboard":
    show_dashboard()
elif page == "upload":
    show_upload()
elif page == "history":
    show_history()
elif page == "advisor":
    show_advisor()
elif page == "settings":
    show_settings()
