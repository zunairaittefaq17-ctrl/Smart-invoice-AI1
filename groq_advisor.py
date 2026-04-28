import os
import json
import streamlit as st


def get_groq_client():
    api_key = st.secrets.get("GROQ_API_KEY", os.environ.get("GROQ_API_KEY", ""))
    if not api_key or api_key == "your_groq_api_key_here":
        return None
    from groq import Groq
    return Groq(api_key=api_key)


def chat_with_advisor(user_message: str, conversation_history: list, stats: dict) -> str:
    """Financial advisor chatbot powered by Groq LLaMA-3."""
    client = get_groq_client()
    if not client:
        return "⚠️ Groq API key not configured. Add your key in Streamlit Cloud secrets as GROQ_API_KEY."

    system_prompt = f"""You are SmartInvoice AI — an expert personal finance advisor and accountant.

USER'S FINANCIAL SUMMARY:
- Total invoices: {stats.get('total_count', 0)}
- Total spending: {stats.get('total_spend', 0):,.0f} PKR
- Total tax paid: {stats.get('total_tax', 0):,.0f} PKR
- Duplicate invoices detected: {stats.get('duplicates', 0)}
- Fraud alerts: {stats.get('frauds', 0)}
- Spending by category: {json.dumps(stats.get('by_category', {}), indent=2)}
- Top vendors: {json.dumps(stats.get('top_vendors', []), indent=2)}

Your role:
- Give specific, actionable financial advice based on THEIR actual data
- Identify spending patterns, anomalies, and savings opportunities
- Answer questions about their invoices, budgets, and expenses
- Generate tax summaries and accounting insights
- Be concise, warm, and professional
- Use emojis sparingly but effectively
- If asked about a specific vendor/category, reference their actual numbers"""

    messages = [{"role": "system", "content": system_prompt}]
    for msg in conversation_history[-8:]:  # last 8 turns
        messages.append(msg)
    messages.append({"role": "user", "content": user_message})

    try:
        response = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=messages,
            max_tokens=600,
            temperature=0.7,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {str(e)}"


def generate_financial_report(stats: dict, invoices: list) -> str:
    """Generate a detailed financial report using Groq."""
    client = get_groq_client()
    if not client:
        vendor = stats.get("top_vendors", [{}])[0].get("vendor", "N/A") if stats.get("top_vendors") else "N/A"
        cat = list(stats.get("by_category", {}).keys())[0] if stats.get("by_category") else "N/A"
        return f"""## Financial Report

**Total Spend:** {stats.get('total_spend', 0):,.0f} PKR across {stats.get('total_count', 0)} invoices
**Tax Paid:** {stats.get('total_tax', 0):,.0f} PKR
**Top Category:** {cat}
**Top Vendor:** {vendor}

*Add Groq API key for AI-powered insights.*"""

    prompt = f"""Generate a professional financial analysis report for this user.

DATA:
- Total invoices: {stats.get('total_count')}
- Total spending: {stats.get('total_spend', 0):,.0f} PKR
- Total tax: {stats.get('total_tax', 0):,.0f} PKR  
- By category: {json.dumps(stats.get('by_category', {}))}
- Top vendors: {json.dumps(stats.get('top_vendors', []))}
- Monthly trends: {json.dumps(stats.get('monthly', {}))}
- Fraud alerts: {stats.get('frauds', 0)}
- Duplicates: {stats.get('duplicates', 0)}

Write a structured report with:
1. Executive Summary (2-3 sentences)
2. Key Spending Insights (bullet points)
3. Tax Overview
4. Fraud & Compliance Notes
5. Top 3 Actionable Recommendations

Use markdown formatting. Be specific with numbers."""

    try:
        response = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=800,
            temperature=0.4,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Report generation failed: {e}"


def forecast_spending(monthly_data: dict) -> str:
    """Predict next month's spending using Groq."""
    client = get_groq_client()
    if not client or len(monthly_data) < 2:
        if len(monthly_data) >= 2:
            vals = list(monthly_data.values())
            avg = sum(vals) / len(vals)
            return f"📈 Based on your history, estimated next month: **PKR {avg:,.0f}**"
        return "Upload more invoices for spending forecasts."

    prompt = f"""Monthly spending data (PKR): {json.dumps(monthly_data)}

Predict next month's spending. Give:
1. Predicted amount
2. Trend (increasing/stable/decreasing)
3. One suggestion

Be concise — 3 lines max."""

    try:
        response = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
            temperature=0.3,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Forecast error: {e}"
