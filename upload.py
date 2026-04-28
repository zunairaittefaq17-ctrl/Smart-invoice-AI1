import streamlit as st
from PIL import Image
import io
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.ocr_engine import process_invoice_image
from ai.voice_engine import parse_voice_text, enhance_voice_with_groq
from utils.database import save_invoice, get_all_invoices
from components.styles import section_header


CATEGORIES = ["Food","Transport","Utilities","Medical","Shopping","Telecom","Education","Travel","Other"]
CURRENCIES  = ["PKR","USD","GBP","EUR","AED","INR"]


def render_extracted_fields(data: dict):
    """Render the extracted invoice data as a styled card grid."""
    fields = [
        ("Vendor / Store",   data.get("vendor_name"),     True),
        ("Total Amount",     f"{data.get('currency','PKR')} {data.get('total_amount'):,.2f}" if data.get("total_amount") else None, True),
        ("Invoice Number",   data.get("invoice_number"),  False),
        ("Date",             data.get("date"),             False),
        ("Tax / GST",        f"{data.get('currency','PKR')} {data.get('tax_amount'):,.2f}" if data.get("tax_amount") else None, False),
        ("Currency",         data.get("currency"),        False),
        ("Category",         data.get("category"),        False),
        ("Payment Method",   data.get("payment_method"),  False),
    ]
    html = '<div class="inv-result-grid">'
    for label, value, highlighted in fields:
        if value:
            hl = " highlight" if highlighted else ""
            html += f"""
<div class="inv-field{hl}">
    <div class="f-label">{label}</div>
    <div class="f-value">{value}</div>
</div>"""
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


