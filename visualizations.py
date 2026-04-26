"""
visualizations.py
All Plotly chart generation for the Trends dashboard.
Dark theme to match the app — navy backgrounds, no white chart areas.
"""

import json
import plotly.graph_objects as go
from typing import List, Tuple

# ── Dark palette ─────────────────────────────────────────────────────────────────
ORANGE      = "#FF6B35"
NAVY        = "#0A1628"
CARD_BG     = "#0f1e33"
BORDER      = "#1e3a5f"
BLUE_ACCENT = "#3B82F6"
ICE_BLUE    = "#CADCFC"
SLATE       = "#64849f"
RED         = "#f87171"
GREEN       = "#4ade80"
AMBER       = "#fbbf24"
GRID        = "#1a2e4a"
TEXT        = "#c8d6e5"
TEXT_DIM    = "#64849f"

BASE = dict(
    paper_bgcolor=CARD_BG,
    plot_bgcolor=CARD_BG,
    font=dict(family="Inter, Segoe UI, sans-serif", color=TEXT, size=12),
    margin=dict(l=48, r=24, t=52, b=44),
    hoverlabel=dict(
        bgcolor="#112240",
        font_color=ICE_BLUE,
        font_size=12,
        bordercolor=BORDER,
    ),
)


def _axis(title="", dtick=None, tickformat=None, showgrid=True):
    d = dict(
        title=dict(text=title, font=dict(color=TEXT_DIM, size=11)),
        tickfont=dict(color=TEXT_DIM, size=11),
        showgrid=showgrid,
        gridcolor=GRID,
        gridwidth=1,
        zeroline=False,
        linecolor=BORDER,
        showline=True,
    )
    if dtick: d["dtick"] = dtick
    if tickformat: d["tickformat"] = tickformat
    return d


def _title(text):
    return dict(
        text=text,
        font=dict(color=ICE_BLUE, size=14, family="Inter, Segoe UI, sans-serif"),
        x=0,
        xanchor="left",
        pad=dict(l=4),
    )


def _empty_fig(title, message="Add more quarters to populate this chart"):
    fig = go.Figure()
    fig.add_annotation(
        text=message,
        x=0.5, y=0.5, xref="paper", yref="paper",
        showarrow=False,
        font=dict(color=TEXT_DIM, size=13),
    )
    fig.update_layout(
        **BASE,
        title=_title(title),
        xaxis=dict(showgrid=False, showticklabels=False, zeroline=False, linecolor=BORDER),
        yaxis=dict(showgrid=False, showticklabels=False, zeroline=False, linecolor=BORDER),
    )
    return fig


# ── Chart 1: Confidence score over time ──────────────────────────────────────────

