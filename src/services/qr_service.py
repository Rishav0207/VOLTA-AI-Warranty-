"""QR code token and SVG generation."""

import secrets

from schemas.intelligence import QRCodeResponse


def new_qr_token() -> str:
    """Return a URL-safe QR token."""
    return secrets.token_urlsafe(18)


def qr_svg(product_id: int, qr_token: str, base_url: str = "http://localhost:8000") -> QRCodeResponse:
    """Generate a scannable SVG using the `qrcode` package when available."""
    product_url = f"{base_url.rstrip('/')}/api/v1/qr/{qr_token}"
    try:
        import qrcode
        import qrcode.image.svg

        factory = qrcode.image.svg.SvgPathImage
        image = qrcode.make(product_url, image_factory=factory)
        svg = image.to_string(encoding="unicode")
    except Exception:
        svg = f"<svg xmlns='http://www.w3.org/2000/svg' width='256' height='256'><rect width='256' height='256' fill='white'/><text x='16' y='128' fill='black'>{qr_token}</text></svg>"
    return QRCodeResponse(product_id=product_id, qr_token=qr_token, product_url=product_url, qr_svg=svg)
