"""
analyzer.py
Core analysis logic: Claude API calls, JSON parsing, fallback handling.

The fallback parser is important — the model occasionally wraps JSON in markdown
code fences or adds a preamble sentence. This module strips both before parsing.
"""

import json
import os
import re
from typing import Optional, Tuple
from anthropic import Anthropic
from dotenv import load_dotenv

from prompts import SYSTEM_PROMPT, build_analysis_prompt, build_comparison_prompt, build_comparison_from_stored_prompt
from database import save_analysis, get_trend_data, hash_transcript, analysis_exists, get_all_analyses

load_dotenv()


def _json_dumps(obj) -> str:
    """Convenience wrapper so app.py can call az._json_dumps."""
    return json.dumps(obj)


def score_transcript_quality(text: str) -> dict:
    """
    Score transcript quality before running analysis.
    Returns a dict with: score (0-100), grade, issues, warnings.
    No API call — pure text heuristics.
    """
    issues   = []
    warnings = []
    score    = 100

    word_count = len(text.split())
    if word_count < 1000:
        issues.append(f"Very short transcript ({word_count:,} words) — likely incomplete")
        score -= 40
    elif word_count < 3000:
        warnings.append(f"Short transcript ({word_count:,} words) — may be missing Q&A section")
        score -= 15

    # Speaker label detection
    speaker_patterns = re.findall(r'\n[A-Z][a-zA-Z\s]+:', text)
    if len(speaker_patterns) < 3:
        issues.append("No speaker labels detected — transcript may be unformatted text")
        score -= 25
    elif len(speaker_patterns) < 8:
        warnings.append("Few speaker transitions detected — may be missing analyst Q&A")
        score -= 10

    # Q&A section
    has_qa = bool(re.search(r'\b(question[s]?[ &]+answer|Q&A|question-and-answer|analyst question)\b', text, re.IGNORECASE))
    if not has_qa:
        warnings.append("No Q&A section detected — analysis of analyst questions may be limited")
        score -= 10

    # Inaudible / garbled content
    inaudible_count = len(re.findall(r'\[inaudible\]|\[unclear\]|\[crosstalk\]', text, re.IGNORECASE))
    if inaudible_count > 20:
        warnings.append(f"{inaudible_count} inaudible markers — transcript quality may be degraded")
        score -= 10
    elif inaudible_count > 5:
        warnings.append(f"{inaudible_count} inaudible markers detected")
        score -= 5

    # Operator/moderator presence (good signal of full call)
    has_operator = bool(re.search(r'\boperator\b|\bmoderator\b', text, re.IGNORECASE))
    if not has_operator:
        warnings.append("No operator/moderator detected — may not be a full call transcript")
        score -= 5

    # Financial content sanity check
    has_financials = bool(re.search(r'\$[\d,]+|\d+[\.,]\d+\s*(billion|million|%)', text, re.IGNORECASE))
    if not has_financials:
        issues.append("No financial figures detected — this may not be an earnings transcript")
        score -= 20

    score = max(0, min(100, score))

    if score >= 80:
        grade = "Good"
    elif score >= 60:
        grade = "Fair"
    elif score >= 40:
        grade = "Poor"
    else:
        grade = "Very Poor"

    return {
        "score":    score,
        "grade":    grade,
        "issues":   issues,
        "warnings": warnings,
        "word_count": word_count,
    }


def get_client() -> Anthropic:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not found. Add it to your .env file.")
    return Anthropic(api_key=api_key)


# ── JSON extraction ─────────────────────────────────────────────────────────────

def extract_json(raw: str) -> dict:
    """
    Parse JSON from Claude's response. Handles:
    - Clean JSON (ideal case)
    - JSON wrapped in ```json ... ``` fences
    - JSON preceded by a preamble sentence
    Raises ValueError if no valid JSON object is found.
    """
    # Strip code fences
    stripped = re.sub(r"```(?:json)?", "", raw).strip().rstrip("`").strip()

    # Try direct parse first
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        pass

    # Find the first { and last } and extract
    start = stripped.find("{")
    end = stripped.rfind("}") + 1
    if start != -1 and end > start:
        try:
            return json.loads(stripped[start:end])
        except json.JSONDecodeError:
            pass

    raise ValueError(f"Could not extract valid JSON from model response.\nRaw output:\n{raw[:500]}")


