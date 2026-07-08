"""Tests for the deterministic AI and OCR pipeline."""

from services.ocr_service import extract_invoice_fields


def test_invoice_extraction_detects_key_fields() -> None:
    """OCR parser extracts the fields the UI highlights."""
    text = """
    Invoice: INV-2026-7788
    Seller: Company X Store
    Model: LP-14P
    Serial: SN-LAP-1001
    Total: INR 68,999.00
    12 months warranty
    GST: 29ABCDE1234F1Z5
    Customer: Rishav Sinha
    """
    result = extract_invoice_fields(text)
    assert result.invoice_number == "INV-2026-7788"
    assert result.model_number == "LP-14P"
    assert result.serial_number == "SN-LAP-1001"
    assert result.price == 68999.0
    assert result.confidence_score >= 80
