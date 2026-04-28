import re
import json
import os
import streamlit as st


def transcribe_audio_bytes(audio_bytes: bytes) -> str:
    """
    Convert raw audio bytes → text using Google Speech Recognition (free, no key needed).
    Supports WAV, FLAC, or AIFF input.
    """
    import speech_recognition as sr
    import tempfile

    recognizer = sr.Recognizer()
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    try:
        with sr.AudioFile(tmp_path) as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio = recognizer.record(source)
        text = recognizer.recognize_google(audio, language="en-US")
        return text
    except sr.UnknownValueError:
        return ""
    except sr.RequestError as e:
        return f"SPEECH_ERROR: {e}"
    finally:
        try:
            os.remove(tmp_path)
        except Exception:
            pass


def parse_voice_text(text: str) -> dict:
    """
    Parse a spoken expense like:
    'I spent five hundred rupees at Imtiaz store on groceries'
    'Paid 1200 for electricity bill today'
    'Restaurant lunch at KFC cost 850 rupees paid by card'
    """
    if not text:
        return None

    text_clean = text.lower().strip()

    data = {
        "source": "voice",
        "raw_text": text,
        "vendor_name": None,
        "total_amount": None,
        "currency": "PKR",
        "category": None,
        "payment_method": None,
        "date": "today",
        "invoice_number": None,
        "tax_amount": None,
        "items": [],
        "ai_summary": f'Voice entry: "{text[:80]}"',
    }

    # ── Amount extraction ──────────────────────────────────────────────────
    # Handles: "500 rupees", "1,200 PKR", "five hundred", "$50", "Rs 300"
    written_numbers = {
        "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
        "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
        "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14,
        "fifteen": 15, "sixteen": 16, "seventeen": 17, "eighteen": 18,
        "nineteen": 19, "twenty": 20, "thirty": 30, "forty": 40,
        "fifty": 50, "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90,
        "hundred": 100, "thousand": 1000, "lakh": 100000,
    }

    # Numeric amount
    amount_match = re.search(
        r'(\d[\d,]*\.?\d*)\s*(?:rupees?|pkr|rs\.?|dollars?|usd|\$|pounds?|gbp|dirhams?|aed)?',
        text_clean
    )
    if amount_match:
        try:
            data["total_amount"] = float(amount_match.group(1).replace(',', ''))
        except ValueError:
            pass

    # Written amount fallback (e.g. "five hundred")
    if data["total_amount"] is None:
        words = text_clean.split()
        val = 0
        current = 0
        for w in words:
            if w in written_numbers:
                n = written_numbers[w]
                if n == 100:
                    current = current * 100 if current else 100
                elif n == 1000:
                    val += current * 1000
                    current = 0
                elif n == 100000:
                    val += current * 100000
                    current = 0
                else:
                    current += n
        val += current
        if val > 0:
            data["total_amount"] = float(val)

    # ── Currency ──────────────────────────────────────────────────────────
    if re.search(r'dollar|usd|\$', text_clean):
        data["currency"] = "USD"
    elif re.search(r'pound|gbp|£', text_clean):
        data["currency"] = "GBP"
    elif re.search(r'euro|eur|€', text_clean):
        data["currency"] = "EUR"
    elif re.search(r'dirham|aed', text_clean):
        data["currency"] = "AED"
    else:
        data["currency"] = "PKR"

    # ── Vendor / store name ───────────────────────────────────────────────
    vendor_match = re.search(
        r'(?:at|from|in|to)\s+([A-Za-z][A-Za-z\s]{2,30?})(?:\s+(?:on|for|today|yesterday|the|store|restaurant|pharmacy|shop)|\s*$)',
        text, re.IGNORECASE
    )
    if vendor_match:
        data["vendor_name"] = vendor_match.group(1).strip().title()

    # ── Payment method ────────────────────────────────────────────────────
    if re.search(r'\bcard\b|debit|credit|visa|master', text_clean):
        data["payment_method"] = "Card"
    elif re.search(r'easypaisa|jazzcash|transfer|online', text_clean):
        data["payment_method"] = "Digital"
    elif re.search(r'\bcash\b', text_clean):
        data["payment_method"] = "Cash"

    # ── Auto-category ─────────────────────────────────────────────────────
    category_map = {
        "Food":       ["food","restaurant","lunch","dinner","breakfast","groceries","meal","eat","biryani","pizza","burger","cafe","bakery","kfc","mcdonalds"],
        "Transport":  ["fuel","petrol","cng","uber","careem","taxi","bus","metro","transport","ride","oil","tyre"],
        "Medical":    ["medicine","doctor","pharmacy","hospital","clinic","lab","medical","prescription"],
        "Shopping":   ["shopping","clothes","shoes","store","mart","online","amazon","daraz","bought"],
        "Utilities":  ["electricity","gas","water","internet","bill","wapda","phone","mobile","recharge","utility"],
        "Education":  ["tuition","fee","book","school","university","course","class"],
        "Travel":     ["hotel","flight","airline","booking","trip","ticket","travel"],
    }
    for cat, keywords in category_map.items():
        if any(kw in text_clean for kw in keywords):
            data["category"] = cat
            break

    # ── Build summary ─────────────────────────────────────────────────────
    vendor = data.get("vendor_name") or "Unknown"
    amount = data.get("total_amount")
    currency = data.get("currency")
    if amount:
        data["ai_summary"] = f"Voice: {vendor} — {currency} {amount:,.0f}"
    else:
        data["ai_summary"] = f'Voice entry: "{text[:60]}"'

    return data


def enhance_voice_with_groq(text: str, base_data: dict) -> dict:
    """Use Groq LLaMA to improve voice parsing accuracy."""
    try:
        api_key = st.secrets.get("GROQ_API_KEY", os.environ.get("GROQ_API_KEY", ""))
        if not api_key or api_key == "your_groq_api_key_here":
            return base_data

        from groq import Groq
        client = Groq(api_key=api_key)

        prompt = f"""Parse this spoken expense statement into structured JSON.

SPOKEN TEXT: "{text}"

INITIAL PARSE:
{json.dumps(base_data, indent=2)}

Return ONLY valid JSON (no markdown):
{{
  "vendor_name": "string or null",
  "total_amount": number or null,
  "currency": "PKR/USD/GBP/EUR/AED",
  "category": "Food/Transport/Utilities/Medical/Shopping/Telecom/Education/Travel/Other",
  "payment_method": "Cash/Card/Digital or null",
  "date": "today/yesterday/YYYY-MM-DD or null",
  "ai_summary": "one sentence"
}}"""

        response = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.1,
        )
        result_text = response.choices[0].message.content.strip()
        result_text = re.sub(r'^```json\s*|^```\s*|\s*```$', '', result_text)
        enhanced = json.loads(result_text)
        for key, val in enhanced.items():
            if val is not None:
                base_data[key] = val
        return base_data
    except Exception:
        return base_data
