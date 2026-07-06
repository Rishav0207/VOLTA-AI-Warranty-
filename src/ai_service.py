"""
Given a product's warranty coverage/exclusion text and a customer's issue
description, asks a local LLM (via Ollama) whether the issue is likely
covered. Falls back to a rule-based guess if Ollama isn't running.

Setup:
    1. Install Ollama: https://ollama.com
    2. ollama pull llama3.1 (or any model you want)
    3. leave it running (listens on http://localhost:11434 by default)

Env vars (optional): OLLAMA_HOST, OLLAMA_MODEL
"""

import os
import json
import re

import requests

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.1")

SYSTEM_PROMPT = """You are a warranty analysis assistant for a consumer electronics/appliance company.
You will be given:
- The product's warranty coverage details
- The product's warranty exclusions
- A customer's reported issue

Analyze whether the described issue is LIKELY COVERED, LIKELY NOT COVERED,
or NEEDS INSPECTION (unclear from description alone).

You MUST respond with ONLY a single JSON object, and nothing else before or
after it (no preamble, no markdown code fences, no explanation outside the JSON).
Use exactly this format:
{
  "verdict": "LIKELY_COVERED" or "LIKELY_NOT_COVERED" or "NEEDS_INSPECTION",
  "explanation": "2-3 sentence plain-English explanation referencing the specific warranty clause that applies",
  "missing_proof_checklist": ["document 1", "document 2", "document 3"]
}"""


def analyze_service_request(coverage_details: str, exclusions: str, issue_description: str) -> dict:
    """Returns {verdict, explanation, missing_proof_checklist}."""
    try:
        return _call_ollama(coverage_details, exclusions, issue_description)
    except Exception as e:
        fallback = _fallback_analysis(coverage_details, exclusions, issue_description)
        fallback["explanation"] = (
            f"[Local LLM call failed ({e}), showing rule-based fallback instead] "
            + fallback["explanation"]
        )
        return fallback


def _call_ollama(coverage_details: str, exclusions: str, issue_description: str) -> dict:
    user_prompt = f"""Warranty coverage: {coverage_details}
Warranty exclusions: {exclusions}
Customer's reported issue: {issue_description}"""

    response = requests.post(
        f"{OLLAMA_HOST}/api/chat",
        json={
            "model": OLLAMA_MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            "stream": False,
            "format": "json",  # asks Ollama to constrain output to valid JSON
            "options": {"temperature": 0.2},
        },
        timeout=60,
    )
    response.raise_for_status()
    raw_text = response.json()["message"]["content"].strip()

    return _parse_llm_json(raw_text)


def _parse_llm_json(raw_text: str) -> dict:
    """Local models don't always stick to 'JSON only' even with format=json,
    so this strips code fences/stray text and grabs the first {...} block."""
    cleaned = raw_text.replace("```json", "").replace("```", "").strip()

    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON object found in model output: {cleaned[:200]}")

    result = json.loads(match.group(0))

    required_keys = {"verdict", "explanation", "missing_proof_checklist"}
    if not required_keys.issubset(result.keys()):
        raise ValueError(f"Model JSON missing required keys: {result}")

    if result["verdict"] not in {"LIKELY_COVERED", "LIKELY_NOT_COVERED", "NEEDS_INSPECTION"}:
        result["verdict"] = "NEEDS_INSPECTION"

    if not isinstance(result["missing_proof_checklist"], list):
        result["missing_proof_checklist"] = [str(result["missing_proof_checklist"])]

    return result


def _fallback_analysis(coverage_details: str, exclusions: str, issue_description: str) -> dict:
    """Basic keyword match so the app still works if Ollama is down. Doesn't
    understand negation ("no water damage" still matches "water damage") —
    good enough to keep things running, not a real substitute for Ollama."""
    issue_lower = issue_description.lower()
    exclusion_keywords = ["physical damage", "water damage", "accidental", "misuse",
                           "unauthorized", "liquid", "spill", "crack", "dent", "rust"]

    hit = next((kw for kw in exclusion_keywords if kw in issue_lower), None)

    if hit:
        verdict = "LIKELY_NOT_COVERED"
        explanation = (
            f"The issue description mentions '{hit}', which matches an exclusion in this "
            f"product's warranty terms. This is a rule-based fallback estimate, not a final decision."
        )
    else:
        verdict = "NEEDS_INSPECTION"
        explanation = (
            "Based on keywords alone we can't confidently classify this issue. "
            "A technician should inspect the product against the warranty's coverage terms."
        )

    return {
        "verdict": verdict,
        "explanation": explanation,
        "missing_proof_checklist": [
            "Original purchase invoice",
            "Product serial number photo",
            "Photos/video of the reported issue",
        ],
    }