def confidence_chart(trend_data: List[dict], company: str = "Primary",
                     overlay_data: List[dict] = None, overlay_name: str = None) -> go.Figure:
    quarters = [r["quarter"] for r in trend_data]
    scores   = [r["confidence_score"] or 5 for r in trend_data]

    fig = go.Figure()

    # Subtle zone bands
    fig.add_hrect(y0=0,  y1=4,  fillcolor=RED,   opacity=0.05, line_width=0)
    fig.add_hrect(y0=7,  y1=10, fillcolor=GREEN,  opacity=0.05, line_width=0)

    # Zone labels
    fig.add_annotation(text="Low confidence zone", x=1, y=2,
        xref="paper", showarrow=False,
        font=dict(color=RED, size=10), xanchor="right")
    fig.add_annotation(text="High confidence zone", x=1, y=8.5,
        xref="paper", showarrow=False,
        font=dict(color=GREEN, size=10), xanchor="right")

    # Line + markers — primary company
    fig.add_trace(go.Scatter(
        x=quarters, y=scores,
        name=company,
        mode="lines+markers",
        line=dict(color=ORANGE, width=2.5, shape="spline"),
        marker=dict(size=10, color=ORANGE, line=dict(color=CARD_BG, width=2)),
        hovertemplate=f"<b>{company}</b> · %{{x}}<br>Confidence: <b>%{{y}}/10</b><extra></extra>",
    ))

    # Overlay series
    all_scores = list(scores)
    if overlay_data and overlay_name:
        ov_quarters = [r["quarter"] for r in overlay_data]
        ov_scores   = [r["confidence_score"] or 5 for r in overlay_data]
        all_scores  += ov_scores
        fig.add_trace(go.Scatter(
            x=ov_quarters, y=ov_scores,
            name=overlay_name,
            mode="lines+markers",
            line=dict(color=BLUE_ACCENT, width=2.5, shape="spline", dash="dash"),
            marker=dict(size=9, color=BLUE_ACCENT, line=dict(color=CARD_BG, width=2)),
            hovertemplate=f"<b>{overlay_name}</b> · %{{x}}<br>Confidence: <b>%{{y}}/10</b><extra></extra>",
        ))

    # Annotate peak and low only when they differ
    if len(scores) >= 2 and max(scores) != min(scores):
        max_i = scores.index(max(scores))
        min_i = scores.index(min(scores))
        for idx, lbl, col, ay in [
            (max_i, f"Peak {scores[max_i]}", GREEN, -32),
            (min_i, f"Low {scores[min_i]}", RED, 32),
        ]:
            fig.add_annotation(
                x=quarters[idx], y=scores[idx],
                text=lbl, showarrow=True, arrowhead=2,
                arrowcolor=col, arrowwidth=1.5,
                font=dict(size=10, color=col),
                ay=ay, ax=0, bgcolor=CARD_BG,
                bordercolor=col, borderwidth=1, borderpad=3,
            )

    # Tight y-axis using all visible scores
    y_min = max(0, min(all_scores) - 1.5)
    y_max = min(10, max(all_scores) + 1.5)
    if y_max - y_min < 3:
        y_min = max(0, y_min - 1)
        y_max = min(10, y_max + 1)

    show_legend = bool(overlay_data and overlay_name)

    fig.update_layout(
        **BASE,
        title=_title("Management Confidence Score"),
        xaxis=dict(**_axis("Quarter", showgrid=False)),
        yaxis=dict(**_axis("Score (1–10)", dtick=1), range=[y_min, y_max]),
        showlegend=show_legend,
        legend=dict(
            orientation="h", y=-0.2,
            font=dict(color=TEXT_DIM, size=11),
            bgcolor="rgba(0,0,0,0)",
        ),
    )
    return fig


# ── Chart 2: Risk frequency heatmap ──────────────────────────────────────────────

RISK_CATEGORIES = ["macro", "competitive", "regulatory", "operational", "guidance", "product"]


def _categorize_risk(text: str) -> str:
    t = text.lower()
    if any(w in t for w in ["macro", "economy", "recession", "inflation", "interest rate", "gdp"]):
        return "macro"
    if any(w in t for w in ["competi", "market share", "rival", "alternative"]):
        return "competitive"
    if any(w in t for w in ["regulat", "legal", "compliance", "antitrust", "policy"]):
        return "regulatory"
    if any(w in t for w in ["operat", "supply chain", "execut", "headcount", "cost", "margin"]):
        return "operational"
    if any(w in t for w in ["guid", "forecast", "outlook", "expect", "target"]):
        return "guidance"
    return "product"


