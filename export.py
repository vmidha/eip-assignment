"""
export.py
Clean PDF report generation using reportlab.
Professional layout with proper typography, spacing, and color.
"""

import io
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether, PageBreak,
)
from reportlab.lib.colors import HexColor

# ── Colors ────────────────────────────────────────────────────────────────────
NAVY      = HexColor("#0A1628")
NAVY2     = HexColor("#112240")
BLUE      = HexColor("#3B82F6")
ORANGE    = HexColor("#FF6B35")
SLATE     = HexColor("#64849f")
ICE       = HexColor("#CADCFC")
TEXT      = HexColor("#1e293b")
TEXT_MID  = HexColor("#475569")
TEXT_DIM  = HexColor("#94a3b8")
CARD      = HexColor("#f8fafc")
CARD2     = HexColor("#f1f5f9")
BORDER    = HexColor("#e2e8f0")
GREEN     = HexColor("#16a34a")
GREEN_BG  = HexColor("#f0fdf4")
RED       = HexColor("#dc2626")
RED_BG    = HexColor("#fef2f2")
AMBER     = HexColor("#d97706")
AMBER_BG  = HexColor("#fffbeb")
BLUE_BG   = HexColor("#eff6ff")
WHITE     = colors.white

W = 6.7 * inch   # usable width at 0.9in margins each side


# ── Style factory ─────────────────────────────────────────────────────────────

def _s(name, font="Helvetica", size=9, color=TEXT, leading=None,
       align=TA_LEFT, space_before=0, space_after=2, bold=False):
    return ParagraphStyle(
        name,
        fontName=f"Helvetica-Bold" if bold else font,
        fontSize=size,
        textColor=color,
        leading=leading or int(size * 1.45),
        alignment=align,
        spaceBefore=space_before,
        spaceAfter=space_after,
    )


def _styles():
    return {
        # Header
        "h_title":  _s("ht", size=15, color=WHITE, bold=True, leading=18),
        "h_sub":    _s("hs", size=8,  color=ICE,   leading=10),
        "h_badge":  _s("hb", size=7,  color=ICE,   bold=True, align=TA_RIGHT),
        # Section headers
        "sec_lbl":  _s("sl", size=7.5, color=BLUE, bold=True, space_before=10, space_after=4),
        # Body text
        "body":     _s("b",  size=8.5, color=TEXT, leading=13, space_after=3),
        "body_dim": _s("bd", size=8,   color=TEXT_MID, leading=12, space_after=2),
        "italic":   _s("it", size=7.5, color=SLATE, font="Helvetica-Oblique", leading=11, space_after=2),
        # Scores
        "sc_val":   _s("sv", size=20,  color=NAVY, bold=True, align=TA_CENTER, leading=22),
        "sc_lbl":   _s("sl2",size=7,   color=SLATE, align=TA_CENTER, leading=9),
        # Tables
        "th":       _s("th", size=7.5, color=WHITE, bold=True, align=TA_CENTER, leading=10),
        "tc":       _s("tc", size=8,   color=TEXT, leading=12),
        "tc_c":     _s("tcc",size=8,   color=TEXT, bold=True, align=TA_CENTER, leading=12),
        # Summary
        "summary":  _s("sm", size=9, color=TEXT, leading=14, space_after=0),
        # Meta
        "meta":     _s("me", size=7.5, color=TEXT_MID, leading=10),
        # Footer
        "footer":   _s("ft", size=6.5, color=TEXT_DIM, align=TA_CENTER, leading=9),
        # Company header in comparison
        "co_name":  _s("cn", size=9, color=NAVY, bold=True, leading=11),
        "co_score": _s("cs", size=7.5, color=TEXT_MID, leading=10),
    }


# ── Header block ──────────────────────────────────────────────────────────────

def _header(subtitle: str, st: dict) -> Table:
    """Full-width navy header with title, subtitle, badge."""
    title_block = [
        Paragraph("Earnings Intelligence Platform", st["h_title"]),
        Spacer(1, 2),
        Paragraph(subtitle, st["h_sub"]),
    ]
    badge = Paragraph("POWERED BY CLAUDE", st["h_badge"])

    t = Table([[title_block, badge]],
              colWidths=[W * 0.78, W * 0.22])
    t.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, -1), NAVY),
        ("TOPPADDING",   (0, 0), (-1, -1), 14),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 14),
        ("LEFTPADDING",  (0, 0), (-1, -1), 16),
        ("RIGHTPADDING", (-1,0), (-1, -1), 14),
        ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN",        (1, 0), (1,  0),  "RIGHT"),
    ]))
    return t


