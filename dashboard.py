import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import json
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.database import get_summary_stats, get_all_invoices, get_budgets
from components.styles import metric_card, section_header
from ai.groq_advisor import forecast_spending


# ── Plotly theme ─────────────────────────────────────────────────────────────
PLOT_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="DM Sans", color="#94A3B8", size=12),
    margin=dict(l=0, r=0, t=30, b=0),
    showlegend=True,
    legend=dict(
        bgcolor="rgba(17,24,39,0.8)",
        bordercolor="rgba(0,212,170,0.2)",
        borderwidth=1,
        font=dict(color="#F1F5F9"),
    ),
)
GRID_STYLE = dict(
    xaxis=dict(gridcolor="rgba(255,255,255,0.05)", linecolor="rgba(255,255,255,0.1)"),
    yaxis=dict(gridcolor="rgba(255,255,255,0.05)", linecolor="rgba(255,255,255,0.1)"),
)
COLORS = ["#00D4AA","#F5C842","#FF4D6D","#60A5FA","#A78BFA","#34D399","#FB923C","#F472B6"]


def show_dashboard():
    stats = get_summary_stats()
    invoices = get_all_invoices()

    # ── KPI Row ───────────────────────────────────────────────────────────────
    section_header("Financial Overview", "📊")
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1: metric_card("Total Invoices",  str(stats["total_count"]), "all time")
    with c2: metric_card("Total Spend",     f"{stats['total_spend']:,.0f}", stats.get('currency','PKR'))
    with c3: metric_card("Tax Recorded",    f"{stats['total_tax']:,.0f}",  "PKR")
    with c4: metric_card("Fraud Alerts",    str(stats["frauds"]),    "flagged", color="rose")
    with c5: metric_card("Duplicates",      str(stats["duplicates"]), "detected", color="gold")

    st.markdown("<br>", unsafe_allow_html=True)

    if not invoices:
        st.markdown("""
<div style='text-align:center; padding:4rem 0; color:#64748B;'>
    <div style='font-size:48px; margin-bottom:1rem;'>📂</div>
    <div style='font-size:18px; font-family:Syne,sans-serif; color:#94A3B8;'>No invoices yet</div>
    <div style='font-size:14px; margin-top:8px;'>Upload your first invoice to see analytics</div>
</div>""", unsafe_allow_html=True)
        return

    df = pd.DataFrame(invoices)
    df["total_amount"] = pd.to_numeric(df["total_amount"], errors="coerce").fillna(0)
    df["upload_date"] = pd.to_datetime(df["upload_date"], errors="coerce")

    # ── Row 1: Monthly Spend + Category Pie ──────────────────────────────────
    col_a, col_b = st.columns([3, 2])

    with col_a:
        section_header("Monthly Spending Trend", "📈")
        monthly = stats.get("monthly", {})
        if monthly:
            months = list(monthly.keys())
            vals   = list(monthly.values())
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=months, y=vals,
                mode="lines+markers",
                name="Spending",
                line=dict(color="#00D4AA", width=3),
                marker=dict(size=8, color="#00FFD1", line=dict(color="#0A0E1A", width=2)),
                fill="tozeroy",
                fillcolor="rgba(0,212,170,0.08)",
            ))
            fig.update_layout(**PLOT_LAYOUT, **GRID_STYLE, height=280)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Upload more invoices across multiple months for trend data.")

    with col_b:
        section_header("By Category", "🍩")
        cat_data = stats.get("by_category", {})
        if cat_data:
            fig = go.Figure(go.Pie(
                labels=list(cat_data.keys()),
                values=list(cat_data.values()),
                hole=0.55,
                marker=dict(colors=COLORS, line=dict(color="#0A0E1A", width=2)),
                textinfo="label+percent",
                textfont=dict(size=11, color="#F1F5F9"),
            ))
            fig.add_annotation(
                text=f"<b>{len(cat_data)}</b><br>Categories",
                x=0.5, y=0.5, font=dict(size=14, color="#F1F5F9"),
                showarrow=False
            )
            fig.update_layout(**PLOT_LAYOUT, height=280, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

    # ── Row 2: Top Vendors + Weekly Bar ──────────────────────────────────────
    col_c, col_d = st.columns(2)

    with col_c:
        section_header("Top Vendors", "🏪")
        vendors = stats.get("top_vendors", [])
        if vendors:
            v_names  = [v["vendor"][:18] for v in vendors]
            v_totals = [v["total"] for v in vendors]
            fig = go.Figure(go.Bar(
                x=v_totals, y=v_names,
                orientation="h",
                marker=dict(
                    color=v_totals,
                    colorscale=[[0,"#1C2535"],[1,"#00D4AA"]],
                    line=dict(width=0),
                ),
                text=[f"PKR {t:,.0f}" for t in v_totals],
                textposition="auto",
                textfont=dict(color="#0A0E1A", size=11),
            ))
            fig.update_layout(**PLOT_LAYOUT, **GRID_STYLE, height=280, xaxis_title="")
            fig.update_yaxes(autorange="reversed")
            st.plotly_chart(fig, use_container_width=True)

    with col_d:
        section_header("Daily Spending (Last 30 Days)", "📅")
        if not df.empty:
            last30 = df[df["upload_date"] >= datetime.now() - timedelta(days=30)].copy()
            if not last30.empty:
                last30["day"] = last30["upload_date"].dt.date
                daily = last30.groupby("day")["total_amount"].sum().reset_index()
                fig = go.Figure(go.Bar(
                    x=daily["day"], y=daily["total_amount"],
                    marker_color="#00D4AA",
                    marker_line_width=0,
                ))
                fig.update_layout(**PLOT_LAYOUT, **GRID_STYLE, height=280)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No transactions in last 30 days.")

    # ── Row 3: Source breakdown + Forecast ───────────────────────────────────
    col_e, col_f = st.columns(2)

    with col_e:
        section_header("Invoice Sources", "📱")
        if not df.empty and "source" in df.columns:
            src = df["source"].value_counts()
            fig = go.Figure(go.Bar(
                x=src.index.tolist(),
                y=src.values.tolist(),
                marker_color=COLORS[:len(src)],
                marker_line_width=0,
                text=src.values.tolist(),
                textposition="outside",
                textfont=dict(color="#F1F5F9"),
            ))
            fig.update_layout(**PLOT_LAYOUT, **GRID_STYLE, height=240, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

    with col_f:
        section_header("AI Spending Forecast", "🔮")
        forecast = forecast_spending(stats.get("monthly", {}))
        st.markdown(f"""
<div class="si-card" style="margin-top:0.5rem;">
    <div style="font-size:13px; color:#94A3B8; line-height:1.7;">{forecast}</div>
</div>
""", unsafe_allow_html=True)

    # ── Budget Tracker ────────────────────────────────────────────────────────
    section_header("Budget Tracker", "🎯")
    budgets = get_budgets()
    cat_data = stats.get("by_category", {})
    if budgets:
        cols = st.columns(min(len(budgets), 4))
        for i, b in enumerate(budgets):
            spent   = cat_data.get(b["category"], 0)
            limit   = b["monthly_limit"]
            pct     = min(spent / limit * 100, 100) if limit > 0 else 0
            color   = "#00D4AA" if pct < 75 else ("#F5C842" if pct < 100 else "#FF4D6D")
            with cols[i % 4]:
                st.markdown(f"""
<div class="si-metric">
    <div class="label">{b['category']}</div>
    <div class="value" style="color:{color}; font-size:20px;">{pct:.0f}%</div>
    <div class="sub">PKR {spent:,.0f} / {limit:,.0f}</div>
    <div style="height:6px; background:#1C2535; border-radius:3px; margin-top:8px;">
        <div style="width:{pct}%; height:6px; background:{color}; border-radius:3px; transition:width 0.5s;"></div>
    </div>
</div>
""", unsafe_allow_html=True)
    else:
        st.info("Set budgets in the Settings tab to track category spending.")


    # ── Recent Invoices Table ─────────────────────────────────────────────────
    section_header("Recent Invoices", "🧾")
    recent = df.head(10).copy()
    if not recent.empty:
        display_cols = ["upload_date","vendor_name","category","total_amount","currency","is_fraud","is_duplicate","source"]
        show_df = recent[[c for c in display_cols if c in recent.columns]].copy()
        show_df["upload_date"] = pd.to_datetime(show_df["upload_date"]).dt.strftime("%b %d %Y")
        show_df.columns = [c.replace("_"," ").title() for c in show_df.columns]
        show_df["Is Fraud"]     = show_df["Is Fraud"].apply(lambda x: "⚠️" if x else "✅")
        show_df["Is Duplicate"] = show_df["Is Duplicate"].apply(lambda x: "🔴" if x else "✅")
        st.dataframe(show_df, use_container_width=True, hide_index=True)