def risk_heatmap(trend_data: List[dict]) -> go.Figure:
    quarters = [r["quarter"] for r in trend_data]
    matrix   = {cat: [0] * len(quarters) for cat in RISK_CATEGORIES}
    details  = {cat: [""] * len(quarters) for cat in RISK_CATEGORIES}

    for q_idx, row in enumerate(trend_data):
        for item in row.get("risks", []):
            text  = item.get("risk", "") if isinstance(item, dict) else str(item)
            sev   = item.get("severity", "medium") if isinstance(item, dict) else "medium"
            quote = item.get("quote", "") if isinstance(item, dict) else ""
            weight = {"high": 3, "medium": 2, "low": 1}.get(sev, 1)
            cat   = _categorize_risk(text)
            matrix[cat][q_idx] += weight
            entry = f"[{sev.upper()}] {text}"
            if quote:
                entry += f'  "{quote[:80]}..."' if len(quote) > 80 else f'  "{quote}"'
            details[cat][q_idx] = (details[cat][q_idx] + "\n" + entry).strip()

    # Build hover text — concise: just risk names, no quotes
    hover_text = []
    for cat in RISK_CATEGORIES:
        row_hover = []
        for q_idx in range(len(quarters)):
            score = matrix[cat][q_idx]
            if score == 0:
                row_hover.append("No risks recorded")
            else:
                # Pull just the risk names for this category/quarter (no quotes)
                names = []
                for item in trend_data[q_idx].get("risks", []):
                    text = item.get("risk", "") if isinstance(item, dict) else str(item)
                    sev  = item.get("severity", "medium") if isinstance(item, dict) else "medium"
                    if _categorize_risk(text) == cat:
                        short = text[:55] + "…" if len(text) > 55 else text
                        names.append(f"[{sev.upper()[0]}] {short}")
                row_hover.append("<br>".join(names) if names else f"Score: {score}")
        hover_text.append(row_hover)

    z           = [matrix[cat] for cat in RISK_CATEGORIES]
    detail_text = [details[cat] for cat in RISK_CATEGORIES]

    fig = go.Figure(go.Heatmap(
        z=z,
        x=quarters,
        y=RISK_CATEGORIES,
        customdata=detail_text,   # kept for click panel
        text=hover_text,
        # Fixed zmin/zmax so colour meaning is identical across all companies
        zmin=0,
        zmax=9,
        colorscale=[
            [0.0,   "#2a3a52"],   # none   — clearly visible muted slate, distinct from bg
            [0.06,  "#163354"],   # trace  — dark navy blue
            [0.28,  "#1d4e89"],   # low    — medium blue
            [0.55,  "#d97706"],   # medium — amber
            [0.80,  "#dc2626"],   # high   — red
            [1.0,   "#7f1d1d"],   # max    — deep red
        ],
        showscale=True,
        colorbar=dict(
            title=dict(text="Severity", font=dict(color=TEXT_DIM, size=11)),
            tickfont=dict(color=TEXT_DIM, size=10),
            outlinecolor=BORDER,
            outlinewidth=1,
            thickness=12,
            tickvals=[0, 2, 4, 6, 9],
            ticktext=["None", "Low", "Medium", "High", "Critical"],
        ),
        hovertemplate=(
            "<b>%{y}  ·  %{x}</b><br>"
            "Severity score: <b>%{z}</b><br>"
            "%{text}<extra></extra>"
        ),
    ))

    fig.update_layout(
        **BASE,
        title=_title("Risk Category Heatmap  ·  click for detail"),
        xaxis=dict(**_axis("Quarter", showgrid=False)),
        yaxis=dict(
            tickfont=dict(color=TEXT_DIM, size=11),
            showgrid=False, zeroline=False,
            linecolor=BORDER, showline=True,
        ),
    )
    return fig


# ── Chart 3: Confidence vs Risk grouped bar ───────────────────────────────────────

def guidance_accuracy_chart(trend_data: List[dict], company: str = "Primary",
                             overlay_data: List[dict] = None, overlay_name: str = None) -> go.Figure:
    if len(trend_data) < 2 and not overlay_data:
        row = trend_data[0]
        conf = row.get("confidence_score") or 5
        risk = row.get("risk_score") or 5
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=["Confidence", "Risk"],
            y=[conf, risk],
            marker_color=[ORANGE, BLUE_ACCENT],
            text=[f"{conf}/10", f"{risk}/10"],
            textposition="outside",
            textfont=dict(color=TEXT, size=13),
            hovertemplate="<b>%{x}</b>: %{y}/10<extra></extra>",
            width=0.4,
        ))
        fig.update_layout(
            **BASE,
            title=_title("Confidence vs Risk  (add quarters for trend)"),
            xaxis=dict(showgrid=False, tickfont=dict(color=TEXT, size=13), zeroline=False, linecolor=BORDER, showline=True),
            yaxis=dict(**_axis("Score (1–10)", dtick=2), range=[0, 12]),
            showlegend=False,
        )
        return fig

    quarters   = [r["quarter"] for r in trend_data]
    confidence = [r["confidence_score"] or 5 for r in trend_data]
    risk       = [r["risk_score"] or 5 for r in trend_data]

    fig = go.Figure()

    # Primary company bars
    fig.add_trace(go.Bar(
        name=f"{company} — Confidence", x=quarters, y=confidence,
        marker_color=ORANGE, opacity=0.9,
        hovertemplate=f"<b>{company}</b> · %{{x}}<br>Confidence: <b>%{{y}}/10</b><extra></extra>",
    ))
    fig.add_trace(go.Bar(
        name=f"{company} — Risk", x=quarters, y=risk,
        marker_color=BLUE_ACCENT, opacity=0.9,
        hovertemplate=f"<b>{company}</b> · %{{x}}<br>Risk: <b>%{{y}}/10</b><extra></extra>",
    ))

    # Overlay bars
    if overlay_data and overlay_name:
        ov_quarters   = [r["quarter"] for r in overlay_data]
        ov_confidence = [r["confidence_score"] or 5 for r in overlay_data]
        ov_risk       = [r["risk_score"] or 5 for r in overlay_data]
        fig.add_trace(go.Bar(
            name=f"{overlay_name} — Confidence", x=ov_quarters, y=ov_confidence,
            marker_color=ORANGE, opacity=0.45,
            marker_pattern_shape="/",
            hovertemplate=f"<b>{overlay_name}</b> · %{{x}}<br>Confidence: <b>%{{y}}/10</b><extra></extra>",
        ))
        fig.add_trace(go.Bar(
            name=f"{overlay_name} — Risk", x=ov_quarters, y=ov_risk,
            marker_color=BLUE_ACCENT, opacity=0.45,
            marker_pattern_shape="/",
            hovertemplate=f"<b>{overlay_name}</b> · %{{x}}<br>Risk: <b>%{{y}}/10</b><extra></extra>",
        ))

    has_overlay = bool(overlay_data and overlay_name)
    fig.update_layout(
        **BASE,
        barmode="group",
        bargap=0.25,
        bargroupgap=0.06,
        title=_title("Confidence vs Risk Over Time"),
        xaxis=dict(**_axis("Quarter", showgrid=False)),
        yaxis=dict(**_axis("Score (1–10)", dtick=2), range=[0, 11]),
        legend=dict(
            orientation="h", y=-0.22,
            font=dict(color=TEXT_DIM, size=10),
            bgcolor="rgba(0,0,0,0)",
        ) if has_overlay else dict(
            orientation="h", y=-0.18,
            font=dict(color=TEXT_DIM, size=11),
            bgcolor="rgba(0,0,0,0)",
        ),
        showlegend=True,
    )
    return fig