# ── Divider + section label ───────────────────────────────────────────────────

def _section(label: str, st: dict) -> list:
    return [
        Spacer(1, 6),
        HRFlowable(width="100%", thickness=0.4, color=BORDER, spaceAfter=4),
        Paragraph(label.upper(), st["sec_lbl"]),
    ]


# ── Score cards ───────────────────────────────────────────────────────────────

def _score_cards(conf, risk, st: dict) -> Table:
    def _color(v, mode="conf"):
        if mode == "conf":
            return GREEN if (v or 0) >= 7 else (AMBER if (v or 0) >= 4 else RED)
        else:
            return RED if (v or 0) >= 7 else (AMBER if (v or 0) >= 4 else GREEN)

    def _card(val, lbl, col):
        return [
            Paragraph(f'<font color="#{col.hexval()[2:]}">{val}/10</font>',
                      st["sc_val"]),
            Spacer(1, 2),
            Paragraph(lbl, st["sc_lbl"]),
        ]

    t = Table(
        [[_card(conf, "Management Confidence", _color(conf, "conf")),
          _card(risk, "Risk Score", _color(risk, "risk"))]],
        colWidths=[W * 0.5, W * 0.5],
    )
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), CARD),
        ("BOX",           (0, 0), (0,  0),  0.5, BORDER),
        ("BOX",           (1, 0), (1,  0),  0.5, BORDER),
        ("TOPPADDING",    (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
    ]))
    return t


# ── Severity pill helper ──────────────────────────────────────────────────────

def _pill(sev: str) -> str:
    mapping = {
        "high":      ("#dc2626", "HIGH"),
        "medium":    ("#d97706", "MED"),
        "low":       ("#16a34a", "LOW"),
        "confident": ("#2563eb", "CONFIDENT"),
        "hedged":    ("#dc2626", "HEDGED"),
    }
    col, lbl = mapping.get(sev.lower(), ("#64849f", sev.upper()))
    return f'<font color="{col}"><b>[{lbl}]</b></font>'


# ── Meta strip ────────────────────────────────────────────────────────────────

def _meta_row(pairs: list, st: dict) -> Table:
    """Pairs = [(label, value), ...]"""
    cells = [Paragraph(f"<b>{l}:</b>  {v}", st["meta"]) for l, v in pairs]
    widths = [W / len(pairs)] * len(pairs)
    t = Table([cells], colWidths=widths)
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), CARD2),
        ("BOX",           (0, 0), (-1, -1), 0.4, BORDER),
        ("TOPPADDING",    (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
    ]))
    return t


# ── Footer ────────────────────────────────────────────────────────────────────

def _footer(st: dict) -> list:
    ts = datetime.utcnow().strftime("%B %d, %Y at %H:%M UTC")
    return [
        Spacer(1, 10),
        HRFlowable(width="100%", thickness=0.4, color=BORDER, spaceAfter=4),
        Paragraph(
            f"Earnings Intelligence Platform  ·  Generated {ts}",
            st["footer"],
        ),
    ]


# ══════════════════════════════════════════════════════════════════════════════
# ANALYSIS PDF
# ══════════════════════════════════════════════════════════════════════════════

