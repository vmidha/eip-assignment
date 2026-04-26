"""
prompts.py
System and user prompt templates for the Earnings Intelligence Platform.

The critical architectural decision: Claude returns structured JSON, not prose.
This enables database storage, trend visualizations, and comparison mode.
The tradeoff: more careful prompt engineering and a fallback parser in analyzer.py.
"""

SYSTEM_PROMPT = """You are a senior BizOps analyst preparing an intelligence brief for the strategy team at a public technology company.

Your output must be a single valid JSON object. No preamble. No explanation. No markdown. No code fences. Only the raw JSON object.

Rules:
- Every claim must reference the source in the transcript (speaker name, direct quote, or paraphrase with attribution)
- Three to five points per section maximum — never exceed this
- Confidence score: 1 (extremely hedged, defensive language throughout) to 10 (highly confident, forward-leaning language throughout)
- Risk score: 1 (no material risks flagged) to 10 (multiple severe risks explicitly called out)
- For management_confidence_signals: flag [CONFIDENT] for assertive forward guidance, [HEDGED] for qualifications, caveats, and uncertainty language
- For risks: severity is "high" if management or analysts dwelled on it, "medium" if mentioned once, "low" if only implied
- narrative_shift must be null if no prior quarter context is provided
- strategic_implications must be exactly 3 items — directional hypotheses for a competitor analyst, not conclusions
- Quote fields must use exact language from the transcript, kept under 30 words

Output this exact JSON schema and nothing else:

{
  "executive_summary": "<3 to 4 sentence plain-English summary of the most important things a strategy team needs to know from this call. Lead with the single biggest takeaway. Be direct and specific — no filler.>",
  "confidence_score": <integer 1-10>,
  "risk_score": <integer 1-10>,
  "growth_drivers": [
    "<driver with attribution>",
    "<driver with attribution>",
    "<driver with attribution>"
  ],
  "management_confidence_signals": [
    {"signal": "<description>", "quote": "<exact quote>", "type": "high"},
    {"signal": "<description>", "quote": "<exact quote>", "type": "low"}
  ],
  "risks": [
    {"risk": "<risk description>", "severity": "high", "quote": "<exact quote>"},
    {"risk": "<risk description>", "severity": "medium", "quote": "<exact quote>"}
  ],
  "guidance": "<summary of next quarter and full year guidance with direct quotes>",
  "narrative_shift": "<how the story has changed vs prior quarter, or null>",
  "strategic_implications": [
    "<implication 1 for a competitor analyst>",
    "<implication 2 for a competitor analyst>",
    "<implication 3 for a competitor analyst>"
  ]
}"""


def build_analysis_prompt(
    transcript: str,
    company: str,
    quarter: str,
    prior_context: str = None,
) -> str:
    prior_block = ""
    if prior_context:
        prior_block = f"""
PRIOR QUARTER ANALYSIS SUMMARY (for narrative_shift context):
{prior_context}

"""
    return f"""Analyze this earnings call transcript and return the JSON brief.

Company: {company}
Quarter: {quarter}
{prior_block}
TRANSCRIPT:

{transcript}"""


def build_comparison_prompt(
    transcript_a: str,
    company_a: str,
    quarter_a: str,
    transcript_b: str,
    company_b: str,
    quarter_b: str,
) -> str:
    return f"""You are comparing two earnings call transcripts to generate a competitive intelligence brief.

Analyze both transcripts and return a single JSON object with this exact schema:

{{
  "company_a": {{
    "name": "{company_a}",
    "quarter": "{quarter_a}",
    "confidence_score": <integer 1-10>,
    "risk_score": <integer 1-10>,
    "growth_drivers": ["<driver>", "<driver>", "<driver>"],
    "management_confidence_signals": [
      {{"signal": "<desc>", "quote": "<quote>", "type": "high"}}
    ],
    "risks": [
      {{"risk": "<desc>", "severity": "high", "quote": "<quote>"}}
    ],
    "guidance": "<guidance summary>",
    "narrative_shift": null,
    "strategic_implications": ["<impl>", "<impl>", "<impl>"]
  }},
  "company_b": {{
    "name": "{company_b}",
    "quarter": "{quarter_b}",
    "confidence_score": <integer 1-10>,
    "risk_score": <integer 1-10>,
    "growth_drivers": ["<driver>", "<driver>", "<driver>"],
    "management_confidence_signals": [
      {{"signal": "<desc>", "quote": "<quote>", "type": "high"}}
    ],
    "risks": [
      {{"risk": "<desc>", "severity": "high", "quote": "<quote>"}}
    ],
    "guidance": "<guidance summary>",
    "narrative_shift": null,
    "strategic_implications": ["<impl>", "<impl>", "<impl>"]
  }},
  "convergences": ["<shared theme>", "<shared theme>"],
  "divergences": ["<key difference>", "<key difference>"],
  "synthesis": ["<actionable insight 1>", "<actionable insight 2>", "<actionable insight 3>"]
}}

No preamble. No explanation. Raw JSON only.

{company_a} — {quarter_a} TRANSCRIPT:
{transcript_a}

---

{company_b} — {quarter_b} TRANSCRIPT:
{transcript_b}"""