def show_upload():
    section_header("Upload Invoice", "📤")
    st.markdown("<div style='color:#94A3B8; font-size:14px; margin-bottom:1.5rem;'>Upload any bill, receipt, or invoice — our AI will extract all data automatically.</div>", unsafe_allow_html=True)

    tab_img, tab_voice, tab_manual = st.tabs(["📸  Image / PDF", "🎤  Voice Entry", "✏️  Manual Entry"])

    # ─────────────────────────────────────────────────────────────────────────
    # TAB 1 — IMAGE UPLOAD
    # ─────────────────────────────────────────────────────────────────────────
    with tab_img:
        uploaded = st.file_uploader(
            "Drop invoice image here — JPG, PNG, WEBP, PDF",
            type=["jpg","jpeg","png","webp","bmp","tiff"],
            label_visibility="collapsed",
        )

        if uploaded:
            col_img, col_result = st.columns([1, 1], gap="large")

            with col_img:
                img = Image.open(uploaded)
                st.image(img, caption=uploaded.name, use_container_width=True)

            with col_result:
                with st.spinner("🤖 AI is reading your invoice..."):
                    history = get_all_invoices()
                    result  = process_invoice_image(img, uploaded.name, history)

                if "error" in result:
                    st.error(f"OCR failed: {result['error']}")
                    return

                st.markdown("### ✅ Extracted Data")
                render_extracted_fields(result)

                if result.get("ai_summary"):
                    st.markdown(f"""
<div class="si-card" style="margin:0.75rem 0; border-color:rgba(0,212,170,0.3);">
    <span style="font-size:11px; color:#00D4AA; text-transform:uppercase; letter-spacing:0.08em;">AI Summary</span>
    <div style="margin-top:4px; color:#F1F5F9; font-size:14px;">{result['ai_summary']}</div>
</div>""", unsafe_allow_html=True)

                if result.get("fraud_flags"):
                    st.warning("⚠️ **Fraud Flags:** " + " | ".join(result["fraud_flags"]))
                if result.get("is_duplicate"):
                    st.error("🔴 This appears to be a **duplicate invoice**.")

                # Allow editing before save
                st.markdown("#### Edit if needed:")
                with st.expander("✏️ Correct extracted fields"):
                    col1, col2 = st.columns(2)
                    with col1:
                        result["vendor_name"]   = st.text_input("Vendor", value=result.get("vendor_name") or "")
                        result["date"]          = st.text_input("Date",   value=result.get("date") or "")
                        result["invoice_number"]= st.text_input("Invoice #", value=result.get("invoice_number") or "")
                        result["payment_method"]= st.selectbox("Payment", ["","Cash","Card","Digital"],
                                                   index=["","Cash","Card","Digital"].index(result.get("payment_method") or "") if result.get("payment_method") in ["","Cash","Card","Digital"] else 0)
                    with col2:
                        amt_val = result.get("total_amount") or 0.0
                        result["total_amount"]  = st.number_input("Total Amount", value=float(amt_val), min_value=0.0, step=1.0)
                        tax_val = result.get("tax_amount") or 0.0
                        result["tax_amount"]    = st.number_input("Tax Amount", value=float(tax_val), min_value=0.0, step=1.0)
                        result["currency"]      = st.selectbox("Currency", CURRENCIES,
                                                   index=CURRENCIES.index(result.get("currency","PKR")) if result.get("currency","PKR") in CURRENCIES else 0)
                        result["category"]      = st.selectbox("Category", [""] + CATEGORIES,
                                                   index=([""] + CATEGORIES).index(result.get("category","")) if result.get("category","") in ([""] + CATEGORIES) else 0)

                if st.button("💾 Save Invoice to Database", use_container_width=True, key="save_img"):
                    inv_id = save_invoice(result)
                    st.success(f"✅ Invoice saved! ID: #{inv_id}")
                    st.balloons()


    # ─────────────────────────────────────────────────────────────────────────
    # TAB 2 — VOICE ENTRY
    # ─────────────────────────────────────────────────────────────────────────
    with tab_voice:
        st.markdown("""
<div class="si-card" style="margin-bottom:1.5rem;">
    <div style="font-size:15px; font-weight:600; color:#00D4AA; margin-bottom:8px;">🎤 Speak Your Expense</div>
    <div style="color:#94A3B8; font-size:13px; line-height:1.7;">
        Say something like:<br>
        <em>"I spent 850 rupees at KFC for lunch today, paid by card"</em><br>
        <em>"Electricity bill 3400 PKR, paid online this month"</em><br>
        <em>"Paid 1200 for medicine at City Pharmacy"</em>
    </div>
</div>
""", unsafe_allow_html=True)

        voice_method = st.radio("Input method:", ["Type it out (fastest)", "Upload audio file"],
                                horizontal=True, label_visibility="collapsed")

        voice_text = None

        if voice_method == "Type it out (fastest)":
            voice_text = st.text_area(
                "Describe your expense in plain English or Urdu-English mix:",
                placeholder="e.g. Spent 2500 at Hyperstar on groceries today, paid by card",
                height=80,
            )
            if st.button("🔍 Parse This Expense", use_container_width=True, key="parse_voice_text"):
                if voice_text.strip():
                    st.session_state["voice_parsed_text"] = voice_text.strip()

        else:
            audio_file = st.file_uploader("Upload WAV audio recording", type=["wav","flac","aiff"], label_visibility="collapsed")
            if audio_file and st.button("🎧 Transcribe & Parse", use_container_width=True, key="transcribe_audio"):
                with st.spinner("Transcribing audio..."):
                    from ai.voice_engine import transcribe_audio_bytes
                    text = transcribe_audio_bytes(audio_file.read())
                if text and not text.startswith("SPEECH_ERROR"):
                    st.session_state["voice_parsed_text"] = text
                    st.info(f"Transcribed: *{text}*")
                else:
                    st.error("Could not transcribe audio. Please type it instead.")

        # Process voice text
        if st.session_state.get("voice_parsed_text"):
            vt = st.session_state["voice_parsed_text"]
            with st.spinner("🤖 Parsing with AI..."):
                parsed = parse_voice_text(vt)
                parsed = enhance_voice_with_groq(vt, parsed)

            st.markdown("### ✅ Parsed Data")
            render_extracted_fields(parsed)

            st.markdown("#### Review & adjust:")
            with st.expander("✏️ Edit fields"):
                col1, col2 = st.columns(2)
                with col1:
                    parsed["vendor_name"]   = st.text_input("Vendor",  value=parsed.get("vendor_name") or "", key="v_vendor")
                    parsed["category"]      = st.selectbox("Category", [""] + CATEGORIES, key="v_cat",
                                               index=([""] + CATEGORIES).index(parsed.get("category","")) if parsed.get("category","") in ([""] + CATEGORIES) else 0)
                    parsed["payment_method"]= st.selectbox("Payment", ["","Cash","Card","Digital"], key="v_pay",
                                               index=["","Cash","Card","Digital"].index(parsed.get("payment_method") or "") if parsed.get("payment_method") in ["","Cash","Card","Digital"] else 0)
                with col2:
                    amt_val = parsed.get("total_amount") or 0.0
                    parsed["total_amount"]  = st.number_input("Amount", value=float(amt_val), min_value=0.0, step=1.0, key="v_amt")
                    parsed["currency"]      = st.selectbox("Currency", CURRENCIES, key="v_cur",
                                               index=CURRENCIES.index(parsed.get("currency","PKR")) if parsed.get("currency","PKR") in CURRENCIES else 0)
                    parsed["date"]          = st.text_input("Date", value=parsed.get("date") or "today", key="v_date")

            if st.button("💾 Save Voice Invoice", use_container_width=True, key="save_voice"):
                inv_id = save_invoice(parsed)
                st.success(f"✅ Voice invoice saved! ID: #{inv_id}")
                del st.session_state["voice_parsed_text"]
                st.balloons()


    # ─────────────────────────────────────────────────────────────────────────
    # TAB 3 — MANUAL ENTRY
    # ─────────────────────────────────────────────────────────────────────────
    with tab_manual:
        st.markdown("<div style='color:#94A3B8; font-size:14px; margin-bottom:1rem;'>Enter invoice details manually.</div>", unsafe_allow_html=True)
        with st.form("manual_form"):
            col1, col2 = st.columns(2)
            with col1:
                vendor   = st.text_input("Vendor / Store Name *")
                inv_num  = st.text_input("Invoice Number")
                date_val = st.text_input("Date (DD/MM/YYYY)")
                category = st.selectbox("Category", [""] + CATEGORIES)
            with col2:
                amount   = st.number_input("Total Amount *", min_value=0.0, step=1.0)
                tax_amt  = st.number_input("Tax / GST", min_value=0.0, step=1.0)
                currency = st.selectbox("Currency", CURRENCIES)
                payment  = st.selectbox("Payment Method", ["","Cash","Card","Digital"])

            notes = st.text_area("Notes / Description", height=60)
            submitted = st.form_submit_button("💾 Save Invoice", use_container_width=True)

            if submitted:
                if not vendor or amount <= 0:
                    st.error("Vendor name and amount are required.")
                else:
                    data = {
                        "source": "manual",
                        "vendor_name": vendor,
                        "invoice_number": inv_num,
                        "date": date_val,
                        "total_amount": float(amount),
                        "tax_amount": float(tax_amt) if tax_amt else None,
                        "currency": currency,
                        "category": category or None,
                        "payment_method": payment or None,
                        "raw_text": notes,
                        "ai_summary": f"Manual: {vendor} — {currency} {amount:,.0f}",
                        "is_fraud": False,
                        "is_duplicate": False,
                        "fraud_flags": [],
                    }
                    inv_id = save_invoice(data)
                    st.success(f"✅ Invoice saved! ID: #{inv_id}")
                    st.balloons()
  
