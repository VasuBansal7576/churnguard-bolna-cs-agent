"""Health score extraction — Bolna native extraction + OpenAI fallback."""

import os
import json
import logging
from typing import Optional
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

# Bolna status → ChurnGuard status mapping
BOLNA_STATUS_MAP = {
    # Pre-call
    "scheduled": "scheduled",
    "queued": "scheduled",
    "rescheduled": "scheduled",
    # In-progress
    "initiated": "in_call",
    "ringing": "in_call",
    "in-progress": "in_call",
    "call-disconnected": "failed",
    # Terminal — success
    "completed": "completed",
    # Terminal — failure
    "busy": "failed",
    "no-answer": "failed",
    "canceled": "failed",
    "failed": "failed",
    "stopped": "failed",
    "error": "failed",
    "balance-low": "failed",
}

TERMINAL_STATUSES = {
    "completed", "busy", "no-answer", "canceled",
    "failed", "stopped", "error", "balance-low", "call-disconnected"
}

EXTRACTION_PROMPT = """You are analyzing a customer success call transcript.
Extract the following as JSON only — no other text, no markdown, no preamble:

{{
  "health_score": <integer 0-100>,
  "risk_label": "<Healthy|Monitor|At-Risk>",
  "key_blocker": "<one sentence or null>",
  "sentiment": "<positive|neutral|frustrated>",
  "recommendation": "<escalate|monitor|healthy>"
}}

Scoring:
- 70-100: Customer is adopting the product, no major blockers → Healthy
- 40-69: Some friction but not churning → Monitor
- 0-39: Blockers, frustration, or stated intent to cancel → At-Risk

Transcript:
{transcript}"""


def parse_bolna_extraction(extracted_data: Optional[dict]) -> dict:
    """
    Parse Bolna's extracted_data into our health score format.
    Values from Bolna extraction are strings — parse health_score to int.
    """
    if not extracted_data:
        return {
            "health_score": None,
            "risk_label": None,
            "key_blocker": None,
            "sentiment": None,
            "recommendation": None
        }

    try:
        raw_score = extracted_data.get("health_score")
        score = int(raw_score) if raw_score is not None else None
        # Clamp to 0-100
        if score is not None:
            score = max(0, min(100, score))
    except (ValueError, TypeError):
        score = None

    blocker = extracted_data.get("key_blocker")
    if blocker and blocker.lower() in ("none", "null", "n/a", ""):
        blocker = None

    return {
        "health_score": score,
        "risk_label": extracted_data.get("risk_label"),
        "key_blocker": blocker,
        "sentiment": extracted_data.get("sentiment"),
        "recommendation": extracted_data.get("recommendation")
    }


async def llm_extract_health(transcript: str) -> dict:
    """
    Fallback: Call OpenAI GPT-4o-mini to extract health score from transcript.
    Returns the same dict shape as parse_bolna_extraction.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.warning("OPENAI_API_KEY not set — using rule-based extraction")
        return rule_based_extract_health(transcript)

    try:
        client = AsyncOpenAI(api_key=api_key)
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a data extraction assistant. Return only valid JSON."},
                {"role": "user", "content": EXTRACTION_PROMPT.format(transcript=transcript)}
            ],
            temperature=0.1,
            max_tokens=200
        )

        raw = response.choices[0].message.content.strip()

        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
            if raw.endswith("```"):
                raw = raw[:-3]
            raw = raw.strip()

        data = json.loads(raw)
        return parse_bolna_extraction(data)

    except Exception as e:
        logger.error(f"LLM extraction failed: {e}")
        return rule_based_extract_health(transcript)


def rule_based_extract_health(transcript: str) -> dict:
    """Deterministic fallback for demos when no LLM key is configured."""
    text = transcript.lower()
    cancel_signals = ("cancel", "churn", "not keep", "won't keep", "might cancel")
    blocker_signals = ("stuck", "unclear", "confusing", "couldn't", "cannot", "can't", "not solved", "issue", "problem", "blocked")

    has_cancel = any(signal in text for signal in cancel_signals)
    has_blocker = any(signal in text for signal in blocker_signals)

    if has_cancel:
        return {
            "health_score": 25,
            "risk_label": "At-Risk",
            "key_blocker": "Customer expressed cancellation risk and mentioned a setup/account connection blocker.",
            "sentiment": "frustrated",
            "recommendation": "escalate"
        }

    if has_blocker:
        return {
            "health_score": 55,
            "risk_label": "Monitor",
            "key_blocker": "Customer mentioned friction or confusion that may reduce adoption.",
            "sentiment": "neutral",
            "recommendation": "monitor"
        }

    return {
        "health_score": 85,
        "risk_label": "Healthy",
        "key_blocker": None,
        "sentiment": "positive",
        "recommendation": "healthy"
    }


def map_bolna_status(bolna_status: str) -> str:
    """Map a Bolna call status to our simplified status enum."""
    return BOLNA_STATUS_MAP.get(bolna_status, "failed")


def is_terminal_status(bolna_status: str) -> bool:
    """Check if a Bolna status is terminal (call is done)."""
    return bolna_status in TERMINAL_STATUSES
