# 💎 SmartInvoice AI

> **Final Year Project** — AI-Powered Invoice Processing, Expense Management & Financial Analytics Platform

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://your-app-url.streamlit.app)

---

## 🌟 What It Does

SmartInvoice AI turns any photo of a bill, receipt, or invoice into structured financial data — automatically. No manual typing needed.

| Feature | Description |
|---------|-------------|
| 📸 **OCR Engine** | EasyOCR + OpenCV reads ANY invoice image |
| 🤖 **AI Extraction** | Groq LLaMA-3 70B fills in missing fields |
| 🎤 **Voice Entry** | Speak your expense, AI parses it |
| 📊 **Dashboard** | Beautiful charts, trends, category analysis |
| 🔍 **Fraud Detection** | Flags suspicious invoices automatically |
| 💬 **AI Advisor** | Chat with LLaMA-3 about your finances |
| 🎯 **Budget Tracker** | Set limits, track spending in real-time |
| 🗂️ **Search History** | Full-text search across all invoices |

---

## 🚀 Deploy to Streamlit Cloud (No VS Code needed!)

### Step 1 — Fork this repo on GitHub
1. Go to `github.com` → Sign up / Login  
2. Click the **Fork** button on this repo  
3. You now have your own copy

### Step 2 — Get your Groq API Key (Free)
1. Go to [console.groq.com](https://console.groq.com)  
2. Sign up (it's free)  
3. Click **API Keys** → **Create API Key**  
4. Copy it — looks like `gsk_...`

### Step 3 — Deploy on Streamlit Cloud
1. Go to [share.streamlit.io](https://share.streamlit.io)  
2. Sign in with GitHub  
3. Click **New app**  
4. Select your forked repo  
5. Set **Main file path** to: `app.py`  
6. Click **Advanced settings** → **Secrets** and paste:

```toml
GROQ_API_KEY = "gsk_your_key_here"
```

7. Click **Deploy!**  
8. Wait ~3 minutes → Your app is LIVE! 🎉

---

## 💻 Run Locally (Optional)

```bash
# 1. Clone
git clone https://github.com/YOURUSERNAME/SmartInvoiceAI.git
cd SmartInvoiceAI

# 2. Install Python 3.10+
python --version

# 3. Install dependencies
pip install -r requirements.txt

# 4. Add your Groq key
# Edit .streamlit/secrets.toml and add:
# GROQ_API_KEY = "gsk_your_key"

# 5. Run
streamlit run app.py
# Opens at http://localhost:8501
```

---

## 🛠 Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Streamlit + Custom CSS (Dark Luxury Theme) |
| OCR | EasyOCR + OpenCV (image preprocessing) |
| AI Model | Groq LLaMA-3 70B (invoice parsing + advisor) |
| Voice | Google Speech Recognition API |
| Database | SQLite (auto-created, no setup needed) |
| Charts | Plotly (interactive, dark theme) |
| Deployment | Streamlit Cloud (free) |

---

## 📁 Project Structure

```
SmartInvoiceAI/
├── app.py                  ← Main entry point (run this)
├── requirements.txt        ← All dependencies
├── .streamlit/
│   ├── config.toml        ← Theme (dark luxury)
│   └── secrets.toml       ← API keys (never commit this)
├── ai/
│   ├── ocr_engine.py      ← EasyOCR + LLaMA extraction
│   ├── voice_engine.py    ← Speech-to-invoice
│   └── groq_advisor.py    ← Chatbot + reports
├── pages/
│   ├── dashboard.py       ← Charts & analytics
│   ├── upload.py          ← Invoice upload UI
│   ├── history.py         ← Search & browse invoices
│   ├── advisor.py         ← AI chatbot
│   └── settings.py        ← Budgets & config
├── components/
│   └── styles.py          ← CSS theme + UI components
├── utils/
│   └── database.py        ← SQLite operations
└── data/
    └── smartinvoice.db    ← Auto-created database
```

---

## 🎓 Academic Significance

This project demonstrates:
- **Computer Vision**: Image preprocessing with OpenCV
- **NLP**: Named entity extraction with regex + transformer models
- **Large Language Models**: Groq LLaMA-3 for intelligent parsing
- **Speech Recognition**: Real-time voice-to-text processing
- **Financial Analytics**: Fraud detection, duplicate identification, forecasting
- **Full-Stack Development**: Complete web application from UI to database
- **Cloud Deployment**: Production-grade SaaS deployment

---

*SmartInvoice AI — Final Year Project 2024*
