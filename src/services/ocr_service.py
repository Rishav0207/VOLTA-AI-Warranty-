"""OCR extraction and invoice parsing helpers."""

import re

from schemas.intelligence import OCRExtractionResponse


def extract_invoice_fields(text: str) -> OCRExtractionResponse:
    """Extract invoice metadata from OCR text with transparent confidence scoring."""
    patterns = {
        "invoice_number": r"(?:invoice|inv)[\s#:.-]*([A-Z0-9-]{4,})",
        "purchase_date": r"(\d{4}-\d{2}-\d{2}|\d{2}[/-]\d{2}[/-]\d{4})",
        "seller": r"(?:seller|sold by|vendor)[:\s]+([A-Za-z0-9 &.,-]{3,80})",
        "serial_number": r"(?:serial|s/n|sn)[:\s#-]*([A-Z0-9-]{4,})",
        "model_number": r"(?:model)[:\s#-]*([A-Z0-9-]{3,})",
        "warranty_duration": r"(\d+\s*(?:month|months|year|years))\s*warranty",
        "gst_number": r"\b(\d{2}[A-Z]{5}\d{4}[A-Z][A-Z0-9]Z[A-Z0-9])\b",
        "customer_name": r"(?:customer|bill to)[:\s]+([A-Za-z .]{3,80})",
    }
    values: dict[str, str] = {}
    for field, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            values[field] = match.group(1).strip()
    price_match = re.search(r"(?:total|price|amount)[:\s]*(?:rs\.?|inr)?\s*([0-9,]+(?:\.\d{1,2})?)", text, re.IGNORECASE)
    price = float(price_match.group(1).replace(",", "")) if price_match else None
    confidence = min(100, 35 + len(values) * 8 + (8 if price is not None else 0))
    return OCRExtractionResponse(
        invoice_number=values.get("invoice_number"),
        purchase_date=values.get("purchase_date"),
        seller=values.get("seller"),
        serial_number=values.get("serial_number"),
        model_number=values.get("model_number"),
        warranty_duration=values.get("warranty_duration"),
        price=price,
        gst_number=values.get("gst_number"),
        customer_name=values.get("customer_name"),
        confidence_score=confidence,
        extracted_text=text,
        highlighted_fields=values,
    )
