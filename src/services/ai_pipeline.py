"""Retrieval-augmented warranty intelligence pipeline."""

import json
import math
import re
from collections import Counter

import requests

from config import get_settings
from database.connection import get_connection
from schemas.intelligence import AIExplanation, FraudSignal


def _tokenize(text: str) -> list[str]:
    """Tokenize text for deterministic local embeddings."""
    return re.findall(r"[a-z0-9]+", text.lower())


def _embedding_dict(text: str) -> dict[str, float]:
    """Build a sparse TF embedding that works offline."""
    tokens = _tokenize(text)
    counts = Counter(tokens)
    norm = math.sqrt(sum(value * value for value in counts.values())) or 1.0
    return {token: value / norm for token, value in counts.items()}


def build_clause_embedding(text: str) -> str:
    """Serialize a clause embedding for storage."""
    return json.dumps(_embedding_dict(text), sort_keys=True)


def _cosine(a: dict[str, float], b: dict[str, float]) -> float:
    """Return cosine similarity for sparse vectors."""
    return sum(weight * b.get(token, 0.0) for token, weight in a.items())


def retrieve_relevant_clauses(template_id: int, query: str, limit: int = 5) -> list[dict]:
    """Retrieve semantically relevant warranty clauses for a query."""
    query_vec = _embedding_dict(query)
    conn = get_connection()
    rows = conn.execute(
        "SELECT id, clause_type, clause_text, embedding FROM warranty_clauses WHERE template_id = ?",
        (template_id,),
    ).fetchall()
    conn.close()
    scored = []
    for row in rows:
        embedding = json.loads(row["embedding"] or "{}")
        scored.append({**dict(row), "score": _cosine(query_vec, embedding)})
    return sorted(scored, key=lambda item: item["score"], reverse=True)[:limit]


def analyze_warranty_claim(product: dict, issue_description: str, ocr_confidence: int = 85) -> AIExplanation:
    """Run retrieval, optional LLM reasoning, fraud scoring, and deterministic fallback."""
    clauses = retrieve_relevant_clauses(product["warranty_template_id"], issue_description)
    fraud_signals = detect_fraud_signals(product, issue_description)
    fallback = _rule_based_explanation(product, issue_description, clauses, fraud_signals, ocr_confidence)
    try:
        llm_result = _call_ollama(product, issue_description, clauses, fallback)
        return AIExplanation(**llm_result)
    except Exception:
        return fallback


def detect_fraud_signals(product: dict, issue_description: str) -> list[FraudSignal]:
    """Detect duplicate registrations, suspicious dates, and mismatch signals."""
    signals: list[FraudSignal] = []
    conn = get_connection()
    duplicate_serials = conn.execute(
        "SELECT COUNT(*) AS c FROM customer_products WHERE serial_number = ? AND deleted_at IS NULL",
        (product["serial_number"],),
    ).fetchone()["c"]
    duplicate_invoices = 0
    if product.get("invoice_number"):
        duplicate_invoices = conn.execute(
            "SELECT COUNT(*) AS c FROM customer_products WHERE invoice_number = ? AND deleted_at IS NULL",
            (product["invoice_number"],),
        ).fetchone()["c"]
    conn.close()
    if duplicate_serials > 1:
        signals.append(FraudSignal(code="DUPLICATE_SERIAL", severity="high", message="Serial number appears on more than one registration."))
    if duplicate_invoices > 1:
        signals.append(FraudSignal(code="DUPLICATE_INVOICE", severity="high", message="Invoice number is already attached to another product."))
    if re.search(r"\b(edit|edited|photoshop|tamper|fake)\b", issue_description.lower()):
        signals.append(FraudSignal(code="DOCUMENT_TAMPER_HINT", severity="medium", message="Claim text contains terms that require document authenticity review."))
    return signals


