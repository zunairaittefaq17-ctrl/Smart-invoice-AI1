import re
import json
import os
import numpy as np
from PIL import Image
import streamlit as st

# ── Lazy-load EasyOCR so it doesn't crash if not installed ──────────────────
_reader = None

def _get_reader():
    global _reader
    if _reader is None:
        import easyocr
        _reader = easyocr.Reader(['en'], gpu=False, verbose=False)
    return _reader


# ── Image pre-processing ────────────────────────────────────────────────────
def preprocess_image(pil_image: Image.Image) -> np.ndarray:
    """Convert PIL image → enhanced numpy array for better OCR."""
    import cv2
    img = np.array(pil_image.convert("RGB"))
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    # Adaptive threshold — handles uneven lighting, shadows, phone photos
    thresh = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 31, 10
    )
    # Light denoising
    denoised = cv2.fastNlMeansDenoising(thresh, h=15)
    return denoised


# ── Raw text extraction ──────────────────────────────────────────────────────
def extract_raw_text(pil_image: Image.Image) -> str:
    """Run EasyOCR on image and return concatenated text."""
    try:
        processed = preprocess_image(pil_image)
        reader = _get_reader()
        results = reader.readtext(processed, detail=1, paragraph=False)
        # Keep only results with confidence > 40%
        lines = [text for (_, text, conf) in results if conf > 0.40]
        return "\n".join(lines)
    except Exception as e:
        return f"OCR_ERROR: {str(e)}"


# ── Regex-based field parser (works offline, no API needed) ─────────────────
def parse_fields_regex(raw_text: str) -> dict:
    text = raw_text

    data = {
        "invoice_number": None,
        "date": None,
        "vendor_name": None,
        "total_amount": None,
        "tax_amount": None,
        "currency": "PKR",
        "payment_method": None,
        "category": None,
        "items": [],
    }

    # Invoice number
    m = re.search(r'(?:invoice|inv|bill|receipt|rcpt)\s*(?:no|#|num|number)?[:\s.-]*([A-Z0-9]{3,20})',
                  text, re.IGNORECASE)
    if m:
        data["invoice_number"] = m.group(1).strip()

    # Date — handles DD/MM/YYYY, MM-DD-YYYY, Month DD YYYY etc.
    date_patterns = [
        r'\b(\d{1,2}[./-]\d{1,2}[./-]\d{2,4})\b',
        r'\b(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{2,4})\b',
        r'\b((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4})\b',
    ]
    for pat in date_patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            data["date"] = m.group(1)
            break

    # Total amount
    total_patterns = [
        r'(?:grand\s*total|total\s*amount|net\s*total|amount\s*due|total\s*payable|total)[:\s]*(?:PKR|Rs\.?|USD|\$|£|€|AED|INR)?\s*([\d,]+\.?\d*)',
        r'(?:PKR|Rs\.?)\s*([\d,]+\.?\d*)',
        r'\$\s*([\d,]+\.?\d*)',
    ]
    for pat in total_patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            try:
                data["total_amount"] = float(m.group(1).replace(',', ''))
                break
            except ValueError:
                pass

    # Tax
    m = re.search(r'(?:tax|gst|vat|sales\s*tax)[:\s]*(?:PKR|Rs\.?|USD|\$)?\s*([\d,]+\.?\d*)',
                  text, re.IGNORECASE)
    if m:
        try:
            data["tax_amount"] = float(m.group(1).replace(',', ''))
        except ValueError:
            pass

    # Currency detection
    if re.search(r'\bPKR\b|Rs\.?\s*\d|rupee', text, re.IGNORECASE):
        data["currency"] = "PKR"
    elif re.search(r'\$|USD', text):
        data["currency"] = "USD"
    elif re.search(r'£|GBP', text):
        data["currency"] = "GBP"
    elif re.search(r'€|EUR', text):
        data["currency"] = "EUR"
    elif re.search(r'AED|dirham', text, re.IGNORECASE):
        data["currency"] = "AED"

    # Payment method
    if re.search(r'cash', text, re.IGNORECASE):
        data["payment_method"] = "Cash"
    elif re.search(r'card|visa|master|debit|credit', text, re.IGNORECASE):
        data["payment_method"] = "Card"
    elif re.search(r'easypaisa|jazzcash|bank\s*transfer|online', text, re.IGNORECASE):
        data["payment_method"] = "Digital"

    # Auto-category
    category_map = {
        "Utilities":  ["electricity","wapda","k-electric","sui gas","wasa","nepra","ptcl","water bill"],
        "Food":       ["restaurant","cafe","food","meal","pizza","burger","biryani","dhaba","bakery","chicken","mcdonalds","kfc","subway"],
        "Transport":  ["fuel","petrol","cng","uber","careem","toll","bus","metro","oil","tyre"],
        "Medical":    ["pharmacy","hospital","clinic","labs","medicine","medical","doctor"],
        "Shopping":   ["store","mart","mall","hyperstar","metro","carrefour","daraz","clothing","shoes"],
        "Telecom":    ["jazz","ufone","zong","telenor","stc","internet","mobile","sim"],
        "Education":  ["school","university","tuition","fee","books","stationary"],
        "Travel":     ["hotel","airline","pia","airblue","booking","airbnb","hostel"],
    }
    text_lower = text.lower()
    for cat, keywords in category_map.items():
        if any(kw in text_lower for kw in keywords):
            data["category"] = cat
            break

    # Vendor name — try to grab first meaningful line
    lines = [l.strip() for l in text.split('\n') if len(l.strip()) > 3]
    if lines:
        # Skip lines that look like addresses or pure numbers
        for line in lines[:5]:
            if not re.match(r'^[\d\s,.-]+$', line) and len(line) > 3:
                data["vendor_name"] = line[:60]
                break

    return data


