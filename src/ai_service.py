"""Backward-compatible AI analysis facade."""

from services.ai_pipeline import analyze_warranty_claim


def analyze_service_request(coverage_details: str, exclusions: str, issue_description: str) -> dict:
    """Return the legacy verdict shape from the upgraded AI pipeline."""
    product = {
        "id": 0,
        "serial_number": "",
        "product_name": "Product",
        "category": "General",
        "warranty_template_id": 0,
        "coverage_details": coverage_details,
        "exclusions": exclusions,
        "conditions": "Valid proof of purchase required.",
    }
    explanation = analyze_warranty_claim(product, issue_description)
    return {
        "verdict": explanation.coverage_status,
        "explanation": explanation.reasoning,
        "missing_proof_checklist": explanation.missing_documents,
    }