def validate_schema(data: dict) -> dict:
    """
    Ensure required fields exist with sensible defaults.
    Prevents KeyErrors downstream if the model omits a field.
    """
    defaults = {
        "executive_summary": "",
        "confidence_score": 5,
        "risk_score": 5,
        "growth_drivers": [],
        "management_confidence_signals": [],
        "risks": [],
        "guidance": "",
        "narrative_shift": None,
        "strategic_implications": [],
    }
    for key, default in defaults.items():
        if key not in data:
            data[key] = default
    return data


# ── Single transcript analysis ──────────────────────────────────────────────────

def run_analysis(
    transcript: str,
    company: str,
    quarter: str,
    save_to_db: bool = True,
) -> Tuple[dict, str]:
    """
    Run a single-transcript analysis.
    Returns (parsed_dict, full_raw_output).
    Saves to DB if save_to_db=True.
    """
    client = get_client()

    # Build prior quarter context if available
    prior_context = _get_prior_context(company, quarter)

    user_prompt = build_analysis_prompt(
        transcript=transcript,
        company=company,
        quarter=quarter,
        prior_context=prior_context,
    )

    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=3000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )

    raw = response.content[0].text
    parsed = validate_schema(extract_json(raw))

    if save_to_db:
        save_analysis(
            company=company,
            quarter=quarter,
            transcript=transcript,
            parsed=parsed,
            full_output=raw,
        )

    return parsed, raw


def _get_prior_context(company: str, quarter: str) -> Optional[str]:
    """
    Pull the most recent previous quarter's analysis to give Claude
    narrative shift context. Returns a concise text summary or None.
    """
    try:
        trend_data = get_trend_data(company)
        if not trend_data:
            return None
        # Sort and find the last entry before current quarter
        sorted_data = sorted(trend_data, key=lambda x: x["quarter"])
        candidates = [r for r in sorted_data if r["quarter"] < quarter]
        if not candidates:
            return None
        prior = candidates[-1]
        lines = [
            f"Quarter: {prior['quarter']}",
            f"Confidence score: {prior['confidence_score']}/10",
            f"Risk score: {prior['risk_score']}/10",
            f"Top growth drivers: {', '.join(prior['growth_drivers'][:3])}",
            f"Guidance: {prior['guidance'][:300] if prior['guidance'] else 'N/A'}",
        ]
        return "\n".join(lines)
    except Exception:
        return None


# ── Competitor comparison ───────────────────────────────────────────────────────

def run_comparison(
    transcript_a: str,
    company_a: str,
    quarter_a: str,
    transcript_b: str,
    company_b: str,
    quarter_b: str,
    save_both: bool = True,
) -> dict:
    """
    Run a side-by-side competitor comparison in one API call.
    Returns the full comparison dict including convergences, divergences, synthesis.
    Optionally saves both individual analyses to the DB.
    """
    client = get_client()

    prompt = build_comparison_prompt(
        transcript_a=transcript_a,
        company_a=company_a,
        quarter_a=quarter_a,
        transcript_b=transcript_b,
        company_b=company_b,
        quarter_b=quarter_b,
    )

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = response.content[0].text
    parsed = extract_json(raw)

    if save_both:
        for key, company, quarter, transcript in [
            ("company_a", company_a, quarter_a, transcript_a),
            ("company_b", company_b, quarter_b, transcript_b),
        ]:
            section = parsed.get(key, {})
            if section:
                validated = validate_schema(section)
                tx_hash = hash_transcript(transcript)
                if not analysis_exists(tx_hash):
                    save_analysis(
                        company=company,
                        quarter=quarter,
                        transcript=transcript,
                        parsed=validated,
                        full_output=raw,
                    )

    return parsed