import json as _json


def build_comparison_from_stored_prompt(
    company_a: str,
    quarter_a: str,
    summary_a: dict,
    company_b: str,
    quarter_b: str,
    summary_b: dict,
) -> str:
    """
    Comparison prompt when using stored analyses instead of raw transcripts.
    Passes structured summaries so no transcript text is needed.
    """
    def fmt(company, quarter, s):
        risks_text = "; ".join(
            r.get("risk", "") if isinstance(r, dict) else str(r)
            for r in s.get("risks", [])
        )
        return (
            f"Company: {company}\n"
            f"Quarter: {quarter}\n"
            f"Confidence: {s.get('confidence_score','N/A')}/10\n"
            f"Risk: {s.get('risk_score','N/A')}/10\n"
            f"Executive summary: {s.get('executive_summary','N/A')}\n"
            f"Growth drivers: {'; '.join(s.get('growth_drivers', []))}\n"
            f"Guidance: {s.get('guidance','N/A')}\n"
            f"Top risks: {risks_text}\n"
            f"Strategic implications: {'; '.join(s.get('strategic_implications', []))}\n"
            f"Narrative shift: {s.get('narrative_shift') or 'N/A'}"
        )

    return (
        "You are generating a competitive intelligence comparison from two stored earnings analyses.\n\n"
        "Use the structured data below. Return this exact JSON and nothing else:\n\n"
        "{\n"
        f'  "company_a": {{"name":"{company_a}","quarter":"{quarter_a}",'
        f'"confidence_score":{summary_a.get("confidence_score",5)},'
        f'"risk_score":{summary_a.get("risk_score",5)},'
        f'"growth_drivers":{_json.dumps(summary_a.get("growth_drivers",[]))},'
        f'"management_confidence_signals":{_json.dumps(summary_a.get("management_confidence_signals",[]))},'
        f'"risks":{_json.dumps(summary_a.get("risks",[]))},'
        f'"guidance":{_json.dumps(summary_a.get("guidance",""))},'
        f'"narrative_shift":null,'
        f'"strategic_implications":{_json.dumps(summary_a.get("strategic_implications",[]))}}},'
        f'\n  "company_b": {{"name":"{company_b}","quarter":"{quarter_b}",'
        f'"confidence_score":{summary_b.get("confidence_score",5)},'
        f'"risk_score":{summary_b.get("risk_score",5)},'
        f'"growth_drivers":{_json.dumps(summary_b.get("growth_drivers",[]))},'
        f'"management_confidence_signals":{_json.dumps(summary_b.get("management_confidence_signals",[]))},'
        f'"risks":{_json.dumps(summary_b.get("risks",[]))},'
        f'"guidance":{_json.dumps(summary_b.get("guidance",""))},'
        f'"narrative_shift":null,'
        f'"strategic_implications":{_json.dumps(summary_b.get("strategic_implications",[]))}}},'
        '\n  "convergences": ["<shared theme>","<shared theme>"],'
        '\n  "divergences": ["<key difference>","<key difference>"],'
        '\n  "synthesis": ["<insight 1>","<insight 2>","<insight 3>"]'
        "\n}\n\n"
        "No preamble. No explanation. Raw JSON only.\n\n"
        f"{company_a} — {quarter_a}:\n{fmt(company_a, quarter_a, summary_a)}\n\n"
        "---\n\n"
        f"{company_b} — {quarter_b}:\n{fmt(company_b, quarter_b, summary_b)}"
    )
