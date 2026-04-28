import streamlit as st


def inject_global_css():
    """Inject the global dark-luxury CSS theme into Streamlit."""
    st.markdown("""
<style>
/* ─── Import Fonts ──────────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;500;600;700;800&family=DM+Sans:wght@300;400;500&display=swap');

/* ─── Root Variables ────────────────────────────────────── */
:root {
    --emerald:   #00D4AA;
    --emerald2:  #00FFD1;
    --gold:      #F5C842;
    --rose:      #FF4D6D;
    --ink:       #0A0E1A;
    --ink2:      #111827;
    --ink3:      #1C2535;
    --ink4:      #243047;
    --text1:     #F1F5F9;
    --text2:     #94A3B8;
    --text3:     #64748B;
    --border:    rgba(0,212,170,0.15);
    --border2:   rgba(0,212,170,0.30);
}

/* ─── Base ──────────────────────────────────────────────── */
html, body, .stApp {
    background-color: var(--ink) !important;
    color: var(--text1) !important;
    font-family: 'DM Sans', sans-serif !important;
}

.main .block-container {
    padding: 2rem 2.5rem !important;
    max-width: 1400px !important;
}

/* ─── Headings ──────────────────────────────────────────── */
h1, h2, h3, h4 { font-family: 'Syne', sans-serif !important; }

/* ─── Sidebar ───────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background: var(--ink2) !important;
    border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] .block-container {
    padding: 1.5rem 1rem !important;
}

/* ─── Cards ─────────────────────────────────────────────── */
.si-card {
    background: var(--ink2);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 1.5rem;
    transition: border-color 0.2s, transform 0.2s;
}
.si-card:hover {
    border-color: var(--border2);
    transform: translateY(-2px);
}

/* Metric card */
.si-metric {
    background: var(--ink3);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1.25rem 1.5rem;
    text-align: left;
}
.si-metric .label {
    font-size: 12px;
    color: var(--text2);
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 6px;
    font-family: 'DM Sans', sans-serif;
}
.si-metric .value {
    font-size: 28px;
    font-weight: 700;
    font-family: 'Syne', sans-serif;
    color: var(--emerald);
    line-height: 1;
}
.si-metric .sub {
    font-size: 12px;
    color: var(--text3);
    margin-top: 4px;
}

/* Status badges */
.badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.04em;
}
.badge-ok     { background: rgba(0,212,170,0.15); color: var(--emerald); border: 1px solid rgba(0,212,170,0.3); }
.badge-warn   { background: rgba(245,200,66,0.15); color: var(--gold); border: 1px solid rgba(245,200,66,0.3); }
.badge-danger { background: rgba(255,77,109,0.15); color: var(--rose); border: 1px solid rgba(255,77,109,0.3); }

/* ─── Inputs & Buttons ──────────────────────────────────── */
.stTextInput > div > input,
.stTextArea > div > textarea,
.stSelectbox > div > div,
.stNumberInput > div > input {
    background: var(--ink3) !important;
    border: 1px solid var(--border) !important;
    color: var(--text1) !important;
    border-radius: 10px !important;
}
.stTextInput > div > input:focus,
.stTextArea > div > textarea:focus {
    border-color: var(--emerald) !important;
    box-shadow: 0 0 0 2px rgba(0,212,170,0.2) !important;
}

.stButton > button {
    background: linear-gradient(135deg, var(--emerald), #009E7F) !important;
    color: #0A0E1A !important;
    font-weight: 700 !important;
    font-family: 'Syne', sans-serif !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 0.6rem 1.8rem !important;
    transition: opacity 0.2s, transform 0.1s !important;
    letter-spacing: 0.02em !important;
}
.stButton > button:hover {
    opacity: 0.88 !important;
    transform: translateY(-1px) !important;
}
.stButton > button[kind="secondary"] {
    background: var(--ink3) !important;
    color: var(--text1) !important;
    border: 1px solid var(--border) !important;
}

/* ─── File uploader ─────────────────────────────────────── */
[data-testid="stFileUploader"] {
    background: var(--ink3) !important;
    border: 2px dashed var(--border2) !important;
    border-radius: 16px !important;
    padding: 1rem !important;
}
[data-testid="stFileUploader"]:hover {
    border-color: var(--emerald) !important;
    background: rgba(0,212,170,0.04) !important;
}

/* ─── Dataframe / tables ────────────────────────────────── */
.stDataFrame, [data-testid="stDataFrame"] {
    background: var(--ink2) !important;
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
    overflow: hidden !important;
}

/* ─── Plotly charts ─────────────────────────────────────── */
.js-plotly-plot {
    border-radius: 12px !important;
    overflow: hidden !important;
}

/* ─── Tabs ───────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
    background: var(--ink3) !important;
    border-radius: 12px !important;
    padding: 4px !important;
    border: 1px solid var(--border) !important;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: var(--text2) !important;
    border-radius: 8px !important;
    font-family: 'DM Sans', sans-serif !important;
}
.stTabs [aria-selected="true"] {
    background: var(--emerald) !important;
    color: #0A0E1A !important;
    font-weight: 600 !important;
}

/* ─── Expander ──────────────────────────────────────────── */
.streamlit-expanderHeader {
    background: var(--ink3) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    color: var(--text1) !important;
}

/* ─── Success / warning / error messages ───────────────── */
.stAlert {
    border-radius: 10px !important;
    border: none !important;
}
[data-baseweb="notification"][kind="positive"] {
    background: rgba(0,212,170,0.1) !important;
    border-left: 3px solid var(--emerald) !important;
}

/* ─── Scrollbar ─────────────────────────────────────────── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: var(--ink2); }
::-webkit-scrollbar-thumb { background: var(--ink4); border-radius: 10px; }
::-webkit-scrollbar-thumb:hover { background: var(--text3); }

/* ─── Section headers ───────────────────────────────────── */
.section-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin: 1.5rem 0 1rem;
    padding-bottom: 10px;
    border-bottom: 1px solid var(--border);
}
.section-header h3 {
    margin: 0;
    color: var(--text1);
    font-size: 18px;
}
.section-dot {
    width: 8px; height: 8px;
    border-radius: 50%;
    background: var(--emerald);
    flex-shrink: 0;
}

/* ─── Invoice result card ───────────────────────────────── */
.inv-result-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 12px;
    margin: 1rem 0;
}
.inv-field {
    background: var(--ink3);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 10px 14px;
}
.inv-field .f-label {
    font-size: 11px;
    color: var(--text2);
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-bottom: 4px;
}
.inv-field .f-value {
    font-size: 16px;
    font-weight: 600;
    color: var(--text1);
    font-family: 'Syne', sans-serif;
}
.inv-field.highlight .f-value { color: var(--emerald); }

/* ─── Chatbot messages ──────────────────────────────────── */
.chat-bubble {
    padding: 0.9rem 1.2rem;
    border-radius: 14px;
    margin: 6px 0;
    max-width: 85%;
    line-height: 1.6;
    font-size: 14px;
}
.chat-user {
    background: rgba(0,212,170,0.12);
    border: 1px solid rgba(0,212,170,0.25);
    margin-left: auto;
    border-bottom-right-radius: 4px;
}
.chat-ai {
    background: var(--ink3);
    border: 1px solid var(--border);
    margin-right: auto;
    border-bottom-left-radius: 4px;
}
</style>
""", unsafe_allow_html=True)


def metric_card(label: str, value: str, sub: str = "", color: str = "emerald"):
    """Render a styled metric card."""
    color_map = {
        "emerald": "#00D4AA",
        "gold":    "#F5C842",
        "rose":    "#FF4D6D",
        "blue":    "#60A5FA",
    }
    c = color_map.get(color, "#00D4AA")
    st.markdown(f"""
<div class="si-metric">
    <div class="label">{label}</div>
    <div class="value" style="color:{c}">{value}</div>
    {'<div class="sub">' + sub + '</div>' if sub else ''}
</div>
""", unsafe_allow_html=True)


def section_header(title: str, icon: str = ""):
    st.markdown(f"""
<div class="section-header">
    <span class="section-dot"></span>
    <h3>{icon}&nbsp;{title}</h3>
</div>
""", unsafe_allow_html=True)


def status_badge(text: str, kind: str = "ok"):
    """kind: ok | warn | danger"""
    st.markdown(f'<span class="badge badge-{kind}">{text}</span>', unsafe_allow_html=True)