def build_analysis_pdf(
    parsed: dict,
    company: str,
    quarter: str,
    analyst_notes: str = "",
) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=letter,
        leftMargin=0.9*inch, rightMargin=0.9*inch,
        topMargin=0.6*inch, bottomMargin=0.7*inch,
        title=f"{company} {quarter} — Intelligence Brief",
        author="Earnings Intelligence Platform",
    )
    st = _styles()
    story = []

    # Header
    story.append(_header(f"Intelligence Brief  ·  {company}  ·  {quarter}", st))
    story.append(Spacer(1, 10))

    # Meta
    ts = datetime.utcnow().strftime("%B %d, %Y")
    story.append(_meta_row([("Company", company), ("Quarter", quarter), ("Generated", ts)], st))
    story.append(Spacer(1, 10))

    # Scores
    story.append(_score_cards(parsed.get("confidence_score"), parsed.get("risk_score"), st))
    story.append(Spacer(1, 10))

    # Executive summary
    summary = parsed.get("executive_summary", "")
    if summary:
        summ_t = Table(
            [[Paragraph("EXECUTIVE SUMMARY", st["sec_lbl"])],
             [Paragraph(summary, st["summary"])]],
            colWidths=[W],
        )
        summ_t.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), BLUE_BG),
            ("LINEBEFORE",    (0, 0), (-1, -1), 3, BLUE),
            ("BOX",           (0, 0), (-1, -1), 0.4, BORDER),
            ("TOPPADDING",    (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ("LEFTPADDING",   (0, 0), (-1, -1), 12),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 12),
        ]))
        story.append(summ_t)
        story.append(Spacer(1, 4))

    # Section 1 — Growth Drivers
    story += _section("Section 1 — Revenue Growth Drivers", st)
    for item in parsed.get("growth_drivers", []):
        story.append(Paragraph(f"<font color='#3B82F6'>›</font>  {item}", st["body"]))

    # Section 2 — Confidence Signals
    story += _section("Section 2 — Management Confidence Signals", st)
    for sig in parsed.get("management_confidence_signals", []):
        if isinstance(sig, dict):
            tag = _pill("confident" if sig.get("type") == "high" else "hedged")
            story.append(Paragraph(f"{tag}  {sig.get('signal','')}", st["body"]))
            if sig.get("quote"):
                story.append(Paragraph(f'"{sig["quote"]}"', st["italic"]))

    # Section 3 — Risks
    story += _section("Section 3 — Key Risks Flagged", st)
    for r in parsed.get("risks", []):
        if isinstance(r, dict):
            tag = _pill(r.get("severity", "medium"))
            story.append(Paragraph(f"{tag}  {r.get('risk','')}", st["body"]))
            if r.get("quote"):
                story.append(Paragraph(f'"{r["quote"]}"', st["italic"]))

    # Section 4 — Guidance
    story += _section("Section 4 — Forward Guidance Summary", st)
    story.append(Paragraph(parsed.get("guidance", "No guidance available."), st["body"]))

    # Section 5 — Narrative Shift
    story += _section("Section 5 — Quarter over Quarter Narrative Shift", st)
    shift = parsed.get("narrative_shift")
    story.append(Paragraph(
        shift or "No prior quarter data available.",
        st["body"] if shift else st["italic"],
    ))

    # Section 6 — Strategic Implications
    story += _section("Section 6 — Strategic Implications", st)
    for impl in parsed.get("strategic_implications", []):
        story.append(Paragraph(f"<font color='#3B82F6'>›</font>  {impl}", st["body"]))

    # Analyst Notes
    if analyst_notes.strip():
        story += _section("Analyst Notes", st)
        notes_t = Table(
            [[Paragraph(analyst_notes, st["body"])]],
            colWidths=[W],
        )
        notes_t.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), CARD2),
            ("BOX",           (0, 0), (-1, -1), 0.4, BORDER),
            ("TOPPADDING",    (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        ]))
        story.append(notes_t)

    story += _footer(st)
    doc.build(story)
    return buf.getvalue()


# ══════════════════════════════════════════════════════════════════════════════
# COMPARISON PDF
# ══════════════════════════════════════════════════════════════════════════════