def _rule_based_explanation(product: dict, issue_description: str, clauses: list[dict], fraud_signals: list[FraudSignal], ocr_confidence: int) -> AIExplanation:
    """Create an explainable analysis without external services."""
    issue = issue_description.lower()
    exclusion_hits = [clause for clause in clauses if clause["clause_type"] == "exclusion" and any(token in issue for token in _tokenize(clause["clause_text"])[:5])]
    coverage_hits = [clause for clause in clauses if clause["clause_type"] == "coverage" and clause["score"] > 0]
    if exclusion_hits:
        status = "LIKELY_NOT_COVERED"
        probability = 24
        action = "Request proof documents and route to manual review before rejection."
    elif coverage_hits:
        status = "LIKELY_COVERED"
        probability = 78
        action = "Approve inspection and verify invoice, serial number, and product condition."
    else:
        status = "NEEDS_INSPECTION"
        probability = 52
        action = "Schedule diagnostic inspection and collect missing proof."
    fraud_score = min(100, len(fraud_signals) * 30)
    confidence = max(20, min(95, int((ocr_confidence * 0.25) + (max([c["score"] for c in clauses] or [0]) * 60) + 35 - fraud_score * 0.2)))
    age_hint = "Plan preventive maintenance before warranty expiry." if product.get("warranty_end") else "Keep invoice and serial proof ready."
    return AIExplanation(
        coverage_status=status,
        confidence_score=confidence,
        relevant_warranty_clauses=[clause["clause_text"] for clause in clauses],
        reasoning=f"The claim was compared against retrieved {product['product_name']} warranty clauses. Coverage and exclusion matches drive the provisional status.",
        applicable_conditions=[product.get("conditions") or "Valid invoice and matching serial number are required."],
        missing_documents=["Original purchase invoice", "Serial number photo", "Issue photos or diagnostic video"],
        recommended_next_action=action,
        estimated_approval_probability=max(0, probability - fraud_score),
        fraud_risk_score=fraud_score,
        fraud_signals=fraud_signals,
        predictive_insights=[f"{product['category']} claims commonly require early inspection when symptoms recur.", age_hint],
        maintenance_advice=maintenance_advice(product),
    )


def _call_ollama(product: dict, issue_description: str, clauses: list[dict], fallback: AIExplanation) -> dict:
    """Ask Ollama for a strict JSON explanation using retrieved clauses."""
    settings = get_settings()
    prompt = {
        "product": product["product_name"],
        "issue": issue_description,
        "retrieved_clauses": [{k: c[k] for k in ("clause_type", "clause_text", "score")} for c in clauses],
        "fallback_json_contract": fallback.model_dump(),
    }
    response = requests.post(
        f"{settings.ollama_host}/api/chat",
        json={
            "model": settings.ollama_model,
            "messages": [
                {"role": "system", "content": "Return only JSON matching the provided fallback_json_contract keys. Be conservative and explainable."},
                {"role": "user", "content": json.dumps(prompt)},
            ],
            "stream": False,
            "format": "json",
            "options": {"temperature": 0.1},
        },
        timeout=2,
    )
    response.raise_for_status()
    raw = response.json()["message"]["content"]
    return json.loads(re.search(r"\{.*\}", raw, re.DOTALL).group(0))


def maintenance_advice(product: dict) -> list[str]:
    """Generate product-aware maintenance recommendations."""
    category = (product.get("category") or "").lower()
    name = product.get("product_name") or product.get("name") or "Product"
    if "appliance" in category:
        return [f"Inspect {name} power, drainage, and ventilation monthly.", "Use authorized service to preserve warranty eligibility."]
    return [f"Keep {name} firmware, thermal vents, and accessories in good condition.", "Back up issue evidence before service handoff."]


def semantic_search(query: str, limit: int = 10) -> list[dict]:
    """Search products, registered assets, claims, and clauses semantically."""
    query_vec = _embedding_dict(query)
    conn = get_connection()
    rows = []
    rows.extend(
        {
            "entity_type": "product",
            "entity_id": row["id"],
            "title": row["name"],
            "snippet": f"{row['category']} {row['model_number']}",
            "text": f"{row['name']} {row['category']} {row['model_number']}",
        }
        for row in conn.execute("SELECT * FROM products WHERE deleted_at IS NULL").fetchall()
    )
    rows.extend(
        {
            "entity_type": "claim",
            "entity_id": row["id"],
            "title": f"Claim #{row['id']} {row['status']}",
            "snippet": row["issue_description"],
            "text": f"{row['issue_description']} {row['ai_analysis'] or ''}",
        }
        for row in conn.execute("SELECT * FROM service_requests WHERE deleted_at IS NULL").fetchall()
    )
    rows.extend(
        {
            "entity_type": "clause",
            "entity_id": row["id"],
            "title": row["clause_type"].title(),
            "snippet": row["clause_text"],
            "text": row["clause_text"],
        }
        for row in conn.execute("SELECT * FROM warranty_clauses").fetchall()
    )
    conn.close()
    results = []
    for row in rows:
        score = _cosine(query_vec, _embedding_dict(row.pop("text")))
        if score > 0:
            results.append({**row, "score": round(score, 4)})
    return sorted(results, key=lambda item: item["score"], reverse=True)[:limit]
