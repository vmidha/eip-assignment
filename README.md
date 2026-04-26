# Earnings Intelligence Platform

A multi-feature Streamlit application that analyzes earnings call transcripts, tracks narrative trends across quarters, and generates competitive intelligence comparisons — powered by Claude.

---

## Features

**Analyze tab** — Paste or upload any earnings call transcript and get a structured six-section intelligence brief in under 40 seconds. Results are automatically saved to SQLite so they appear in the Trends dashboard immediately.

**Trends tab** — Load analyses across up to eight quarters and view four interactive Plotly charts: management confidence over time, risk category heatmap, guidance vs risk profile, and narrative theme evolution.

**Compare tab** — Run two transcripts simultaneously and get a side-by-side competitive brief including convergences, divergences, and a three-point strategic synthesis.

---

## Setup

### 1. Clone and navigate

```bash
git clone <your-repo-url>
cd earnings-platform
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate      # Mac/Linux
venv\Scripts\activate         # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure your API key

```bash
cp .env.example .env
```

Open `.env` and replace the placeholder with your Anthropic API key:

```
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

### 5. Run

```bash
streamlit run app.py
```

Opens at `http://localhost:8501`.

---

## Architecture

```
Transcript input (paste or PDF upload)
        ↓
analyzer.py — Claude API call with JSON system prompt
        ↓
JSON structured output (confidence score, risk score, six sections)
        ↓
database.py — SQLite storage (data/analyses.db)
        ↓
visualizations.py — Plotly charts (confidence, heatmap, guidance, themes)
        ↓
app.py — Streamlit UI (Analyze | Trends | Compare tabs)
```

### Why each component was chosen

| Component | Choice | Reason |
|---|---|---|
| LLM | Claude Sonnet | Citation accuracy and JSON formatting reliability |
| Output format | Structured JSON | Enables DB storage, trend charts, and comparison mode |
| Database | SQLite | Zero infrastructure setup; sufficient for demo data volumes |
| Visualization | Plotly | Native Streamlit integration, interactive charts out of the box |
| Frontend | Streamlit | 48-hour build window; tabs and charts are production-quality for a demo |
| PDF parsing | pdfplumber + PyPDF2 | pdfplumber as primary, PyPDF2 as fallback for compatibility |

---

## Demo data

Place transcript `.txt` files in the `data/` folder. Recommended sources:

- **AppLovin** Q1–Q4 2024: [investors.applovin.com](https://investors.applovin.com)
- **The Trade Desk** Q4 2024: [thetradedesk.com/us/investor-relations](https://www.thetradedesk.com/us/investor-relations)
- **Seeking Alpha** publishes clean transcript text for most public companies

### Recommended demo sequence

1. Run AppLovin Q1 2024 → Analyze tab
2. Run AppLovin Q2, Q3, Q4 2024 → Section 5 (narrative shift) populates automatically after Q1
3. Switch to Trends tab → four charts populate for AppLovin
4. Switch to Compare tab → AppLovin Q4 2024 vs The Trade Desk Q4 2024

---

## Assumptions

- Transcript quality determines output quality — poorly formatted or partial transcripts produce weaker analysis
- Confidence and risk scores are relative indicators — most meaningful when compared across quarters, not in isolation
- The guidance tracker requires at least two quarters to show meaningful comparisons
- JSON output reliability depends on prompt quality — the fallback parser in `analyzer.py` handles the occasional malformed response
- This is a first-pass intelligence instrument, not a replacement for human analyst judgment

---

## Tradeoffs

**JSON over prose** — Machine-readable structured output enables every platform feature (database, charts, comparison). The cost is more careful prompt engineering and a fallback parser. This is the most technically interesting tradeoff and worth discussing explicitly.

**SQLite over cloud DB** — Zero infrastructure setup and sufficient for demo data volumes. Production deployment would move to PostgreSQL.

**Full transcript over chunking** — Earnings calls fit within Claude's context window. Chunking introduces analysis inconsistency that undermines quarter-over-quarter comparability.

**Streamlit over React** — 48 hours does not allow custom frontend development. Streamlit's tab and chart components produce a sufficiently professional demo result.

**No auth layer** — Demo context is single-user. Production deployment requires authentication.

---

## File structure

```
earnings-platform/
├── app.py               # Streamlit UI — three tabs
├── analyzer.py          # Claude API calls, JSON parsing, fallback logic
├── database.py          # SQLite schema, read/write functions
├── visualizations.py    # Four Plotly chart generators
├── prompts.py           # System and user prompt templates
├── requirements.txt     # Python dependencies
├── .env                 # API key (never commit)
├── .env.example         # Template
├── .gitignore
├── README.md
└── data/                # Transcript files + analyses.db (auto-created)
```

---

## Version 2 roadmap

1. Automated transcript ingestion via earnings call API — no manual upload
2. Slack integration — brief posts within minutes of a call ending
3. RAG on internal strategy documents — Section 6 references company-specific context
4. Natural language query interface — ask questions across the analysis database
5. Expanded coverage — analyst day presentations, 10-K filings, press releases

The architecture was designed from day one to support these extensions. None require a rebuild — only additional components on top of what already exists.