def build_comparison_pdf(result: dict, label_a: str, label_b: str) -> bytes:
    buf = io.BytesIO()
    a = result.get("company_a", {})
    b = result.get("company_b", {})
    name_a = a.get("name", label_a)
    name_b = b.get("name", label_b)
    q_a    = a.get("quarter", "")
    q_b    = b.get("quarter", "")

    doc = SimpleDocTemplate(
        buf, pagesize=letter,
        leftMargin=0.9*inch, rightMargin=0.9*inch,
        topMargin=0.6*inch, bottomMargin=0.7*inch,
        title=f"{name_a} vs {name_b} — Comparison Brief",
        author="Earnings Intelligence Platform",
    )
    st = _styles()
    story = []

    story.append(_header(f"Comparison Brief  ·  {name_a}  vs  {name_b}", st))
    story.append(Spacer(1, 10))

    # Score header table — 2 columns
    def _co_block(data, name, quarter):
        conf = data.get("confidence_score", "—")
        risk  = data.get("risk_score", "—")
        return [
            Paragraph(f"{name}", st["co_name"]),
            Paragraph(f"{quarter}", st["co_score"]),
            Spacer(1, 4),
            Paragraph(
                f'<font color="#3B82F6"><b>Confidence</b></font>  {conf}/10'
                f'   <font color="#FF6B35"><b>Risk</b></font>  {risk}/10',
                st["co_score"],
            ),
        ]

    co_t = Table(
        [[_co_block(a, name_a, q_a), _co_block(b, name_b, q_b)]],
        colWidths=[W * 0.5, W * 0.5],
    )
    co_t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), CARD),
        ("BOX",           (0, 0), (0,  0),  0.5, BORDER),
        ("BOX",           (1, 0), (1,  0),  0.5, BORDER),
        ("LINEAFTER",     (0, 0), (0, -1),  0.5, BORDER),
        ("TOPPADDING",    (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
        ("LEFTPADDING",   (0, 0), (-1, -1), 14),
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(co_t)
    story.append(Spacer(1, 6))

    # Side-by-side sections
    def _fmt_list(val):
        if isinstance(val, list):
            return "\n".join(f"›  {i}" for i in val)
        return val or "—"

    def _side_table(label, key):
        val_a = a.get(key, [])
        val_b = b.get(key, [])

        header_row = [
            Paragraph(name_a, st["th"]),
            Paragraph(name_b, st["th"]),
        ]
        def _cell(v):
            text = _fmt_list(v).replace("\n", "<br/>")
            return Paragraph(text, st["tc"])

        t = Table(
            [header_row, [_cell(val_a), _cell(val_b)]],
            colWidths=[W * 0.5, W * 0.5],
        )
        t.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, 0), NAVY),
            ("BACKGROUND",    (0, 1), (-1,-1), CARD),
            ("BOX",           (0, 0), (-1,-1), 0.4, BORDER),
            ("LINEAFTER",     (0, 0), (0, -1), 0.4, BORDER),
            ("TOPPADDING",    (0, 0), (-1,-1), 7),
            ("BOTTOMPADDING", (0, 0), (-1,-1), 7),
            ("LEFTPADDING",   (0, 0), (-1,-1), 8),
            ("VALIGN",        (0, 0), (-1,-1), "TOP"),
        ]))
        return t

    for lbl, key in [
        ("Revenue Growth Drivers", "growth_drivers"),
        ("Forward Guidance",       "guidance"),
        ("Strategic Implications", "strategic_implications"),
    ]:
        story += _section(lbl, st)
        story.append(_side_table(lbl, key))

    # Risks side by side
    story += _section("Key Risks", st)
    def _risk_cell(data):
        lines = []
        for r in data.get("risks", []):
            if isinstance(r, dict):
                tag = _pill(r.get("severity", "medium"))
                lines.append(f"{tag}  {r.get('risk','')}")
        return Paragraph("<br/>".join(lines) if lines else "—", st["tc"])

    risks_t = Table(
        [[Paragraph(name_a, st["th"]), Paragraph(name_b, st["th"])],
         [_risk_cell(a), _risk_cell(b)]],
        colWidths=[W * 0.5, W * 0.5],
    )
    risks_t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0), NAVY),
        ("BACKGROUND",    (0, 1), (-1,-1), CARD),
        ("BOX",           (0, 0), (-1,-1), 0.4, BORDER),
        ("LINEAFTER",     (0, 0), (0, -1), 0.4, BORDER),
        ("TOPPADDING",    (0, 0), (-1,-1), 7),
        ("BOTTOMPADDING", (0, 0), (-1,-1), 7),
        ("LEFTPADDING",   (0, 0), (-1,-1), 8),
        ("VALIGN",        (0, 0), (-1,-1), "TOP"),
    ]))
    story.append(risks_t)

    # Convergences & Divergences
    story += _section("Convergences & Divergences", st)
    conv = result.get("convergences", [])
    divg = result.get("divergences", [])
    n = max(len(conv), len(divg), 1)
    cd_rows = [[Paragraph("Converge", st["th"]), Paragraph("Diverge", st["th"])]]
    for i in range(n):
        c = f"›  {conv[i]}" if i < len(conv) else ""
        d = f"›  {divg[i]}"  if i < len(divg) else ""
        cd_rows.append([Paragraph(c, st["tc"]), Paragraph(d, st["tc"])])
    cd_t = Table(cd_rows, colWidths=[W * 0.5, W * 0.5])
    cd_t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0), NAVY),
        ("BACKGROUND",    (0, 1), (-1,-1), CARD),
        ("BOX",           (0, 0), (-1,-1), 0.4, BORDER),
        ("LINEAFTER",     (0, 0), (0, -1), 0.4, BORDER),
        ("LINEBELOW",     (0, 0), (-1,-2), 0.3, BORDER),
        ("TOPPADDING",    (0, 0), (-1,-1), 7),
        ("BOTTOMPADDING", (0, 0), (-1,-1), 7),
        ("LEFTPADDING",   (0, 0), (-1,-1), 8),
        ("VALIGN",        (0, 0), (-1,-1), "TOP"),
    ]))
    story.append(cd_t)

    # Synthesis
    story += _section("Synthesis — Strategic Implications", st)
    synth_t = Table(
        [[Paragraph(f"<font color='#3B82F6'>›</font>  {item}", st["body"])]
         for item in result.get("synthesis", [])],
        colWidths=[W],
    )
    synth_t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1,-1), CARD),
        ("BOX",           (0, 0), (-1,-1), 0.4, BORDER),
        ("LINEBELOW",     (0, 0), (-1,-2), 0.3, BORDER),
        ("TOPPADDING",    (0, 0), (-1,-1), 7),
        ("BOTTOMPADDING", (0, 0), (-1,-1), 7),
        ("LEFTPADDING",   (0, 0), (-1,-1), 12),
    ]))
    story.append(synth_t)

    story += _footer(st)
    doc.build(story)
    return buf.getvalue()