# ── Chart 4: Narrative theme evolution ───────────────────────────────────────────

THEME_KEYWORDS = {
    "Growth":      ["growth", "revenue", "expand", "scale", "accelerat", "record", "momentum"],
    "Risk":        ["risk", "challeng", "uncertain", "headwind", "concern", "decline", "pressure"],
    "Product":     ["product", "platform", "feature", "launch", "technolog", "AI", "model", "tool"],
    "Competition": ["competi", "market share", "rival", "industry", "sector", "peers"],
}

THEME_COLORS = {
    "Growth":      "#FF6B35",   # orange — strong, warm
    "Risk":        "#f87171",   # red — danger signal
    "Product":     "#3B82F6",   # blue — neutral/tech
    "Competition": "#a78bfa",   # purple — distinct from all others
}


def _score_themes(row: dict) -> dict:
    corpus = " ".join(filter(None, [
        " ".join(row.get("growth_drivers", [])),
        row.get("guidance", ""),
        row.get("narrative_shift") or "",
        " ".join(
            (i.get("risk", "") if isinstance(i, dict) else str(i))
            for i in row.get("risks", [])
        ),
        " ".join(
            (i.get("signal", "") if isinstance(i, dict) else str(i))
            for i in row.get("management_confidence", [])
        ),
    ])).lower()

    scores = {t: sum(corpus.count(kw) for kw in kws) for t, kws in THEME_KEYWORDS.items()}
    total  = sum(scores.values()) or 1
    return {t: round(v / total * 100, 1) for t, v in scores.items()}