def stored_row_to_parsed(row: dict) -> dict:
    """Convert a database row back into a parsed dict for comparison use."""
    return {
        "executive_summary": row.get("full_output", ""),  # fallback
        "confidence_score":  row.get("confidence_score", 5),
        "risk_score":        row.get("risk_score", 5),
        "growth_drivers":    json.loads(row.get("growth_drivers") or "[]"),
        "management_confidence_signals": json.loads(row.get("management_confidence") or "[]"),
        "risks":             json.loads(row.get("risks") or "[]"),
        "guidance":          row.get("guidance", ""),
        "narrative_shift":   row.get("narrative_shift"),
        "strategic_implications": json.loads(row.get("strategic_implications") or "[]"),
    }


def run_comparison_from_stored(
    row_a: dict,
    row_b: dict,
) -> dict:
    """
    Run a competitive comparison using two stored database rows.
    Builds summaries from stored fields and calls Claude to generate
    convergences, divergences, and synthesis.
    """
    client = get_client()

    summary_a = stored_row_to_parsed(row_a)
    summary_b = stored_row_to_parsed(row_b)

    prompt = build_comparison_from_stored_prompt(
        company_a=row_a["company"],
        quarter_a=row_a["quarter"],
        summary_a=summary_a,
        company_b=row_b["company"],
        quarter_b=row_b["quarter"],
        summary_b=summary_b,
    )

    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=4000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = response.content[0].text
    parsed = extract_json(raw)

    # Ensure stored fields are preserved exactly — don't overwrite with Claude inferences
    parsed["company_a"] = {**summary_a, **parsed.get("company_a", {}),
                            "name": row_a["company"], "quarter": row_a["quarter"]}
    parsed["company_b"] = {**summary_b, **parsed.get("company_b", {}),
                            "name": row_b["company"], "quarter": row_b["quarter"]}
    return parsed


# ── Multi-quarter summary brief ─────────────────────────────────────────────────

def generate_trend_summary(company: str, trend_data: list) -> str:
    """
    Generate a single AI-written paragraph synthesizing the full trend history
    for a company. Uses stored analyses — no transcript needed.
    Returns plain text.
    """
    client = get_client()

    # Build a concise structured summary of all quarters for the prompt
    quarters_text = ""
    for r in sorted(trend_data, key=lambda x: x["quarter"]):
        quarters_text += f"\n{r['quarter']}:\n"
        quarters_text += f"  Confidence: {r.get('confidence_score','N/A')}/10, Risk: {r.get('risk_score','N/A')}/10\n"
        quarters_text += f"  Growth: {'; '.join(r.get('growth_drivers', [])[:2])}\n"
        quarters_text += f"  Guidance: {(r.get('guidance') or '')[:200]}\n"
        quarters_text += f"  Narrative shift: {(r.get('narrative_shift') or 'N/A')[:200]}\n"
        risks = r.get("risks", [])
        top_risks = [ri.get("risk","") if isinstance(ri,dict) else str(ri) for ri in risks[:2]]
        quarters_text += f"  Top risks: {'; '.join(top_risks)}\n"

    prompt = f"""You are a senior BizOps analyst. Write a single concise paragraph (4-6 sentences) that synthesizes the full trend history for {company} based on the structured data below.

Lead with the single most important trend or pattern. Cover: confidence trajectory, risk evolution, key narrative shifts, and what this suggests about the company's near-term outlook. Be specific — cite actual score movements and quarters. Write in plain English for a strategy audience. No bullet points, no headers, no preamble.

DATA:
{quarters_text}

Output only the paragraph. Nothing else."""

    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text.strip()


# ── PDF text extraction ─────────────────────────────────────────────────────────

def extract_text_from_pdf(uploaded_file) -> str:
    """
    Extract plain text from a PDF upload.
    Tries pdfplumber first, falls back to PyPDF2.
    """
    try:
        import pdfplumber
        import io
        with pdfplumber.open(io.BytesIO(uploaded_file.read())) as pdf:
            pages = [page.extract_text() or "" for page in pdf.pages]
        uploaded_file.seek(0)
        return "\n".join(pages).strip()
    except Exception:
        pass

    try:
        import PyPDF2
        import io
        reader = PyPDF2.PdfReader(io.BytesIO(uploaded_file.read()))
        text = "\n".join(
            page.extract_text() or "" for page in reader.pages
        )
        uploaded_file.seek(0)
        return text.strip()
    except Exception as e:
        raise ValueError(f"Could not extract text from PDF: {e}")
