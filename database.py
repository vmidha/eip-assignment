"""
database.py
SQLite persistence layer for the Earnings Intelligence Platform.
Handles schema creation, analysis storage, retrieval, and deletion.
"""

import sqlite3
import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

DB_PATH = Path("data/analyses.db")


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create tables if they don't exist."""
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS analyses (
                id                    INTEGER PRIMARY KEY AUTOINCREMENT,
                company               TEXT NOT NULL,
                quarter               TEXT NOT NULL,
                transcript_hash       TEXT NOT NULL,
                confidence_score      INTEGER,
                risk_score            INTEGER,
                growth_drivers        TEXT,
                management_confidence TEXT,
                risks                 TEXT,
                guidance              TEXT,
                narrative_shift       TEXT,
                strategic_implications TEXT,
                full_output           TEXT,
                analyst_notes         TEXT DEFAULT '',
                created_at            TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Migration: add analyst_notes to existing databases
        try:
            conn.execute("ALTER TABLE analyses ADD COLUMN analyst_notes TEXT DEFAULT ''")
        except Exception:
            pass

        # Migration: deduplicate existing rows — keep only the most recent per company+quarter
        # This runs safely even if there are no duplicates
        try:
            conn.execute("""
                DELETE FROM analyses
                WHERE id NOT IN (
                    SELECT MAX(id)
                    FROM analyses
                    GROUP BY company, quarter
                )
            """)
        except Exception:
            pass

        conn.execute("""
            CREATE TABLE IF NOT EXISTS comparisons (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                comparison_hash TEXT NOT NULL UNIQUE,
                label_a         TEXT NOT NULL,
                label_b         TEXT NOT NULL,
                result_json     TEXT NOT NULL,
                created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()


def hash_transcript(text: str) -> str:
    return hashlib.md5(text.encode()).hexdigest()


def analysis_exists(transcript_hash: str) -> bool:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id FROM analyses WHERE transcript_hash = ?",
            (transcript_hash,)
        ).fetchone()
    return row is not None


def save_analysis(
    company: str,
    quarter: str,
    transcript: str,
    parsed: dict,
    full_output: str,
) -> int:
    """
    Persist a completed analysis. Returns the row id.
    If a row for this company+quarter already exists, updates it (upsert).
    This prevents duplicate rows from slightly different transcript text.
    """
    tx_hash = hash_transcript(transcript)

    with get_connection() as conn:
        # Check if this company+quarter already has a row
        existing = conn.execute(
            "SELECT id, analyst_notes FROM analyses WHERE company = ? AND quarter = ?",
            (company, quarter),
        ).fetchone()

        if existing:
            # Update in place — preserve analyst notes
            conn.execute(
                """
                UPDATE analyses SET
                    transcript_hash       = ?,
                    confidence_score      = ?,
                    risk_score            = ?,
                    growth_drivers        = ?,
                    management_confidence = ?,
                    risks                 = ?,
                    guidance              = ?,
                    narrative_shift       = ?,
                    strategic_implications = ?,
                    full_output           = ?,
                    created_at            = ?
                WHERE id = ?
                """,
                (
                    tx_hash,
                    parsed.get("confidence_score"),
                    parsed.get("risk_score"),
                    json.dumps(parsed.get("growth_drivers", [])),
                    json.dumps(parsed.get("management_confidence_signals", [])),
                    json.dumps(parsed.get("risks", [])),
                    parsed.get("guidance", ""),
                    parsed.get("narrative_shift"),
                    json.dumps(parsed.get("strategic_implications", [])),
                    full_output,
                    datetime.utcnow().isoformat(),
                    existing["id"],
                ),
            )
            conn.commit()
            return existing["id"]
        else:
            cursor = conn.execute(
                """
                INSERT INTO analyses (
                    company, quarter, transcript_hash,
                    confidence_score, risk_score,
                    growth_drivers, management_confidence,
                    risks, guidance, narrative_shift,
                    strategic_implications, full_output,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    company,
                    quarter,
                    tx_hash,
                    parsed.get("confidence_score"),
                    parsed.get("risk_score"),
                    json.dumps(parsed.get("growth_drivers", [])),
                    json.dumps(parsed.get("management_confidence_signals", [])),
                    json.dumps(parsed.get("risks", [])),
                    parsed.get("guidance", ""),
                    parsed.get("narrative_shift"),
                    json.dumps(parsed.get("strategic_implications", [])),
                    full_output,
                    datetime.utcnow().isoformat(),
                ),
            )
            conn.commit()
            return cursor.lastrowid
        conn.commit()
        return cursor.lastrowid


def get_all_analyses(company: str = None) -> List[Dict]:
    """Return analyses, one row per company+quarter (most recent), ordered by quarter."""
    with get_connection() as conn:
        if company:
            rows = conn.execute(
                """
                SELECT * FROM analyses
                WHERE id IN (
                    SELECT MAX(id) FROM analyses
                    WHERE company = ?
                    GROUP BY company, quarter
                )
                ORDER BY quarter ASC
                """,
                (company,),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT * FROM analyses
                WHERE id IN (
                    SELECT MAX(id) FROM analyses
                    GROUP BY company, quarter
                )
                ORDER BY company ASC, quarter ASC
                """
            ).fetchall()
    return [dict(r) for r in rows]


def get_companies() -> List[str]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT DISTINCT company FROM analyses ORDER BY company ASC"
        ).fetchall()
    return [r["company"] for r in rows]


def get_analysis_by_id(row_id: int) -> Optional[Dict]:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM analyses WHERE id = ?", (row_id,)
        ).fetchone()
    return dict(row) if row else None


def delete_analysis(row_id: int) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM analyses WHERE id = ?", (row_id,))
        conn.commit()


def get_analysis_count() -> int:
    with get_connection() as conn:
        row = conn.execute("SELECT COUNT(*) as cnt FROM analyses").fetchone()
    return row["cnt"]


def get_trend_data(company: str) -> List[Dict]:
    """
    Return time-series data for a company's trend charts.
    Each row has: quarter, confidence_score, risk_score,
                  growth_drivers (parsed), risks (parsed).
    """
    rows = get_all_analyses(company)
    result = []
    for r in rows:
        result.append({
            "quarter":          r["quarter"],
            "confidence_score": r["confidence_score"],
            "risk_score":       r["risk_score"],
            "growth_drivers":   json.loads(r["growth_drivers"] or "[]"),
            "risks":            json.loads(r["risks"] or "[]"),
            "management_confidence": json.loads(r["management_confidence"] or "[]"),
            "strategic_implications": json.loads(r["strategic_implications"] or "[]"),
            "guidance":         r["guidance"],
            "narrative_shift":  r["narrative_shift"],
            "created_at":       r["created_at"],
        })
    return result


# ── Analyst notes ─────────────────────────────────────────────────────────────

def save_notes(row_id: int, notes: str) -> None:
    with get_connection() as conn:
        conn.execute(
            "UPDATE analyses SET analyst_notes = ? WHERE id = ?",
            (notes, row_id),
        )
        conn.commit()


def load_notes(row_id: int) -> str:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT analyst_notes FROM analyses WHERE id = ?", (row_id,)
        ).fetchone()
    return row["analyst_notes"] or "" if row else ""


def get_analysis_by_company_quarter(company: str, quarter: str) -> Optional[Dict]:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM analyses WHERE company = ? AND quarter = ? ORDER BY created_at DESC LIMIT 1",
            (company, quarter),
        ).fetchone()
    return dict(row) if row else None


# ── Comparison persistence ────────────────────────────────────────────────────

def make_comparison_hash(label_a: str, label_b: str) -> str:
    """
    Order-independent hash so A vs B and B vs A return the same cached result.
    """
    key = "|".join(sorted([label_a, label_b]))
    return hashlib.md5(key.encode()).hexdigest()


def save_comparison(label_a: str, label_b: str, result: dict) -> None:
    """Store a comparison result. Uses INSERT OR REPLACE to update if re-run."""
    h = make_comparison_hash(label_a, label_b)
    with get_connection() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO comparisons
                (comparison_hash, label_a, label_b, result_json, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (h, label_a, label_b, json.dumps(result), datetime.utcnow().isoformat()),
        )
        conn.commit()


def load_comparison(label_a: str, label_b: str) -> Optional[dict]:
    """Return a cached comparison result or None if not found."""
    h = make_comparison_hash(label_a, label_b)
    with get_connection() as conn:
        row = conn.execute(
            "SELECT result_json FROM comparisons WHERE comparison_hash = ?", (h,)
        ).fetchone()
    return json.loads(row["result_json"]) if row else None


def get_all_comparisons() -> List[Dict]:
    """Return all stored comparisons ordered by most recent."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id, label_a, label_b, created_at FROM comparisons ORDER BY created_at DESC"
        ).fetchall()
    return [dict(r) for r in rows]


def delete_comparison(comparison_id: int) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM comparisons WHERE id = ?", (comparison_id,))
        conn.commit()


def reset_database() -> None:
    """Drop and recreate all tables. Used for demo resets."""
    with get_connection() as conn:
        conn.execute("DROP TABLE IF EXISTS analyses")
        conn.execute("DROP TABLE IF EXISTS comparisons")
        conn.commit()
    init_db()
