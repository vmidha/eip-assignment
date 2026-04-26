"""
app.py
Earnings Intelligence Platform — main Streamlit application.
Three tabs: Analyze | Trends | Compare
"""

import json
import os
import streamlit as st
from dotenv import load_dotenv

import database as db
import analyzer as az
from visualizations import build_trend_dashboard, get_risk_detail
from export import build_analysis_pdf, build_comparison_pdf, build_trends_pdf

load_dotenv()

# ── Page config ──────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Earnings Intelligence Platform",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

db.init_db()

# ── CSS ──────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  /* ── Global ── */
  html, body, [class*="css"] {
    font-family: 'Inter', 'Segoe UI', sans-serif;
  }

  /* ── Hide Streamlit chrome ── */
  #MainMenu { visibility: hidden; }
  footer { visibility: hidden; }
  header { visibility: hidden; }

  /* ── Main content padding ── */
  .block-container {
    padding-top: 1.8rem !important;
    padding-bottom: 2rem !important;
    padding-left: 2.5rem !important;
    padding-right: 2.5rem !important;
    max-width: 100% !important;
  }

  /* ── Header ── */
  .eip-header {
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 1.4rem 2rem;
    background: linear-gradient(135deg, #0A1628 0%, #112240 100%);
    border-radius: 12px;
    margin-bottom: 1.6rem;
    border: 1px solid #1e3a5f;
  }
  .eip-header-icon {
    font-size: 2rem;
    line-height: 1;
  }
  .eip-header-text h1 {
    color: #ffffff;
    font-size: 1.35rem;
    font-weight: 700;
    margin: 0;
    letter-spacing: -0.01em;
  }
  .eip-header-text p {
    color: #64849f;
    font-size: 0.78rem;
    margin: 0.2rem 0 0;
    letter-spacing: 0.02em;
  }
  .eip-header-badge {
    margin-left: auto;
    background: #1e3a5f;
    color: #CADCFC;
    font-size: 0.7rem;
    font-weight: 600;
    padding: 0.25rem 0.7rem;
    border-radius: 999px;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    white-space: nowrap;
  }

  /* ── Tabs ── */
  .stTabs [data-baseweb="tab-list"] {
    gap: 0;
    background: transparent;
    border-bottom: 1px solid #1e3a5f;
    margin-bottom: 1.4rem;
  }
  .stTabs [data-baseweb="tab"] {
    background: transparent;
    border: none;
    color: #64849f;
    font-size: 0.82rem;
    font-weight: 500;
    padding: 0.55rem 1.2rem;
    border-bottom: 2px solid transparent;
    margin-bottom: -1px;
    letter-spacing: 0.03em;
  }
  .stTabs [aria-selected="true"] {
    background: transparent !important;
    color: #CADCFC !important;
    border-bottom: 2px solid #3B82F6 !important;
    font-weight: 600;
  }
  .stTabs [data-baseweb="tab"]:hover {
    color: #CADCFC !important;
    background: transparent !important;
  }

  /* ── Inputs ── */
  .stTextInput > div > div > input {
    background: #0f1e33 !important;
    border: 1px solid #1e3a5f !important;
    border-radius: 8px !important;
    color: #e2e8f0 !important;
    font-size: 0.85rem !important;
    padding: 0.55rem 0.9rem !important;
  }
  .stTextInput > div > div > input:focus {
    border-color: #3B82F6 !important;
    box-shadow: 0 0 0 2px rgba(59,130,246,0.15) !important;
  }
  .stTextInput label {
    color: #64849f !important;
    font-size: 0.75rem !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.06em !important;
  }

  /* ── Text area ── */
  .stTextArea > div > div > textarea {
    background: #0f1e33 !important;
    border: 1px solid #1e3a5f !important;
    border-radius: 8px !important;
    color: #e2e8f0 !important;
    font-size: 0.83rem !important;
    font-family: 'SF Mono', 'Fira Code', monospace !important;
    line-height: 1.6 !important;
  }
  .stTextArea > div > div > textarea:focus {
    border-color: #3B82F6 !important;
    box-shadow: 0 0 0 2px rgba(59,130,246,0.15) !important;
  }

  /* ── Primary button ── */
  .stButton > button[kind="primary"] {
    background: #3B82F6 !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 8px !important;
    font-size: 0.82rem !important;
    font-weight: 600 !important;
    padding: 0.55rem 1.4rem !important;
    letter-spacing: 0.02em !important;
    transition: all 0.15s ease !important;
  }
  .stButton > button[kind="primary"]:hover {
    background: #2563eb !important;
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(59,130,246,0.35) !important;
  }

  /* ── Secondary button ── */
  .stButton > button[kind="secondary"] {
    background: transparent !important;
    color: #64849f !important;
    border: 1px solid #1e3a5f !important;
    border-radius: 8px !important;
    font-size: 0.78rem !important;
    font-weight: 500 !important;
  }
  .stButton > button[kind="secondary"]:hover {
    border-color: #3B82F6 !important;
    color: #CADCFC !important;
  }

  /* ── Radio buttons ── */
  .stRadio > div {
    gap: 0.5rem;
  }
  .stRadio label {
    color: #8A9BB0 !important;
    font-size: 0.82rem !important;
  }

  /* ── Expanders ── */
  div[data-testid="stExpander"] {
    background: #0f1e33;
    border: 1px solid #1e3a5f !important;
    border-radius: 10px !important;
    margin-bottom: 0.5rem;
  }
  div[data-testid="stExpander"] summary {
    color: #CADCFC !important;
    font-size: 0.85rem !important;
    font-weight: 600 !important;
    padding: 0.7rem 1rem !important;
  }
  div[data-testid="stExpander"] summary:hover {
    color: #ffffff !important;
  }
  div[data-testid="stExpander"] > div > div {
    padding: 0.4rem 1rem 0.8rem !important;
  }

  /* ── Sidebar ── */
  [data-testid="stSidebar"] {
    background: #080f1c !important;
    border-right: 1px solid #1e3a5f !important;
  }
  [data-testid="stSidebar"] .stMarkdown p,
  [data-testid="stSidebar"] .stMarkdown li {
    color: #64849f !important;
    font-size: 0.8rem !important;
  }
  [data-testid="stSidebar"] h3 {
    color: #CADCFC !important;
    font-size: 0.85rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.03em !important;
  }

  /* ── Metric cards ── */
  .metric-card {
    background: #0f1e33;
    border: 1px solid #1e3a5f;
    border-radius: 10px;
    padding: 1rem 1.4rem;
    text-align: center;
  }
  .metric-card .val {
    font-size: 2.2rem;
    font-weight: 700;
    color: #CADCFC;
    line-height: 1;
  }
  .metric-card .val span {
    font-size: 1rem;
    color: #64849f;
  }
  .metric-card .lbl {
    font-size: 0.68rem;
    color: #64849f;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-top: 0.35rem;
  }

  /* ── Score pills ── */
  .score-pill {
    display: inline-block;
    padding: 0.18rem 0.65rem;
    border-radius: 999px;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.04em;
    margin-right: 0.4rem;
    vertical-align: middle;
  }
  .high   { background: rgba(34,197,94,0.12); color: #4ade80; border: 1px solid rgba(34,197,94,0.25); }
  .medium { background: rgba(251,191,36,0.12); color: #fbbf24; border: 1px solid rgba(251,191,36,0.25); }
  .low    { background: rgba(239,68,68,0.12); color: #f87171; border: 1px solid rgba(239,68,68,0.25); }

  /* ── Section divider ── */
  hr {
    border: none;
    border-top: 1px solid #1e3a5f;
    margin: 1rem 0;
  }

  /* ── Selectbox ── */
  .stSelectbox > div > div {
    background: #0f1e33 !important;
    border: 1px solid #1e3a5f !important;
    border-radius: 8px !important;
    color: #e2e8f0 !important;
  }

  /* ── Info / success / warning messages ── */
  .stAlert {
    border-radius: 8px !important;
    font-size: 0.82rem !important;
  }

  /* ── Spinner ── */
  .stSpinner > div {
    border-top-color: #3B82F6 !important;
  }

  /* ── Caption / small text ── */
  .stCaption, small {
    color: #64849f !important;
    font-size: 0.75rem !important;
  }

  /* ── Section label ── */
  .section-label {
    font-size: 0.68rem;
    font-weight: 700;
    color: #3B82F6;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-bottom: 0.2rem;
  }

  /* ── Subheader override ── */
  h2 {
    color: #e2e8f0 !important;
    font-size: 1.05rem !important;
    font-weight: 600 !important;
    letter-spacing: -0.01em !important;
    margin-bottom: 1rem !important;
  }
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="eip-header">
  <div class="eip-header-icon">
    <svg width="36" height="36" viewBox="0 0 36 36" fill="none" xmlns="http://www.w3.org/2000/svg">
      <rect width="36" height="36" rx="8" fill="#1e3a5f"/>
      <rect x="7" y="22" width="5" height="7" rx="1.5" fill="#3B82F6"/>
      <rect x="15" y="16" width="5" height="13" rx="1.5" fill="#3B82F6" opacity="0.75"/>
      <rect x="23" y="10" width="5" height="19" rx="1.5" fill="#FF6B35"/>
      <path d="M9.5 21 L17.5 15 L25.5 9" stroke="#CADCFC" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" opacity="0.5"/>
    </svg>
  </div>
  <div class="eip-header-text">
    <h1>Earnings Intelligence Platform</h1>
    <p>Structured analysis &nbsp;·&nbsp; Trend tracking &nbsp;·&nbsp; Competitive intelligence</p>
  </div>
  <div class="eip-header-badge">Powered by Claude</div>
</div>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Platform")
    st.caption("Senior BizOps intelligence for strategy teams")
    st.divider()
    count = db.get_analysis_count()
    companies_sidebar = db.get_companies()
    st.markdown(f"**{count}** {'analysis' if count == 1 else 'analyses'} stored")
    if companies_sidebar:
        st.caption("· " + "  ·  ".join(companies_sidebar))
    st.divider()
    st.markdown("### Assumptions")
    st.markdown("""
- Transcript quality drives output quality
- Scores are relative — compare across quarters
- Guidance tracker needs 2+ quarters
- JSON fallback parser handles edge cases
- First-pass instrument, not analyst replacement
    """)
    st.divider()
    if st.button("Reset Database", type="secondary", use_container_width=True):
        db.reset_database()
        st.success("Database cleared.")
        st.rerun()

# ── API key check ─────────────────────────────────────────────────────────────────
if not os.getenv("ANTHROPIC_API_KEY"):
    st.error("ANTHROPIC_API_KEY not found. Add it to your .env file and restart.")
    st.stop()


# ── Render helpers ────────────────────────────────────────────────────────────────

def _render_analysis(parsed: dict, raw: str, company: str = "", quarter: str = "", row_id: int = None, compact: bool = False):
    conf = parsed.get("confidence_score", "—")
    risk = parsed.get("risk_score", "—")

    if compact:
        # Inline pill scores — safe inside expanders and narrow containers
        def _score_color(v, mode):
            if not isinstance(v, int): return "#64849f"
            if mode == "conf": return "#4ade80" if v >= 7 else ("#fbbf24" if v >= 4 else "#f87171")
            else:              return "#f87171" if v >= 7 else ("#fbbf24" if v >= 4 else "#4ade80")
        cc = _score_color(conf, "conf")
        rc = _score_color(risk, "risk")
        st.markdown(
            f'<div style="display:flex;gap:12px;margin-bottom:12px;flex-wrap:wrap">'
            f'<div style="background:#0f1e33;border:1px solid #1e3a5f;border-radius:8px;'
            f'padding:6px 16px;display:flex;align-items:center;gap:8px">'
            f'<span style="color:#64849f;font-size:0.72rem;font-weight:600;text-transform:uppercase;'
            f'letter-spacing:0.06em">Confidence</span>'
            f'<span style="color:{cc};font-size:1.1rem;font-weight:700">{conf}/10</span></div>'
            f'<div style="background:#0f1e33;border:1px solid #1e3a5f;border-radius:8px;'
            f'padding:6px 16px;display:flex;align-items:center;gap:8px">'
            f'<span style="color:#64849f;font-size:0.72rem;font-weight:600;text-transform:uppercase;'
            f'letter-spacing:0.06em">Risk</span>'
            f'<span style="color:{rc};font-size:1.1rem;font-weight:700">{risk}/10</span></div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    else:
        c1, c2, _, _ = st.columns([1, 1, 1, 3])
        with c1:
            st.markdown(
                f'<div class="metric-card">'
                f'<div class="val">{conf}<span>/10</span></div>'
                f'<div class="lbl">Confidence</div></div>',
                unsafe_allow_html=True,
            )
        with c2:
            st.markdown(
                f'<div class="metric-card">'
                f'<div class="val">{risk}<span>/10</span></div>'
                f'<div class="lbl">Risk</div></div>',
                unsafe_allow_html=True,
            )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Executive summary card ──
    summary = parsed.get("executive_summary", "")
    if summary:
        st.markdown(
            f'<div style="background:#0f1e33;border:1px solid #1e3a5f;border-left:3px solid #3B82F6;'
            f'border-radius:10px;padding:1.1rem 1.4rem;margin-bottom:1.2rem">'
            f'<div style="color:#3B82F6;font-size:0.68rem;font-weight:700;text-transform:uppercase;'
            f'letter-spacing:0.1em;margin-bottom:0.55rem">Executive Summary</div>'
            f'<p style="color:#c8d6e5;font-size:0.88rem;line-height:1.75;margin:0">{summary}</p>'
            f'</div>',
            unsafe_allow_html=True,
        )

    with st.expander("Section 1 — Revenue Growth Drivers", expanded=True):
        for item in parsed.get("growth_drivers", []):
            st.markdown(f"- {item}")

    with st.expander("Section 2 — Management Confidence Signals", expanded=True):
        for sig in parsed.get("management_confidence_signals", []):
            if isinstance(sig, dict):
                cls = "high" if sig.get("type") == "high" else "low"
                lbl = "CONFIDENT" if sig.get("type") == "high" else "HEDGED"
                st.markdown(
                    f'<span class="score-pill {cls}">{lbl}</span>'
                    f'<span style="color:#c8d6e5;font-size:0.85rem">{sig.get("signal", "")}</span>',
                    unsafe_allow_html=True,
                )
                if sig.get("quote"):
                    st.caption(f'"{sig["quote"]}"')
                st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

    with st.expander("Section 3 — Key Risks Flagged", expanded=True):
        for r in parsed.get("risks", []):
            if isinstance(r, dict):
                sev = r.get("severity", "medium")
                st.markdown(
                    f'<span class="score-pill {sev}">{sev.upper()}</span>'
                    f'<span style="color:#c8d6e5;font-size:0.85rem">{r.get("risk", "")}</span>',
                    unsafe_allow_html=True,
                )
                if r.get("quote"):
                    st.caption(f'"{r["quote"]}"')
                st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

    with st.expander("Section 4 — Forward Guidance Summary", expanded=True):
        st.markdown(
            f'<p style="color:#c8d6e5;font-size:0.85rem;line-height:1.7">'
            f'{parsed.get("guidance", "No guidance data available.")}</p>',
            unsafe_allow_html=True,
        )

    with st.expander("Section 5 — Quarter over Quarter Narrative Shift", expanded=True):
        shift = parsed.get("narrative_shift")
        if shift:
            st.markdown(
                f'<p style="color:#c8d6e5;font-size:0.85rem;line-height:1.7">{shift}</p>',
                unsafe_allow_html=True,
            )
        else:
            st.caption("No prior quarter in database. Add more quarters to populate this section.")

    with st.expander("Section 6 — Strategic Implications", expanded=True):
        for impl in parsed.get("strategic_implications", []):
            st.markdown(
                f'<div style="display:flex;gap:0.6rem;margin-bottom:0.5rem">'
                f'<span style="color:#3B82F6;font-weight:700;margin-top:1px">›</span>'
                f'<span style="color:#c8d6e5;font-size:0.85rem;line-height:1.6">{impl}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )

    with st.expander("Raw JSON", expanded=False):
        st.code(raw, language="json")

    # ── Q/Q Delta ──
    if company and quarter:
        all_rows = db.get_all_analyses(company)
        sorted_rows = sorted(all_rows, key=lambda r: r["quarter"])
        current_idx = next((i for i, r in enumerate(sorted_rows) if r["quarter"] == quarter), None)
        if current_idx is not None and current_idx > 0:
            prev = sorted_rows[current_idx - 1]
            conf_delta = (parsed.get("confidence_score") or 0) - (prev["confidence_score"] or 0)
            risk_delta  = (parsed.get("risk_score") or 0) - (prev["risk_score"] or 0)
            conf_arrow = "▲" if conf_delta > 0 else ("▼" if conf_delta < 0 else "–")
            risk_arrow  = "▲" if risk_delta > 0 else ("▼" if risk_delta < 0 else "–")
            conf_col = "#4ade80" if conf_delta > 0 else ("#f87171" if conf_delta < 0 else "#64849f")
            risk_col  = "#f87171" if risk_delta > 0 else ("#4ade80" if risk_delta < 0 else "#64849f")
            st.markdown(
                f'<div style="background:#0f1e33;border:1px solid #1e3a5f;border-radius:10px;'
                f'padding:0.9rem 1.2rem;margin-top:0.8rem">'
                f'<div style="color:#3B82F6;font-size:0.68rem;font-weight:700;text-transform:uppercase;'
                f'letter-spacing:0.1em;margin-bottom:0.6rem">vs {prev["quarter"]}</div>'
                f'<span style="color:#64849f;font-size:0.78rem">Confidence &nbsp;</span>'
                f'<span style="color:{conf_col};font-weight:700">{conf_arrow} {abs(conf_delta)} pts</span>'
                f'<span style="color:#1e3a5f"> &nbsp;|&nbsp; </span>'
                f'<span style="color:#64849f;font-size:0.78rem">Risk &nbsp;</span>'
                f'<span style="color:{risk_col};font-weight:700">{risk_arrow} {abs(risk_delta)} pts</span>'
                f'</div>',
                unsafe_allow_html=True,
            )

    # ── Analyst notes ──
    if row_id is not None:
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        existing_notes = db.load_notes(row_id)
        notes_key = f"notes_{row_id}"
        notes_input = st.text_area(
            "Analyst Notes",
            value=existing_notes,
            height=100,
            placeholder="Add your interpretation, follow-up questions, or flags here...",
            key=notes_key,
            help="Notes are saved to the database and included in exports.",
        )
        if st.button("Save Notes", key=f"save_notes_{row_id}"):
            db.save_notes(row_id, notes_input)
            st.success("Notes saved.")

    # ── Export ──
    if company or quarter:
        notes_for_export = db.load_notes(row_id) if row_id else ""
        pdf_bytes = build_analysis_pdf(parsed, company or "Company", quarter or "Quarter", notes_for_export)
        filename = f"{company}_{quarter}_brief.pdf".replace(" ", "_")
        st.download_button(
            label="⬇ Download PDF Report",
            data=pdf_bytes,
            file_name=filename,
            mime="application/pdf",
            key=f"dl_analysis_{company}_{quarter}",
        )


def _render_comparison(result: dict, company_a: str, company_b: str):
    a = result.get("company_a", {})
    b = result.get("company_b", {})

    ca, cb = st.columns(2)
    with ca:
        st.markdown(
            f'<div style="background:#0f1e33;border:1px solid #1e3a5f;border-radius:10px;padding:1rem 1.2rem;margin-bottom:1rem">'
            f'<div style="color:#CADCFC;font-weight:700;font-size:0.95rem;margin-bottom:0.4rem">{company_a}</div>'
            f'<span style="color:#64849f;font-size:0.78rem">Confidence </span>'
            f'<span style="color:#CADCFC;font-weight:600">{a.get("confidence_score","—")}/10</span>'
            f'<span style="color:#1e3a5f"> &nbsp;|&nbsp; </span>'
            f'<span style="color:#64849f;font-size:0.78rem">Risk </span>'
            f'<span style="color:#CADCFC;font-weight:600">{a.get("risk_score","—")}/10</span>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with cb:
        st.markdown(
            f'<div style="background:#0f1e33;border:1px solid #1e3a5f;border-radius:10px;padding:1rem 1.2rem;margin-bottom:1rem">'
            f'<div style="color:#CADCFC;font-weight:700;font-size:0.95rem;margin-bottom:0.4rem">{company_b}</div>'
            f'<span style="color:#64849f;font-size:0.78rem">Confidence </span>'
            f'<span style="color:#CADCFC;font-weight:600">{b.get("confidence_score","—")}/10</span>'
            f'<span style="color:#1e3a5f"> &nbsp;|&nbsp; </span>'
            f'<span style="color:#64849f;font-size:0.78rem">Risk </span>'
            f'<span style="color:#CADCFC;font-weight:600">{b.get("risk_score","—")}/10</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

    for label, key in [
        ("Revenue Growth Drivers", "growth_drivers"),
        ("Forward Guidance",       "guidance"),
        ("Strategic Implications", "strategic_implications"),
    ]:
        st.markdown(
            f'<div style="color:#3B82F6;font-size:0.7rem;font-weight:700;'
            f'text-transform:uppercase;letter-spacing:0.08em;margin:1rem 0 0.4rem">{label}</div>',
            unsafe_allow_html=True,
        )
        cl, cr = st.columns(2)
        val_a = a.get(key, [])
        val_b = b.get(key, [])
        with cl:
            if isinstance(val_a, list):
                for item in val_a:
                    st.markdown(f'<div style="color:#c8d6e5;font-size:0.83rem;margin-bottom:0.3rem">› {item}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<p style="color:#c8d6e5;font-size:0.83rem">{val_a or "—"}</p>', unsafe_allow_html=True)
        with cr:
            if isinstance(val_b, list):
                for item in val_b:
                    st.markdown(f'<div style="color:#c8d6e5;font-size:0.83rem;margin-bottom:0.3rem">› {item}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<p style="color:#c8d6e5;font-size:0.83rem">{val_b or "—"}</p>', unsafe_allow_html=True)
        st.markdown("<hr>", unsafe_allow_html=True)

    st.markdown(
        '<div style="color:#3B82F6;font-size:0.7rem;font-weight:700;text-transform:uppercase;letter-spacing:0.08em;margin:0.5rem 0 0.4rem">Key Risks</div>',
        unsafe_allow_html=True,
    )
    rl, rr = st.columns(2)
    with rl:
        for r in a.get("risks", []):
            if isinstance(r, dict):
                sev = r.get("severity", "medium")
                st.markdown(
                    f'<div style="margin-bottom:0.4rem"><span class="score-pill {sev}">{sev.upper()}</span>'
                    f'<span style="color:#c8d6e5;font-size:0.83rem">{r.get("risk","")}</span></div>',
                    unsafe_allow_html=True,
                )
    with rr:
        for r in b.get("risks", []):
            if isinstance(r, dict):
                sev = r.get("severity", "medium")
                st.markdown(
                    f'<div style="margin-bottom:0.4rem"><span class="score-pill {sev}">{sev.upper()}</span>'
                    f'<span style="color:#c8d6e5;font-size:0.83rem">{r.get("risk","")}</span></div>',
                    unsafe_allow_html=True,
                )

    st.markdown("<hr>", unsafe_allow_html=True)
    col_conv, col_div = st.columns(2)
    with col_conv:
        st.markdown('<div style="color:#3B82F6;font-size:0.7rem;font-weight:700;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:0.4rem">Converge</div>', unsafe_allow_html=True)
        for item in result.get("convergences", []):
            st.markdown(f'<div style="color:#c8d6e5;font-size:0.83rem;margin-bottom:0.3rem">› {item}</div>', unsafe_allow_html=True)
    with col_div:
        st.markdown('<div style="color:#3B82F6;font-size:0.7rem;font-weight:700;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:0.4rem">Diverge</div>', unsafe_allow_html=True)
        for item in result.get("divergences", []):
            st.markdown(f'<div style="color:#c8d6e5;font-size:0.83rem;margin-bottom:0.3rem">› {item}</div>', unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown('<div style="color:#3B82F6;font-size:0.7rem;font-weight:700;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:0.6rem">Synthesis — Strategic Implications</div>', unsafe_allow_html=True)
    for item in result.get("synthesis", []):
        st.markdown(
            f'<div style="display:flex;gap:0.6rem;margin-bottom:0.5rem">'
            f'<span style="color:#3B82F6;font-weight:700">›</span>'
            f'<span style="color:#c8d6e5;font-size:0.85rem;line-height:1.6">{item}</span></div>',
            unsafe_allow_html=True,
        )

    with st.expander("Raw JSON", expanded=False):
        st.code(json.dumps(result, indent=2), language="json")

    # ── Export ──
    label_a = f"{company_a} — {result.get('company_a', {}).get('quarter', '')}"
    label_b = f"{company_b} — {result.get('company_b', {}).get('quarter', '')}"
    pdf_bytes = build_comparison_pdf(result, label_a, label_b)
    filename = f"{company_a}_vs_{company_b}_comparison.pdf".replace(" ", "_")
    st.download_button(
        label="⬇ Download PDF Report",
        data=pdf_bytes,
        file_name=filename,
        mime="application/pdf",
        key=f"dl_compare_{company_a}_{company_b}",
    )


# ── Session state init ────────────────────────────────────────────────────────────
if "clear_counter" not in st.session_state:
    st.session_state.clear_counter = 0
if "trends_company" not in st.session_state:
    st.session_state.trends_company = None
if "clearing" not in st.session_state:
    st.session_state.clearing = False

# ════════════════════════════════════════════════════════════════════════════════
# TABS
# ════════════════════════════════════════════════════════════════════════════════
tab_analyze, tab_trends, tab_compare = st.tabs(["  Analyze  ", "  Trends  ", "  Compare  "])


# ── TAB 1: ANALYZE ───────────────────────────────────────────────────────────────
with tab_analyze:
    st.subheader("Single Transcript Analysis")

    _c = st.session_state.clear_counter  # shorthand

    col_meta1, col_meta2 = st.columns(2)
    with col_meta1:
        company = st.text_input("Company", placeholder="e.g. AppLovin", key=f"company_{_c}")
    with col_meta2:
        quarter = st.text_input("Quarter", placeholder="e.g. Q4 2024", key=f"quarter_{_c}")

    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
    input_method = st.radio("Input", ["Paste text", "Upload file"], horizontal=True,
                            label_visibility="collapsed", key=f"input_method_{_c}")
    transcript_text = ""

    if input_method == "Paste text":
        transcript_text = st.text_area(
            "Transcript",
            height=260,
            placeholder="Paste the full earnings call transcript here...",
            label_visibility="collapsed",
            key=f"transcript_paste_{_c}",
        )
        word_count_live = len(transcript_text.split()) if transcript_text.strip() else 0

        if transcript_text.strip() and word_count_live >= 500:
            tx_hash_live = db.hash_transcript(transcript_text.strip())
            if db.analysis_exists(tx_hash_live):
                st.info("This transcript is already stored — clicking Analyze will load cached results instantly, no API call needed.")
            else:
                # Only re-score when text changes — cache by word count as a cheap proxy
                quality_key = f"quality_{_c}_{word_count_live}"
                if quality_key not in st.session_state:
                    st.session_state[quality_key] = az.score_transcript_quality(transcript_text.strip())
                quality = st.session_state[quality_key]
                grade_colors = {"Good": "#4ade80", "Fair": "#fbbf24", "Poor": "#f87171", "Very Poor": "#ef4444"}
                gc = grade_colors.get(quality["grade"], "#64849f")
                st.markdown(
                    f'<div style="background:#0f1e33;border:1px solid #1e3a5f;border-radius:8px;'
                    f'padding:8px 14px;margin-top:6px;display:flex;align-items:center;gap:12px;flex-wrap:wrap">'
                    f'<span style="color:#64849f;font-size:0.75rem;font-weight:600;text-transform:uppercase;letter-spacing:0.06em">Transcript Quality</span>'
                    f'<span style="color:{gc};font-weight:700;font-size:0.9rem">{quality["grade"]} ({quality["score"]}/100)</span>'
                    f'<span style="color:#64849f;font-size:0.78rem">{quality["word_count"]:,} words</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
                for issue in quality["issues"]:
                    st.error(f"⚠ {issue}")
                for warn in quality["warnings"]:
                    st.warning(f"ℹ {warn}")
        elif transcript_text.strip() and word_count_live < 500:
            st.caption(f"{word_count_live} words — quality check runs at 500+ words")
    else:
        uploaded = st.file_uploader("Upload transcript (.txt or .pdf)", type=["txt", "pdf"],
                                    label_visibility="collapsed", key=f"uploader_{_c}")
        if uploaded:
            if uploaded.type == "application/pdf":
                try:
                    transcript_text = az.extract_text_from_pdf(uploaded)
                    st.success(f"PDF loaded — {len(transcript_text):,} characters extracted.")
                except Exception as e:
                    st.error(f"PDF extraction failed: {e}")
            else:
                transcript_text = uploaded.read().decode("utf-8", errors="ignore")
                st.success(f"File loaded — {len(transcript_text):,} characters.")
            if transcript_text.strip():
                tx_hash_live = db.hash_transcript(transcript_text.strip())
                if db.analysis_exists(tx_hash_live):
                    st.info("This transcript is already stored — clicking Analyze will load cached results instantly, no API call needed.")
                else:
                    quality = az.score_transcript_quality(transcript_text.strip())
                    grade_colors = {"Good": "#4ade80", "Fair": "#fbbf24", "Poor": "#f87171", "Very Poor": "#ef4444"}
                    gc = grade_colors.get(quality["grade"], "#64849f")
                    st.markdown(
                        f'<div style="background:#0f1e33;border:1px solid #1e3a5f;border-radius:8px;'
                        f'padding:8px 14px;margin-top:6px;display:flex;align-items:center;gap:12px;flex-wrap:wrap">'
                        f'<span style="color:#64849f;font-size:0.75rem;font-weight:600;text-transform:uppercase;letter-spacing:0.06em">Transcript Quality</span>'
                        f'<span style="color:{gc};font-weight:700;font-size:0.9rem">{quality["grade"]} ({quality["score"]}/100)</span>'
                        f'<span style="color:#64849f;font-size:0.78rem">{quality["word_count"]:,} words</span>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                    for issue in quality["issues"]:
                        st.error(f"⚠ {issue}")
                    for warn in quality["warnings"]:
                        st.warning(f"ℹ {warn}")

    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

    btn_col1, btn_col2 = st.columns([2, 1])
    with btn_col1:
        analyze_clicked = st.button("Analyze Transcript", type="primary")
    with btn_col2:
        if st.button("Clear", type="secondary"):
            st.session_state.clear_counter += 1
            # Clear only analyze-related keys, preserve trends selection
            for key in list(st.session_state.keys()):
                if key.startswith(("company_", "quarter_", "transcript_paste_",
                                   "input_method_", "uploader_")):
                    del st.session_state[key]
            st.rerun()

    if analyze_clicked:
        if not company.strip():
            st.warning("Enter a company name.")
        elif not quarter.strip():
            st.warning("Enter a quarter label.")
        elif not transcript_text.strip():
            st.warning("Provide a transcript.")
        elif len(transcript_text.split()) < 200:
            st.error(f"⚠ Transcript too short ({len(transcript_text.split())} words) — paste the full earnings call transcript before analyzing.")
        else:
            # Check quality cache for hard blocks
            word_count_check = len(transcript_text.split())
            quality_key = f"quality_{_c}_{word_count_check}"
            quality_check = st.session_state.get(quality_key)
            if quality_check and quality_check.get("grade") == "Very Poor" and quality_check.get("issues"):
                st.error("Analysis blocked — transcript has critical quality issues listed above. Paste a complete earnings call transcript and try again.")
            else:
                tx_hash = db.hash_transcript(transcript_text.strip())
                if db.analysis_exists(tx_hash):
                    st.info("Already stored — showing cached results.")
                    rows = db.get_all_analyses(company.strip())
                    matched = next((r for r in rows if r["transcript_hash"] == tx_hash), None)
                    if matched:
                        parsed = {
                            "confidence_score": matched["confidence_score"],
                            "risk_score": matched["risk_score"],
                            "growth_drivers": json.loads(matched["growth_drivers"] or "[]"),
                            "management_confidence_signals": json.loads(matched["management_confidence"] or "[]"),
                            "risks": json.loads(matched["risks"] or "[]"),
                            "guidance": matched["guidance"],
                            "narrative_shift": matched["narrative_shift"],
                            "strategic_implications": json.loads(matched["strategic_implications"] or "[]"),
                        }
                        _render_analysis(parsed, matched["full_output"], company.strip(), quarter.strip(), row_id=matched["id"])
                else:
                    with st.spinner("Analyzing — 20 to 40 seconds..."):
                        try:
                            parsed, raw = az.run_analysis(
                                transcript=transcript_text.strip(),
                                company=company.strip(),
                                quarter=quarter.strip(),
                            )
                            st.success("Analysis complete and saved.")
                            saved_row = db.get_analysis_by_company_quarter(company.strip(), quarter.strip())
                            row_id_fresh = saved_row["id"] if saved_row else None
                            _render_analysis(parsed, raw, company.strip(), quarter.strip(), row_id=row_id_fresh)
                        except Exception as e:
                            st.error(f"Analysis failed: {e}")

    # ── Stored analyses browser — always visible, no re-run needed ──
    stored_all = db.get_all_analyses()
    if stored_all:
        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown(
            '<div style="color:#CADCFC;font-weight:600;font-size:0.9rem;margin-bottom:0.8rem">'
            'Stored Analyses & Notes</div>',
            unsafe_allow_html=True,
        )

        # Group by company for cleaner navigation
        companies_stored = sorted(set(r["company"] for r in stored_all))
        selected_browse = st.selectbox(
            "Browse by company",
            companies_stored,
            key="browse_company",
            label_visibility="visible",
        )

        company_rows = [r for r in stored_all if r["company"] == selected_browse]
        company_rows = sorted(company_rows, key=lambda r: r["quarter"])

        for row in company_rows:
            conf = row["confidence_score"]
            risk  = row["risk_score"]
            existing_notes = db.load_notes(row["id"])
            notes_indicator = " · 📝" if existing_notes.strip() else ""

            with st.expander(
                f"{row['quarter']}  ·  Confidence {conf}/10  ·  Risk {risk}/10{notes_indicator}",
                expanded=False,
            ):
                # Summary preview
                st.markdown(
                    f'<div style="color:#64849f;font-size:0.72rem;font-weight:700;'
                    f'text-transform:uppercase;letter-spacing:0.08em;margin-bottom:0.3rem">'
                    f'Executive Summary</div>',
                    unsafe_allow_html=True,
                )
                # Try to extract executive summary from full_output JSON
                try:
                    import json as _json
                    full = _json.loads(row["full_output"])
                    exec_sum = full.get("executive_summary", "")
                except Exception:
                    exec_sum = ""
                if exec_sum:
                    st.markdown(
                        f'<p style="color:#c8d6e5;font-size:0.83rem;line-height:1.6;'
                        f'margin-bottom:0.8rem">{exec_sum}</p>',
                        unsafe_allow_html=True,
                    )
                else:
                    st.caption(row.get("guidance", "")[:200] if row.get("guidance") else "No summary available.")

                # Notes field — always editable, always saved
                st.markdown(
                    '<div style="color:#64849f;font-size:0.72rem;font-weight:700;'
                    'text-transform:uppercase;letter-spacing:0.08em;margin-bottom:0.3rem">'
                    'Analyst Notes</div>',
                    unsafe_allow_html=True,
                )
                notes_val = st.text_area(
                    "Notes",
                    value=existing_notes,
                    height=90,
                    placeholder="Add your interpretation, flags, or follow-up questions here...",
                    key=f"browse_notes_{row['id']}",
                    label_visibility="collapsed",
                )

                btn_a, btn_b, btn_c = st.columns([1, 1, 3])
                with btn_a:
                    if st.button("Save Notes", key=f"browse_save_{row['id']}", type="primary"):
                        db.save_notes(row["id"], notes_val)
                        st.success("Saved.")
                        st.rerun()
                with btn_b:
                    if st.button("Load Full Analysis", key=f"browse_load_{row['id']}"):
                        parsed_browse = {
                            "confidence_score": row["confidence_score"],
                            "risk_score": row["risk_score"],
                            "growth_drivers": json.loads(row["growth_drivers"] or "[]"),
                            "management_confidence_signals": json.loads(row["management_confidence"] or "[]"),
                            "risks": json.loads(row["risks"] or "[]"),
                            "guidance": row["guidance"],
                            "narrative_shift": row["narrative_shift"],
                            "strategic_implications": json.loads(row["strategic_implications"] or "[]"),
                            "executive_summary": exec_sum,
                        }
                        _render_analysis(
                            parsed_browse, row["full_output"],
                            row["company"], row["quarter"], row_id=row["id"],
                            compact=True,
                        )


# ── TAB 2: TRENDS ────────────────────────────────────────────────────────────────
with tab_trends:
    companies = db.get_companies()
    if not companies:
        st.subheader("Multi-Quarter Trend Dashboard")
        st.info("No analyses stored yet. Run at least one analysis in the Analyze tab first.")
    else:
        # Preserve selection — only reset if stored value no longer exists
        if st.session_state.trends_company not in companies:
            st.session_state.trends_company = companies[0]

        selected_company = st.selectbox(
            "Company",
            companies,
            index=companies.index(st.session_state.trends_company),
            key="trends_selectbox",
            label_visibility="collapsed",
        )
        # Update immediately when user changes selection
        if selected_company != st.session_state.trends_company:
            st.session_state.trends_company = selected_company

        st.subheader(f"{selected_company} — Trend Dashboard")

        trend_data = db.get_trend_data(selected_company)

        # Optional overlay company for confidence chart
        overlay_options = ["None"] + [c for c in companies if c != selected_company]
        overlay_company = st.selectbox(
            "Overlay company on confidence chart",
            overlay_options,
            key="overlay_selectbox",
            label_visibility="visible",
        )
        overlay_data = db.get_trend_data(overlay_company) if overlay_company != "None" else None

        if not trend_data:
            st.warning("No data found for this company.")
        else:
            st.caption(f"{len(trend_data)} quarter(s) · {selected_company}")

            # Trends export
            trends_pdf = build_trends_pdf(selected_company, trend_data)
            st.download_button(
                label="⬇ Download Trend Report (PDF)",
                data=trends_pdf,
                file_name=f"{selected_company}_trend_report.pdf".replace(" ", "_"),
                mime="application/pdf",
                key=f"dl_trends_{selected_company}",
            )
            fig_conf, fig_heat, fig_guid, fig_theme = build_trend_dashboard(
                trend_data, selected_company, overlay_data, overlay_company if overlay_company != "None" else None
            )

            col_a, col_b = st.columns(2)
            with col_a:
                st.plotly_chart(fig_conf, use_container_width=True)
                st.plotly_chart(fig_guid, use_container_width=True)
            with col_b:
                st.plotly_chart(fig_heat, use_container_width=True)
                st.plotly_chart(fig_theme, use_container_width=True)

            # ── Heatmap detail panel — manual selectors, full width ──────────────
            st.markdown("<hr>", unsafe_allow_html=True)
            st.markdown(
                '<div style="color:#CADCFC;font-weight:600;font-size:0.9rem;margin-bottom:0.6rem">'
                'Risk Category Detail</div>',
                unsafe_allow_html=True,
            )
            available_quarters = [r["quarter"] for r in sorted(trend_data, key=lambda x: x["quarter"])]
            RISK_CATS = ["macro", "competitive", "regulatory", "operational", "guidance", "product"]

            det_col1, det_col2 = st.columns([1, 1])
            with det_col1:
                sel_quarter = st.selectbox(
                    "Quarter", available_quarters,
                    key=f"detail_quarter_{selected_company}",
                    label_visibility="visible",
                )
            with det_col2:
                sel_category = st.selectbox(
                    "Risk Category", RISK_CATS,
                    key=f"detail_category_{selected_company}",
                    label_visibility="visible",
                )

            if sel_quarter and sel_category:
                risk_items = get_risk_detail(trend_data, sel_quarter, sel_category)
                count_label = f"{len(risk_items)} risk{'s' if len(risk_items) != 1 else ''}" if risk_items else "none recorded"
                st.markdown(
                    f'<div style="color:#3B82F6;font-size:0.7rem;font-weight:700;'
                    f'text-transform:uppercase;letter-spacing:0.08em;margin-bottom:0.5rem">'
                    f'{sel_category.upper()} · {sel_quarter} · {count_label}</div>',
                    unsafe_allow_html=True,
                )
                if risk_items:
                    for item in risk_items:
                        sev      = item.get("severity", "medium")
                        sev_col  = {"high": "#f87171", "medium": "#fbbf24", "low": "#4ade80"}.get(sev, "#64849f")
                        full_risk = item.get("risk", "")
                        quote     = item.get("quote", "")
                        short     = full_risk[:65] + "…" if len(full_risk) > 65 else full_risk

                        with st.expander(f"[{sev.upper()}]  {short}", expanded=False):
                            st.markdown(
                                f'<span style="background:rgba(220,38,38,0.12);color:{sev_col};'
                                f'font-size:0.7rem;font-weight:700;padding:2px 9px;'
                                f'border-radius:999px;margin-right:8px">{sev.upper()}</span>',
                                unsafe_allow_html=True,
                            )
                            st.markdown(
                                f'<p style="color:#c8d6e5;font-size:0.86rem;line-height:1.7;margin-top:8px">'
                                f'{full_risk}</p>',
                                unsafe_allow_html=True,
                            )
                            if quote:
                                st.markdown(
                                    f'<p style="color:#64849f;font-size:0.8rem;font-style:italic;'
                                    f'border-left:2px solid #1e3a5f;padding-left:10px;margin-top:4px">'
                                    f'"{quote}"</p>',
                                    unsafe_allow_html=True,
                                )
                else:
                    st.caption(f"No {sel_category} risks recorded for {sel_quarter}.")

            st.markdown("<hr>", unsafe_allow_html=True)
            st.markdown('<div style="color:#CADCFC;font-weight:600;font-size:0.9rem;margin-bottom:0.6rem">Stored Analyses</div>', unsafe_allow_html=True)
            for row in db.get_all_analyses(selected_company):
                with st.expander(
                    f"{row['company']} — {row['quarter']}  ·  "
                    f"Confidence {row['confidence_score']}/10  ·  Risk {row['risk_score']}/10"
                ):
                    st.caption(f"Stored: {row['created_at']}")
                    st.markdown(f'<p style="color:#c8d6e5;font-size:0.83rem">{row["guidance"]}</p>', unsafe_allow_html=True)
                    existing = db.load_notes(row["id"])
                    notes_val = st.text_area(
                        "Analyst Notes",
                        value=existing,
                        height=80,
                        placeholder="Add your notes here...",
                        key=f"trends_notes_{row['id']}",
                        label_visibility="visible",
                    )
                    col_save, col_del = st.columns([1, 1])
                    with col_save:
                        if st.button("Save Notes", key=f"trends_save_{row['id']}"):
                            db.save_notes(row["id"], notes_val)
                            st.success("Saved.")
                    with col_del:
                        if st.button("Delete Analysis", key=f"del_{row['id']}", type="secondary"):
                            db.delete_analysis(row["id"])
                            st.rerun()

            # ── Risk Emergence Detector ──────────────────────────────────────────
            if len(trend_data) >= 2:
                st.markdown("<hr>", unsafe_allow_html=True)
                st.markdown(
                    '<div style="color:#CADCFC;font-weight:600;font-size:0.9rem;margin-bottom:0.6rem">'
                    'Risk Emergence Detector</div>',
                    unsafe_allow_html=True,
                )

                from visualizations import _categorize_risk
                sorted_td = sorted(trend_data, key=lambda r: r["quarter"])
                any_emergence = False

                for i in range(1, len(sorted_td)):
                    prev_q = sorted_td[i - 1]
                    curr_q = sorted_td[i]

                    prev_cats = set(
                        _categorize_risk(r.get("risk","") if isinstance(r,dict) else str(r))
                        for r in prev_q.get("risks", [])
                    )
                    curr_cats = set(
                        _categorize_risk(r.get("risk","") if isinstance(r,dict) else str(r))
                        for r in curr_q.get("risks", [])
                    )

                    new_cats     = curr_cats - prev_cats
                    dropped_cats = prev_cats - curr_cats

                    # Score delta flags
                    conf_delta = (curr_q.get("confidence_score") or 0) - (prev_q.get("confidence_score") or 0)
                    risk_delta  = (curr_q.get("risk_score") or 0)      - (prev_q.get("risk_score") or 0)

                    has_event = new_cats or dropped_cats or abs(conf_delta) >= 2 or abs(risk_delta) >= 2

                    if has_event:
                        any_emergence = True

                        # Count events for expander label
                        event_count = len(new_cats) + len(dropped_cats)
                        if abs(conf_delta) >= 2: event_count += 1
                        if abs(risk_delta) >= 2:  event_count += 1

                        with st.expander(
                            f"{prev_q['quarter']} → {curr_q['quarter']}  ·  {event_count} signal{'s' if event_count != 1 else ''}",
                            expanded=True,
                        ):
                            # New risk categories — full text + quote expandable
                            for cat in sorted(new_cats):
                                matching_items = [
                                    r for r in curr_q.get("risks", [])
                                    if isinstance(r, dict) and _categorize_risk(r.get("risk", "")) == cat
                                ]
                                if matching_items:
                                    for risk_item in matching_items:
                                        full_text = risk_item.get("risk", "")
                                        quote     = risk_item.get("quote", "")
                                        sev       = risk_item.get("severity", "medium")
                                        sev_col   = {"high": "#f87171", "medium": "#fbbf24", "low": "#4ade80"}.get(sev, "#fbbf24")
                                        with st.expander(
                                            f"🆕  {cat.upper()} — {full_text[:60]}{'…' if len(full_text) > 60 else ''}",
                                            expanded=False,
                                        ):
                                            st.markdown(
                                                f'<span style="background:rgba(251,191,36,0.1);color:{sev_col};'
                                                f'font-size:0.7rem;font-weight:700;padding:2px 8px;'
                                                f'border-radius:999px;margin-right:8px">{sev.upper()}</span>'
                                                f'<span style="color:#CADCFC;font-size:0.85rem;font-weight:600">'
                                                f'New in {curr_q["quarter"]}</span>',
                                                unsafe_allow_html=True,
                                            )
                                            st.markdown(
                                                f'<p style="color:#c8d6e5;font-size:0.85rem;line-height:1.65;margin-top:6px">{full_text}</p>',
                                                unsafe_allow_html=True,
                                            )
                                            if quote:
                                                st.markdown(
                                                    f'<p style="color:#64849f;font-size:0.8rem;font-style:italic;'
                                                    f'border-left:2px solid #1e3a5f;padding-left:10px;margin-top:4px">'
                                                    f'"{quote}"</p>',
                                                    unsafe_allow_html=True,
                                                )
                                else:
                                    st.markdown(
                                        f'<div style="color:#fbbf24;font-size:0.83rem;padding:4px 0">'
                                        f'🆕 <b>{cat.upper()}</b> risk category appeared</div>',
                                        unsafe_allow_html=True,
                                    )

                            # Resolved risk categories
                            for cat in sorted(dropped_cats):
                                st.markdown(
                                    f'<div style="color:#4ade80;font-size:0.83rem;padding:4px 0">'
                                    f'✓ <b>{cat.upper()}</b> risk resolved / no longer flagged in {curr_q["quarter"]}</div>',
                                    unsafe_allow_html=True,
                                )

                            # Score shifts
                            if abs(conf_delta) >= 2:
                                arrow = "▲" if conf_delta > 0 else "▼"
                                col   = "#4ade80" if conf_delta > 0 else "#f87171"
                                st.markdown(
                                    f'<div style="color:{col};font-size:0.83rem;padding:4px 0">'
                                    f'{arrow} Confidence {conf_delta:+d} pts — '
                                    f'{prev_q.get("confidence_score")}/10 → {curr_q.get("confidence_score")}/10</div>',
                                    unsafe_allow_html=True,
                                )
                            if abs(risk_delta) >= 2:
                                arrow = "▲" if risk_delta > 0 else "▼"
                                col   = "#f87171" if risk_delta > 0 else "#4ade80"
                                st.markdown(
                                    f'<div style="color:{col};font-size:0.83rem;padding:4px 0">'
                                    f'{arrow} Risk score {risk_delta:+d} pts — '
                                    f'{prev_q.get("risk_score")}/10 → {curr_q.get("risk_score")}/10</div>',
                                    unsafe_allow_html=True,
                                )

                if not any_emergence:
                    st.caption("No significant risk emergence or score shifts detected across quarters.")

            # ── Multi-Quarter Summary Brief ──────────────────────────────────────
            if len(trend_data) >= 2:
                st.markdown("<hr>", unsafe_allow_html=True)
                st.markdown(
                    '<div style="color:#CADCFC;font-weight:600;font-size:0.9rem;margin-bottom:0.4rem">'
                    'AI Trend Summary</div>',
                    unsafe_allow_html=True,
                )
                st.caption("One paragraph synthesizing the full trend history — generated on demand, no new API call if cached.")

                summary_key = f"trend_summary_{selected_company}"
                if summary_key not in st.session_state:
                    st.session_state[summary_key] = None

                if st.button("Generate Trend Summary", key=f"gen_summary_{selected_company}"):
                    with st.spinner("Synthesizing trend history — 10 to 20 seconds..."):
                        try:
                            summary_text = az.generate_trend_summary(selected_company, trend_data)
                            st.session_state[summary_key] = summary_text
                        except Exception as e:
                            st.error(f"Failed: {e}")

                if st.session_state.get(summary_key):
                    st.markdown(
                        f'<div style="background:#0f1e33;border:1px solid #1e3a5f;'
                        f'border-left:3px solid #3B82F6;border-radius:10px;'
                        f'padding:1rem 1.4rem;margin-top:0.5rem">'
                        f'<p style="color:#c8d6e5;font-size:0.88rem;line-height:1.75;margin:0">'
                        f'{st.session_state[summary_key]}</p></div>',
                        unsafe_allow_html=True,
                    )


# ── TAB 3: COMPARE ───────────────────────────────────────────────────────────────
with tab_compare:
    st.subheader("Side-by-Side Comparison")
    st.caption("Compare any two quarters or companies — stored analyses or fresh transcripts")

    all_stored = db.get_all_analyses()
    stored_options = {
        f"{r['company']} — {r['quarter']}": r for r in all_stored
    }
    stored_labels = list(stored_options.keys())
    has_stored = len(stored_labels) > 0

    def _side_input(label, side_key, stored_labels, stored_options, has_stored):
        """Render one side of the comparison — stored or fresh input."""
        st.markdown(f'<div class="section-label">{label}</div>', unsafe_allow_html=True)

        source = st.radio(
            f"Source {side_key}",
            ["Use stored analysis", "Paste new transcript"] if has_stored else ["Paste new transcript"],
            horizontal=True,
            key=f"{side_key}_source",
            label_visibility="collapsed",
        )

        if source == "Use stored analysis" and has_stored:
            selected = st.selectbox(
                f"Select {label}",
                stored_labels,
                key=f"{side_key}_select",
                label_visibility="collapsed",
            )
            row = stored_options[selected]
            st.markdown(
                f'<div style="background:#0f1e33;border:1px solid #1e3a5f;border-radius:8px;'
                f'padding:0.7rem 1rem;margin-top:0.3rem">'
                f'<span style="color:#64849f;font-size:0.75rem">Confidence </span>'
                f'<span style="color:#CADCFC;font-weight:600">{row["confidence_score"]}/10</span>'
                f'<span style="color:#1e3a5f"> &nbsp;·&nbsp; </span>'
                f'<span style="color:#64849f;font-size:0.75rem">Risk </span>'
                f'<span style="color:#CADCFC;font-weight:600">{row["risk_score"]}/10</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
            return "stored", row

        else:
            company = st.text_input(f"Company {side_key}", placeholder="e.g. AppLovin",
                                    key=f"{side_key}_company", label_visibility="collapsed")
            quarter = st.text_input(f"Quarter {side_key}", placeholder="e.g. Q4 2024",
                                    key=f"{side_key}_quarter", label_visibility="collapsed")
            input_type = st.radio(f"Input {side_key}", ["Paste", "Upload"],
                                  horizontal=True, key=f"{side_key}_input",
                                  label_visibility="collapsed")
            tx = ""
            if input_type == "Paste":
                tx = st.text_area("Transcript", height=200,
                                  label_visibility="collapsed", key=f"{side_key}_tx")
            else:
                f = st.file_uploader("Upload", type=["txt", "pdf"],
                                     key=f"{side_key}_file", label_visibility="collapsed")
                if f:
                    tx = (
                        az.extract_text_from_pdf(f)
                        if f.type == "application/pdf"
                        else f.read().decode("utf-8", errors="ignore")
                    )
                    st.success(f"{len(tx):,} chars loaded.")
            return "fresh", {"company": company, "quarter": quarter, "transcript": tx}

    col_l, col_r = st.columns(2)
    with col_l:
        type_a, data_a = _side_input("Side A", "ca", stored_labels, stored_options, has_stored)
    with col_r:
        type_b, data_b = _side_input("Side B", "cb", stored_labels, stored_options, has_stored)

    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

    if st.button("Run Comparison", type="primary"):
        # Validate
        missing = []
        if type_a == "fresh":
            if not data_a.get("company", "").strip(): missing.append("Company A name")
            if not data_a.get("quarter", "").strip():  missing.append("Quarter A")
            if not data_a.get("transcript", "").strip(): missing.append("Transcript A")
        if type_b == "fresh":
            if not data_b.get("company", "").strip(): missing.append("Company B name")
            if not data_b.get("quarter", "").strip():  missing.append("Quarter B")
            if not data_b.get("transcript", "").strip(): missing.append("Transcript B")

        if missing:
            st.warning("Missing: " + ", ".join(missing))
        else:
            # Build human-readable labels for cache keying
            label_a = (
                f"{data_a['company']} — {data_a['quarter']}"
                if type_a == "stored"
                else f"{data_a.get('company','').strip()} — {data_a.get('quarter','').strip()}"
            )
            label_b = (
                f"{data_b['company']} — {data_b['quarter']}"
                if type_b == "stored"
                else f"{data_b.get('company','').strip()} — {data_b.get('quarter','').strip()}"
            )

            # Check cache first — regardless of mode
            cached = db.load_comparison(label_a, label_b)
            if cached:
                st.info("Loaded from cache — no API call needed.")
                name_a = data_a.get("company", label_a) if type_a == "stored" else data_a.get("company", "").strip()
                name_b = data_b.get("company", label_b) if type_b == "stored" else data_b.get("company", "").strip()
                _render_comparison(cached, name_a, name_b)

            # Both stored
            elif type_a == "stored" and type_b == "stored":
                with st.spinner("Generating comparison — 15 to 30 seconds..."):
                    try:
                        result = az.run_comparison_from_stored(data_a, data_b)
                        db.save_comparison(label_a, label_b, result)
                        _render_comparison(result, data_a["company"], data_b["company"])
                    except Exception as e:
                        st.error(f"Comparison failed: {e}")

            # Both fresh
            elif type_a == "fresh" and type_b == "fresh":
                with st.spinner("Running comparison — 30 to 60 seconds..."):
                    try:
                        result = az.run_comparison(
                            transcript_a=data_a["transcript"].strip(),
                            company_a=data_a["company"].strip(),
                            quarter_a=data_a["quarter"].strip(),
                            transcript_b=data_b["transcript"].strip(),
                            company_b=data_b["company"].strip(),
                            quarter_b=data_b["quarter"].strip(),
                        )
                        db.save_comparison(label_a, label_b, result)
                        _render_comparison(result, data_a["company"].strip(), data_b["company"].strip())
                    except Exception as e:
                        st.error(f"Comparison failed: {e}")

            # Mixed — analyze fresh side first, then compare from stored
            else:
                with st.spinner("Analyzing fresh transcript then comparing — 30 to 50 seconds..."):
                    try:
                        if type_a == "fresh":
                            fresh_parsed, _ = az.run_analysis(
                                transcript=data_a["transcript"].strip(),
                                company=data_a["company"].strip(),
                                quarter=data_a["quarter"].strip(),
                            )
                            fresh_row = {
                                "company": data_a["company"].strip(),
                                "quarter": data_a["quarter"].strip(),
                                "confidence_score": fresh_parsed.get("confidence_score", 5),
                                "risk_score": fresh_parsed.get("risk_score", 5),
                                "growth_drivers": az._json_dumps(fresh_parsed.get("growth_drivers", [])),
                                "management_confidence": az._json_dumps(fresh_parsed.get("management_confidence_signals", [])),
                                "risks": az._json_dumps(fresh_parsed.get("risks", [])),
                                "guidance": fresh_parsed.get("guidance", ""),
                                "narrative_shift": fresh_parsed.get("narrative_shift"),
                                "strategic_implications": az._json_dumps(fresh_parsed.get("strategic_implications", [])),
                            }
                            result = az.run_comparison_from_stored(fresh_row, data_b)
                            db.save_comparison(label_a, label_b, result)
                            _render_comparison(result, data_a["company"].strip(), data_b["company"])
                        else:
                            fresh_parsed, _ = az.run_analysis(
                                transcript=data_b["transcript"].strip(),
                                company=data_b["company"].strip(),
                                quarter=data_b["quarter"].strip(),
                            )
                            fresh_row = {
                                "company": data_b["company"].strip(),
                                "quarter": data_b["quarter"].strip(),
                                "confidence_score": fresh_parsed.get("confidence_score", 5),
                                "risk_score": fresh_parsed.get("risk_score", 5),
                                "growth_drivers": az._json_dumps(fresh_parsed.get("growth_drivers", [])),
                                "management_confidence": az._json_dumps(fresh_parsed.get("management_confidence_signals", [])),
                                "risks": az._json_dumps(fresh_parsed.get("risks", [])),
                                "guidance": fresh_parsed.get("guidance", ""),
                                "narrative_shift": fresh_parsed.get("narrative_shift"),
                                "strategic_implications": az._json_dumps(fresh_parsed.get("strategic_implications", [])),
                            }
                            result = az.run_comparison_from_stored(data_a, fresh_row)
                            db.save_comparison(label_a, label_b, result)
                            _render_comparison(result, data_a["company"], data_b["company"].strip())
                    except Exception as e:
                        st.error(f"Comparison failed: {e}")

    # ── Comparison History ───────────────────────────────────────────────────────
    past_comparisons = db.get_all_comparisons()
    if past_comparisons:
        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown(
            f'<div style="color:#CADCFC;font-weight:600;font-size:0.9rem;margin-bottom:0.6rem">'
            f'Comparison History  <span style="color:#64849f;font-weight:400;font-size:0.8rem">'
            f'({len(past_comparisons)} stored)</span></div>',
            unsafe_allow_html=True,
        )
        for comp in past_comparisons:
            created = comp["created_at"][:16].replace("T", " ")
            with st.expander(
                f"{comp['label_a']}  vs  {comp['label_b']}  ·  {created}",
                expanded=False,
            ):
                result_preview = db.load_comparison(comp["label_a"], comp["label_b"])
                if result_preview:
                    a = result_preview.get("company_a", {})
                    b = result_preview.get("company_b", {})
                    st.markdown(
                        f'<div style="display:flex;gap:24px;margin-bottom:8px">'
                        f'<span style="color:#64849f;font-size:0.78rem">'
                        f'{a.get("name","")} · Conf {a.get("confidence_score","—")}/10 · Risk {a.get("risk_score","—")}/10</span>'
                        f'<span style="color:#1e3a5f">|</span>'
                        f'<span style="color:#64849f;font-size:0.78rem">'
                        f'{b.get("name","")} · Conf {b.get("confidence_score","—")}/10 · Risk {b.get("risk_score","—")}/10</span>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                col_load, col_del = st.columns([2, 1])
                with col_load:
                    if st.button("Load Comparison", key=f"load_comp_{comp['id']}", type="primary"):
                        if result_preview:
                            name_a = result_preview.get("company_a", {}).get("name", comp["label_a"])
                            name_b = result_preview.get("company_b", {}).get("name", comp["label_b"])
                            _render_comparison(result_preview, name_a, name_b)
                        else:
                            st.error("Could not load cached comparison.")
                with col_del:
                    if st.button("Delete", key=f"del_comp_{comp['id']}", type="secondary"):
                        db.delete_comparison(comp["id"])
                        st.rerun()