# ── Groq LLaMA enhancement (if API key available) ───────────────────────────
def enhance_with_groq(raw_text: str, base_data: dict) -> dict:
    """
    Use Groq's LLaMA-3 to intelligently fill missing fields.
    Falls back gracefully if no API key or network issue.
    """
    try:
        api_key = st.secrets.get("GROQ_API_KEY", os.environ.get("GROQ_API_KEY", ""))
        if not api_key or api_key == "your_groq_api_key_here":
            return base_data

        from groq import Groq
        client = Groq(api_key=api_key)

        prompt = f"""You are an expert invoice parser. Extract structured data from this invoice text.

INVOICE TEXT:
{raw_text[:3000]}

ALREADY EXTRACTED (may have None values to fill):
{json.dumps(base_data, indent=2)}

Return ONLY valid JSON with these exact keys (fill missing ones, keep correct ones):
{{
  "invoice_number": "string or null",
  "date": "string or null",
  "vendor_name": "string or null",
  "total_amount": number or null,
  "tax_amount": number or null,
  "currency": "PKR/USD/GBP/EUR/AED/INR",
  "payment_method": "Cash/Card/Digital or null",
  "category": "Food/Transport/Utilities/Medical/Shopping/Telecom/Education/Travel/Other or null",
  "items": [{{"name": "...", "qty": number, "price": number}}],
  "ai_summary": "One sentence summary of this invoice"
}}

Return ONLY the JSON, no explanation."""

        response = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=800,
            temperature=0.1,
        )
        result_text = response.choices[0].message.content.strip()
        # Strip markdown code fences if present
        result_text = re.sub(r'^```json\s*', '', result_text)
        result_text = re.sub(r'^```\s*', '', result_text)
        result_text = re.sub(r'\s*```$', '', result_text)
        enhanced = json.loads(result_text)
        # Merge: enhanced values override base only where base has None
        for key, val in enhanced.items():
            if val is not None:
                base_data[key] = val
        return base_data
    except Exception:
        return base_data


# ── Fraud & duplicate checks ─────────────────────────────────────────────────
def check_fraud(invoice_data: dict, history: list) -> dict:
    flags = []
    amount = invoice_data.get("total_amount") or 0

    if history and amount > 0:
        amounts = [h.get("total_amount") or 0 for h in history if h.get("total_amount")]
        if amounts:
            avg = sum(amounts) / len(amounts)
            if avg > 0 and amount > avg * 6:
                flags.append(f"Amount is {amount/avg:.1f}x above your average")

    if not invoice_data.get("vendor_name"):
        flags.append("No vendor name detected")
    if not invoice_data.get("date"):
        flags.append("No date found on invoice")
    if amount > 500000 and amount % 100000 == 0:
        flags.append("Suspiciously round large amount")
    if amount < 0:
        flags.append("Negative amount detected")

    return {"is_fraud": len(flags) >= 2, "fraud_flags": flags}


def check_duplicate(new_inv: dict, history: list) -> bool:
    for h in history:
        match_count = 0
        if h.get("invoice_number") and h.get("invoice_number") == new_inv.get("invoice_number"):
            match_count += 2
        if h.get("total_amount") and h.get("total_amount") == new_inv.get("total_amount"):
            match_count += 1
        if h.get("vendor_name") and h.get("vendor_name") == new_inv.get("vendor_name"):
            match_count += 1
        if match_count >= 3:
            return True
    return False


# ── Master pipeline ──────────────────────────────────────────────────────────
def process_invoice_image(pil_image: Image.Image, file_name: str, history: list) -> dict:
    """
    Full pipeline:
    1. OCR → raw text
    2. Regex parse → base fields
    3. Groq LLaMA enhance → fill gaps
    4. Fraud + duplicate check
    5. Return complete structured dict
    """
    raw_text = extract_raw_text(pil_image)

    if raw_text.startswith("OCR_ERROR"):
        return {"error": raw_text, "raw_text": raw_text}

    base_data = parse_fields_regex(raw_text)
    enriched = enhance_with_groq(raw_text, base_data)

    fraud_result = check_fraud(enriched, history)
    is_dup = check_duplicate(enriched, history)

    enriched["raw_text"] = raw_text
    enriched["is_fraud"] = fraud_result["is_fraud"]
    enriched["fraud_flags"] = fraud_result["fraud_flags"]
    enriched["is_duplicate"] = is_dup
    enriched["file_name"] = file_name
    enriched["source"] = "image"

    if not enriched.get("ai_summary"):
        vendor = enriched.get("vendor_name", "Unknown vendor")
        amount = enriched.get("total_amount", 0)
        currency = enriched.get("currency", "PKR")
        enriched["ai_summary"] = f"{vendor} — {currency} {amount:,.0f}" if amount else f"Invoice from {vendor}"

    return enriched
