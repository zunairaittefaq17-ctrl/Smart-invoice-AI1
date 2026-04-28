import streamlit as st
import pandas as pd
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.database import get_all_invoices, delete_invoice
from components.styles import section_header


CATEGORIES = ["All","Food","Transport","Utilities","Medical","Shopping","Telecom","Education","Travel","Other"]


def show_history():
    section_header("Invoice History", "🗂️")

    invoices = get_all_invoices()
    if not invoices:
        st.markdown("""
<div style='text-align:center; padding:4rem 0; color:#64748B;'>
    <div style='font-size:48px; margin-bottom:1rem;'>🗃️</div>
    <div style='font-size:18px; font-family:Syne,sans-serif; color:#94A3B8;'>No invoices yet</div>
    <div style='font-size:14px; margin-top:8px;'>Upload invoices to see them here</div>
</div>""", unsafe_allow_html=True)
        return

    df = pd.DataFrame(invoices)
    df["total_amount"] = pd.to_numeric(df["total_amount"], errors="coerce").fillna(0)

    # ── Filters ───────────────────────────────────────────────────────────────
    st.markdown("#### Search & Filter")
    col1, col2, col3, col4 = st.columns([3,2,2,2])
    with col1:
        search = st.text_input("🔍 Search vendor, category, invoice #...", label_visibility="collapsed",
                               placeholder="Search vendor, category, invoice number...")
    with col2:
        cat_filter = st.selectbox("Category", CATEGORIES, label_visibility="collapsed")
    with col3:
        source_filter = st.selectbox("Source", ["All","image","voice","manual"], label_visibility="collapsed")
    with col4:
        fraud_filter = st.selectbox("Status", ["All","Clean","Fraud Flagged","Duplicates"], label_visibility="collapsed")

    # Apply filters
    filtered = df.copy()

    if search.strip():
        q = search.strip().lower()
        mask = (
            filtered["vendor_name"].fillna("").str.lower().str.contains(q) |
            filtered["category"].fillna("").str.lower().str.contains(q) |
            filtered["invoice_number"].fillna("").str.lower().str.contains(q) |
            filtered["ai_summary"].fillna("").str.lower().str.contains(q)
        )
        filtered = filtered[mask]

    if cat_filter != "All":
        filtered = filtered[filtered["category"] == cat_filter]

    if source_filter != "All":
        filtered = filtered[filtered["source"] == source_filter]

    if fraud_filter == "Fraud Flagged":
        filtered = filtered[filtered["is_fraud"] == 1]
    elif fraud_filter == "Duplicates":
        filtered = filtered[filtered["is_duplicate"] == 1]
    elif fraud_filter == "Clean":
        filtered = filtered[(filtered["is_fraud"] == 0) & (filtered["is_duplicate"] == 0)]

    # ── Summary bar ──────────────────────────────────────────────────────────
    total_shown = filtered["total_amount"].sum()
    st.markdown(f"""
<div style='display:flex; gap:16px; margin:1rem 0; flex-wrap:wrap;'>
    <div style='background:#111827; border:1px solid rgba(0,212,170,0.15); border-radius:10px; padding:10px 18px;'>
        <span style='color:#94A3B8; font-size:12px;'>Showing</span>
        <span style='color:#00D4AA; font-weight:700; font-size:16px; margin-left:8px;'>{len(filtered)}</span>
        <span style='color:#94A3B8; font-size:12px;'> invoices</span>
    </div>
    <div style='background:#111827; border:1px solid rgba(0,212,170,0.15); border-radius:10px; padding:10px 18px;'>
        <span style='color:#94A3B8; font-size:12px;'>Total</span>
        <span style='color:#F5C842; font-weight:700; font-size:16px; margin-left:8px;'>PKR {total_shown:,.0f}</span>
    </div>
</div>
""", unsafe_allow_html=True)

    if filtered.empty:
        st.info("No invoices match your filters.")
        return

    # ── Invoice cards ─────────────────────────────────────────────────────────
    for _, row in filtered.iterrows():
        vendor  = row.get("vendor_name") or "Unknown Vendor"
        amount  = row.get("total_amount") or 0
        curr    = row.get("currency") or "PKR"
        cat     = row.get("category") or "—"
        date    = str(row.get("date") or row.get("upload_date", ""))[:10]
        src     = row.get("source") or "image"
        summary = row.get("ai_summary") or ""
        inv_id  = row.get("id")

        fraud_badge = ""
        if row.get("is_fraud"):
            fraud_badge = '<span class="badge badge-danger">⚠️ FRAUD</span>&nbsp;'
        if row.get("is_duplicate"):
            fraud_badge += '<span class="badge badge-warn">🔴 DUPLICATE</span>'

        src_icon = {"image":"📸","voice":"🎤","manual":"✏️"}.get(src, "📄")

        with st.expander(f"{src_icon}  {vendor[:35]}  —  {curr} {amount:,.0f}  ({cat})  |  {date}", expanded=False):
            col_a, col_b = st.columns([3,1])
            with col_a:
                st.markdown(f"""
<div style='margin-bottom:8px;'>{fraud_badge}</div>
<div class="inv-result-grid" style="grid-template-columns: repeat(auto-fit, minmax(150px,1fr));">
    <div class="inv-field highlight"><div class="f-label">Amount</div><div class="f-value">{curr} {amount:,.2f}</div></div>
    <div class="inv-field"><div class="f-label">Category</div><div class="f-value">{cat}</div></div>
    <div class="inv-field"><div class="f-label">Date</div><div class="f-value">{date or '—'}</div></div>
    <div class="inv-field"><div class="f-label">Source</div><div class="f-value">{src_icon} {src.title()}</div></div>
    <div class="inv-field"><div class="f-label">Invoice #</div><div class="f-value">{row.get('invoice_number') or '—'}</div></div>
    <div class="inv-field"><div class="f-label">Payment</div><div class="f-value">{row.get('payment_method') or '—'}</div></div>
</div>
""", unsafe_allow_html=True)
                if summary:
                    st.markdown(f"<div style='color:#94A3B8; font-size:13px; margin-top:6px; font-style:italic;'>{summary}</div>",
                                unsafe_allow_html=True)

                # Show fraud flags
                import json
                flags_raw = row.get("fraud_flags") or "[]"
                try:
                    flags = json.loads(flags_raw) if isinstance(flags_raw, str) else flags_raw
                except Exception:
                    flags = []
                if flags:
                    st.markdown(f"<div style='color:#FF4D6D; font-size:12px; margin-top:6px;'>🚨 " + " | ".join(flags) + "</div>",
                                unsafe_allow_html=True)

                # Show raw OCR text
                raw = row.get("raw_text","")
                if raw:
                    with st.expander("📄 View raw OCR text"):
                        st.code(raw[:1000], language=None)

            with col_b:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("🗑️ Delete", key=f"del_{inv_id}", use_container_width=True):
                    delete_invoice(inv_id)
                    st.success("Deleted.")
                    st.rerun()