def narrative_theme_chart(trend_data: List[dict], company: str = "Primary",
                           overlay_data: List[dict] = None, overlay_name: str = None) -> go.Figure:
    quarters   = [r["quarter"] for r in trend_data]
    theme_data = [_score_themes(r) for r in trend_data]

    all_zero = all(sum(td.values()) == 0 for td in theme_data)
    if all_zero:
        return _empty_fig("Narrative Theme Breakdown", "Run more analyses to populate theme data")

    fig = go.Figure()

    # Single quarter, no overlay — horizontal bar breakdown
    if len(trend_data) == 1 and not overlay_data:
        td = theme_data[0]
        themes = list(THEME_KEYWORDS.keys())
        values = [td.get(t, 0) for t in themes]
        colors = [THEME_COLORS[t] for t in themes]
        fig.add_trace(go.Bar(
            x=values, y=themes,
            orientation="h",
            marker_color=colors,
            opacity=0.85,
            text=[f"{v:.0f}%" for v in values],
            textposition="outside",
            textfont=dict(color=TEXT, size=12),
            hovertemplate="<b>%{y}</b>: %{x:.1f}%<extra></extra>",
        ))
        fig.update_layout(
            **BASE,
            title=_title("Narrative Theme Breakdown  (add quarters for trend)"),
            xaxis=dict(**_axis("Share (%)"), range=[0, max(values) * 1.25 if values else 100]),
            yaxis=dict(tickfont=dict(color=TEXT, size=12), showgrid=False,
                       zeroline=False, linecolor=BORDER, showline=True),
            showlegend=False,
        )
        return fig

    # With overlay — switch to lines so both datasets are readable
    if overlay_data and overlay_name:
        ov_quarters   = [r["quarter"] for r in overlay_data]
        ov_theme_data = [_score_themes(r) for r in overlay_data]

        for theme in THEME_KEYWORDS:
            y_primary = [td.get(theme, 0) for td in theme_data]
            y_overlay = [td.get(theme, 0) for td in ov_theme_data]

            fig.add_trace(go.Scatter(
                x=quarters, y=y_primary,
                name=f"{company} — {theme}",
                mode="lines+markers",
                line=dict(color=THEME_COLORS[theme], width=2.5),
                marker=dict(size=7, color=THEME_COLORS[theme],
                            line=dict(color=CARD_BG, width=1.5)),
                hovertemplate=(
                    f"<b>{company} · {theme}</b><br>"
                    f"%{{x}}: <b>%{{y:.1f}}%</b><extra></extra>"
                ),
            ))
            fig.add_trace(go.Scatter(
                x=ov_quarters, y=y_overlay,
                name=f"{overlay_name} — {theme}",
                mode="lines+markers",
                line=dict(color=THEME_COLORS[theme], width=2.5, dash="dot"),
                marker=dict(size=7, color=THEME_COLORS[theme], symbol="diamond",
                            line=dict(color=CARD_BG, width=1.5)),
                hovertemplate=(
                    f"<b>{overlay_name} · {theme}</b><br>"
                    f"%{{x}}: <b>%{{y:.1f}}%</b><extra></extra>"
                ),
            ))

        fig.update_layout(
            **BASE,
            title=_title("Narrative Theme Comparison"),
            xaxis=dict(**_axis("Quarter", showgrid=False)),
            yaxis=dict(**_axis("Theme Share (%)")),
            legend=dict(
                orientation="h", y=-0.32,
                font=dict(color=TEXT_DIM, size=9),
                bgcolor="rgba(0,0,0,0)",
                tracegroupgap=4,
            ),
        )
        return fig

    # Multiple quarters, no overlay — stacked area
    for theme in THEME_KEYWORDS:
        y_vals = [td.get(theme, 0) for td in theme_data]
        fig.add_trace(go.Scatter(
            x=quarters, y=y_vals,
            name=theme,
            stackgroup="one",
            mode="lines",
            line=dict(width=0, color=THEME_COLORS[theme]),
            fillcolor=THEME_COLORS[theme],
            opacity=0.8,
            hovertemplate=f"<b>{theme}</b> · %{{x}}<br>Share: <b>%{{y:.1f}}%</b><extra></extra>",
        ))

    fig.update_layout(
        **BASE,
        title=_title("Narrative Theme Evolution"),
        xaxis=dict(**_axis("Quarter", showgrid=False)),
        yaxis=dict(**_axis("Theme Share (%)")),
        legend=dict(
            orientation="h", y=-0.18,
            font=dict(color=TEXT_DIM, size=11),
            bgcolor="rgba(0,0,0,0)",
        ),
    )
    return fig


# ── Dashboard builder ─────────────────────────────────────────────────────────────

def build_trend_dashboard(
    trend_data: List[dict],
    company: str = "Primary",
    overlay_data: List[dict] = None,
    overlay_name: str = None,
) -> Tuple[go.Figure, go.Figure, go.Figure, go.Figure]:
    return (
        confidence_chart(trend_data, company, overlay_data, overlay_name),
        risk_heatmap(trend_data),
        guidance_accuracy_chart(trend_data, company, overlay_data, overlay_name),
        narrative_theme_chart(trend_data, company, overlay_data, overlay_name),
    )


def get_risk_detail(trend_data: List[dict], quarter: str, category: str) -> List[dict]:
    """Return all risk items for a given quarter and category for the click detail panel."""
    for row in trend_data:
        if row["quarter"] == quarter:
            return [
                item for item in row.get("risks", [])
                if isinstance(item, dict) and _categorize_risk(item.get("risk", "")) == category
            ]
    return []