# ══════════════════════════════════════════════════════════════════════════════
# TRENDS PDF
# ══════════════════════════════════════════════════════════════════════════════

def build_trends_pdf(company: str, trend_data: list) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=letter,
        leftMargin=0.9*inch, rightMargin=0.9*inch,
        topMargin=0.6*inch, bottomMargin=0.7*inch,
        title=f"{company} — Trend Report",
        author="Earnings Intelligence Platform",
    )
    st = _styles()
    story = []

    story.append(_header(
        f"Trend Report  ·  {company}  ·  {len(trend_data)} Quarter(s)", st
    ))
    story.append(Spacer(1, 10))

    # Score summary table
    story += _section("Score Summary by Quarter", st)

    def _conf_color(v):
        return GREEN if (v or 0) >= 7 else (AMBER if (v or 0) >= 4 else RED)
    def _risk_color(v):
        return RED if (v or 0) >= 7 else (AMBER if (v or 0) >= 4 else GREEN)

    hdr = [Paragraph(h, st["th"]) for h in
           ["Quarter", "Confidence", "Risk", "Narrative Shift"]]
    rows = [hdr]

    # Sort by quarter so we can compute fallback shifts between adjacent rows
    sorted_td = sorted(trend_data, key=lambda x: x.get("quarter", ""))

    for i, r in enumerate(sorted_td):
        conf  = r.get("confidence_score", "—")
        risk  = r.get("risk_score", "—")
        shift = r.get("narrative_shift") or ""

        # Fallback: if no stored narrative shift but we have a prior quarter,
        # generate a brief delta description from the score data
        if not shift and i > 0:
            prev = sorted_td[i - 1]
            conf_d = (r.get("confidence_score") or 0) - (prev.get("confidence_score") or 0)
            risk_d  = (r.get("risk_score") or 0)      - (prev.get("risk_score") or 0)
            prev_q  = prev.get("quarter", "prior quarter")
            parts = []
            if conf_d > 0:
                parts.append(f"Confidence increased {abs(conf_d)} pt{'s' if abs(conf_d) != 1 else ''} vs {prev_q}")
            elif conf_d < 0:
                parts.append(f"Confidence decreased {abs(conf_d)} pt{'s' if abs(conf_d) != 1 else ''} vs {prev_q}")
            else:
                parts.append(f"Confidence held steady at {r.get('confidence_score')}/10 vs {prev_q}")
            if risk_d > 0:
                parts.append(f"risk score rose {abs(risk_d)} pt{'s' if abs(risk_d) != 1 else ''}")
            elif risk_d < 0:
                parts.append(f"risk score fell {abs(risk_d)} pt{'s' if abs(risk_d) != 1 else ''}")
            else:
                parts.append(f"risk score unchanged at {r.get('risk_score')}/10")
            shift = "; ".join(parts) + ". No narrative shift was stored for this quarter — re-running the analysis will generate one."

        cc = _conf_color(conf)
        rc = _risk_color(risk)
        rows.append([
            Paragraph(r.get("quarter", ""), st["tc"]),
            Paragraph(f'<font color="#{cc.hexval()[2:]}"><b>{conf}/10</b></font>', st["tc_c"]),
            Paragraph(f'<font color="#{rc.hexval()[2:]}"><b>{risk}/10</b></font>', st["tc_c"]),
            Paragraph(shift, st["tc"]),
        ])

    score_t = Table(rows, colWidths=[0.85*inch, 0.85*inch, 0.7*inch, W-2.4*inch])
    score_t.setStyle(TableStyle([
        ("BACKGROUND",     (0, 0), (-1,  0), NAVY),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, CARD]),
        ("BOX",            (0, 0), (-1, -1), 0.4, BORDER),
        ("LINEBELOW",      (0, 0), (-1, -2), 0.3, BORDER),
        ("TOPPADDING",     (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING",  (0, 0), (-1, -1), 6),
        ("LEFTPADDING",    (0, 0), (-1, -1), 8),
        ("VALIGN",         (0, 0), (-1, -1), "TOP"),
        ("ALIGN",          (1, 0), (2,  -1), "CENTER"),
    ]))
    story.append(score_t)
    story.append(Spacer(1, 10))

    # Per-quarter detail — use sorted_td so fallback shifts are consistent
    for i, r in enumerate(sorted_td):
        q = r.get("quarter", "")
        block = []
        block += _section(f"{company}  —  {q}", st)

        # Narrative shift — full text, with fallback
        shift = r.get("narrative_shift") or ""
        if not shift and i > 0:
            prev = sorted_td[i - 1]
            conf_d = (r.get("confidence_score") or 0) - (prev.get("confidence_score") or 0)
            risk_d  = (r.get("risk_score") or 0)      - (prev.get("risk_score") or 0)
            prev_q  = prev.get("quarter", "prior quarter")
            parts = []
            if conf_d > 0:
                parts.append(f"Confidence increased {abs(conf_d)} pt{'s' if abs(conf_d) != 1 else ''} vs {prev_q}")
            elif conf_d < 0:
                parts.append(f"Confidence decreased {abs(conf_d)} pt{'s' if abs(conf_d) != 1 else ''} vs {prev_q}")
            else:
                parts.append(f"Confidence held steady at {r.get('confidence_score')}/10 vs {prev_q}")
            if risk_d > 0:
                parts.append(f"risk score rose {abs(risk_d)} pt{'s' if abs(risk_d) != 1 else ''}")
            elif risk_d < 0:
                parts.append(f"risk score fell {abs(risk_d)} pt{'s' if abs(risk_d) != 1 else ''}")
            else:
                parts.append(f"risk score unchanged at {r.get('risk_score')}/10")
            shift = "; ".join(parts) + ". Re-run this quarter's analysis to generate a full narrative shift."
        if shift:
            block.append(Paragraph("<b>Narrative Shift</b>", st["body_dim"]))
            block.append(Paragraph(shift, st["body"]))
            block.append(Spacer(1, 4))

        drivers = r.get("growth_drivers", [])
        if drivers:
            block.append(Paragraph("<b>Growth Drivers</b>", st["body_dim"]))
            for d in drivers:
                block.append(Paragraph(f"<font color='#3B82F6'>›</font>  {d}", st["body"]))
            block.append(Spacer(1, 4))

        risks = r.get("risks", [])
        if risks:
            block.append(Paragraph("<b>Key Risks</b>", st["body_dim"]))
            for ri in risks:
                if isinstance(ri, dict):
                    tag = _pill(ri.get("severity", "medium"))
                    block.append(Paragraph(f"{tag}  {ri.get('risk','')}", st["body"]))
            block.append(Spacer(1, 4))

        guidance = r.get("guidance", "")
        if guidance:
            block.append(Paragraph("<b>Guidance</b>", st["body_dim"]))
            block.append(Paragraph(guidance, st["body"]))
            block.append(Spacer(1, 4))

        impl = r.get("strategic_implications", [])
        if impl:
            block.append(Paragraph("<b>Strategic Implications</b>", st["body_dim"]))
            for i in impl:
                block.append(Paragraph(f"<font color='#3B82F6'>›</font>  {i}", st["body"]))

        story.append(KeepTogether(block))
        story.append(Spacer(1, 8))

    story += _footer(st)
    doc.build(story)
    return buf.getvalue()
