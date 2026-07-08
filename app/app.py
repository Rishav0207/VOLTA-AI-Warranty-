"""
Streamlit frontend for VOLTA.

Run with: streamlit run app.py
(make sure the backend is running first: uvicorn main:app --reload --port 8000)
"""

import base64
import html
import json
import requests
import streamlit as st
from datetime import date
from pathlib import Path

API_URL = "http://localhost:8000"

st.set_page_config(page_title="Volta - Smart Warranty Tracker", page_icon="🛠️", layout="wide")

# helper to inline images as base64 so the CSS can reference them
ASSETS_DIR = Path(__file__).parent / "assets"

def get_image_base64(filename):
    path = ASSETS_DIR / filename
    if path.exists():
        with open(path, "rb") as f:
            data = f.read()
        return f"data:image/png;base64,{base64.b64encode(data).decode()}"
    return ""

# preload the ones the CSS/sidebar need
tech_bg_base64 = get_image_base64("tech_bg.png")
logo_base64 = get_image_base64("volta_logo.png")

# --- custom CSS (liquid-glass look) ---
custom_css = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&display=swap');

/* theme vars */
:root {{
    color-scheme: dark;
    --app-overlay: rgba(4, 8, 14, 0.18);
    --app-overlay-strong: rgba(4, 8, 14, 0.28);
    --surface: rgba(255, 255, 255, 0.05);
    --surface-strong: rgba(255, 255, 255, 0.09);
    --surface-soft: rgba(255, 255, 255, 0.05);
    --text-primary: #f3f4f5;
    --text-secondary: #9a9da3;
    --text-muted: #7b7f86;
    --border-color: rgba(255, 255, 255, 0.09);
    --border-color-strong: rgba(255, 255, 255, 0.16);
    --sheen: rgba(255, 255, 255, 0.10);
    --accent: #aab3bd;
    --accent-strong: #7c8590;
    --glass-blur: blur(28px) saturate(150%);
    --glass-shadow: 0 20px 45px -12px rgba(0, 0, 0, 0.45), inset 0 1px 0 rgba(255, 255, 255, 0.08), inset 0 -1px 0 rgba(0, 0, 0, 0.25);
}}

div[data-testid="stAppViewBlockContainer"] {{
    padding-top: 2rem !important;
    padding-bottom: 3rem !important;
    max-width: 1280px !important;
}}

/* Global Reset & Background */
html, body, [data-testid="stAppViewContainer"], .stApp {{
    font-family: 'Outfit', sans-serif !important;
    background: linear-gradient(135deg, var(--app-overlay), var(--app-overlay-strong)),
                url('{tech_bg_base64}') no-repeat center center fixed !important;
    background-size: cover !important;
    color: var(--text-primary) !important;
    transition: background-color 0.35s ease, color 0.35s ease, border-color 0.35s ease, box-shadow 0.35s ease !important;
}}

/* Header Typography */
h1, h2, h3, h4, h5, h6 {{
    font-family: 'Outfit', sans-serif !important;
    color: var(--text-primary) !important;
    font-weight: 600 !important;
    letter-spacing: -0.015em !important;
}}

/* glass panel look for st.container(border=True) */
div[data-testid="stContainer"] {{
    position: relative !important;
    background: var(--surface) !important;
    backdrop-filter: var(--glass-blur) !important;
    -webkit-backdrop-filter: var(--glass-blur) !important;
    border: 1px solid var(--border-color) !important;
    border-radius: 20px !important;
    padding: 24px !important;
    box-shadow: var(--glass-shadow) !important;
    overflow: hidden !important;
    transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1) !important;
}}

div[data-testid="stContainer"]::before {{
    content: "" !important;
    position: absolute !important;
    inset: 0 !important;
    pointer-events: none !important;
    border-radius: 20px !important;
    background: linear-gradient(155deg, var(--sheen) 0%, rgba(255, 255, 255, 0) 32%) !important;
    mix-blend-mode: overlay !important;
}}

/* Remove margins/borders from forms inside glass containers to merge seamlessly */
div[data-testid="stContainer"] div[data-testid="stForm"] {{
    border: none !important;
    background: transparent !important;
    box-shadow: none !important;
    padding: 0 !important;
    margin: 0 !important;
}}

/* Custom Input Field Styling */
div[data-testid="stTextInput"] input, 
div[data-testid="stTextArea"] textarea,
div[data-testid="stNumberInput"] input,
div[data-testid="stDateInput"] input {{
    background-color: var(--surface-strong) !important;
    border: 1px solid var(--border-color) !important;
    color: var(--text-primary) !important;
    border-radius: 10px !important;
    padding: 10px 14px !important;
    font-family: 'Outfit', sans-serif !important;
    transition: all 0.3s ease !important;
}}

div[data-testid="stTextInput"] input:focus, 
div[data-testid="stTextArea"] textarea:focus,
div[data-testid="stNumberInput"] input:focus {{
    border-color: #aab3bd !important;
    box-shadow: 0 0 10px rgba(170, 179, 189, 0.25) !important;
    outline: none !important;
}}

/* Input Labels */
div[data-testid="stTextInput"] label, 
div[data-testid="stTextArea"] label, 
div[data-testid="stDateInput"] label,
div[data-testid="stSelectbox"] label {{
    font-size: 0.88rem !important;
    color: var(--text-secondary) !important;
    font-weight: 500 !important;
    margin-bottom: 6px !important;
}}

/* Input Icons injection */
div[data-testid="stTextInput"]:has(input[type="password"]) input {{
    background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="%2394a3b8" viewBox="0 0 16 16"><path d="M8 1a2 2 0 0 1 2 2v4H6V3a2 2 0 0 1 2-2zm3 6V3a3 3 0 0 0-6 0v4a2 2 0 0 0-2 2v5a2 2 0 0 0 2 2h6a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2zM5 8h6a1 1 0 0 1 1 1v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V9a1 1 0 0 1 1-1z"/></svg>') !important;
    background-repeat: no-repeat !important;
    background-position: 14px center !important;
    padding-left: 42px !important;
}}

div[data-testid="stTextInput"]:not(:has(input[type="password"])) input {{
    background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="%2394a3b8" viewBox="0 0 16 16"><path d="M3 14s-1 0-1-1 1-4 6-4 6 3 6 4-1 1-1 1zm5-6a3 3 0 1 0 0-6 3 3 0 0 0 0 6z"/></svg>') !important;
    background-repeat: no-repeat !important;
    background-position: 14px center !important;
    padding-left: 42px !important;
}}

/* Standard Selectbox overlay */
div[data-testid="stSelectbox"] [data-baseweb="select"] > div {{
    background-color: var(--surface-strong) !important;
    border: 1px solid var(--border-color) !important;
    border-radius: 10px !important;
    color: var(--text-primary) !important;
}}

/* default buttons */
div[data-testid="stButton"] button {{
    position: relative !important;
    background: rgba(255, 255, 255, 0.05) !important;
    backdrop-filter: blur(16px) saturate(140%) !important;
    -webkit-backdrop-filter: blur(16px) saturate(140%) !important;
    color: var(--text-primary) !important;
    border: 1px solid var(--border-color-strong) !important;
    border-radius: 12px !important;
    padding: 8px 20px !important;
    font-family: 'Outfit', sans-serif !important;
    font-weight: 500 !important;
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.08) !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
}}

div[data-testid="stButton"] button:hover {{
    background: rgba(170, 179, 189, 0.12) !important;
    border-color: #aab3bd !important;
    box-shadow: 0 0 18px rgba(170, 179, 189, 0.18), inset 0 1px 0 rgba(255, 255, 255, 0.12) !important;
    color: #aab3bd !important;
    transform: translateY(-1px) !important;
}}

/* primary buttons (forms + register CTA) */
div[data-testid="stForm"] div[data-testid="stButton"] button,
button[key*="register_action_btn"] {{
    background: linear-gradient(155deg, rgba(255, 255, 255, 0.16) 0%, rgba(170, 179, 189, 0.95) 4%, #9099a3 55%, #7c8590 100%) !important;
    color: #101113 !important;
    border: 1px solid rgba(255, 255, 255, 0.25) !important;
    font-weight: 600 !important;
    box-shadow: 0 8px 22px -6px rgba(0, 0, 0, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.35) !important;
}}

div[data-testid="stForm"] div[data-testid="stButton"] button:hover,
button[key*="register_action_btn"]:hover {{
    box-shadow: 0 10px 26px -6px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.45) !important;
    transform: translateY(-1px) !important;
    color: #101113 !important;
}}

/* Glass Tabs Control */
button[data-baseweb="tab"] {{
    color: #9a9da3 !important;
    font-family: 'Outfit', sans-serif !important;
    font-weight: 500 !important;
    background: transparent !important;
    border-bottom: 2px solid transparent !important;
}}
button[aria-selected="true"] {{
    color: #aab3bd !important;
    border-bottom-color: #aab3bd !important;
}}

/* sidebar */
section[data-testid="stSidebar"] {{
    background-color: rgba(18, 18, 20, 0.68) !important;
    backdrop-filter: blur(32px) saturate(140%) !important;
    -webkit-backdrop-filter: blur(32px) saturate(140%) !important;
    border-right: 1px solid rgba(255, 255, 255, 0.06) !important;
    box-shadow: inset -1px 0 0 rgba(255, 255, 255, 0.04) !important;
}}

/* Navigation item vertical lists (accessible tabs layout) */
.nav-item button {{
    background: transparent !important;
    color: #9a9da3 !important;
    border: none !important;
    border-radius: 8px !important;
    text-align: left !important;
    justify-content: flex-start !important;
    padding: 12px 16px !important;
    font-size: 0.95rem !important;
    font-weight: 500 !important;
    transition: all 0.2s ease !important;
    box-shadow: none !important;
    margin-bottom: 4px !important;
}}

.nav-item button:hover {{
    background: rgba(255, 255, 255, 0.04) !important;
    color: #ffffff !important;
    border: none !important;
    box-shadow: none !important;
}}

.nav-item.active button {{
    background: rgba(170, 179, 189, 0.1) !important;
    color: #aab3bd !important;
    border-left: 3px solid #aab3bd !important;
    border-radius: 0 8px 8px 0 !important;
    font-weight: 600 !important;
    box-shadow: none !important;
}}

/* Sign Out button wrapper */
.signout-btn-wrapper button {{
    background: rgba(185, 140, 133, 0.06) !important;
    color: #b98c85 !important;
    border: 1px solid rgba(185, 140, 133, 0.15) !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    transition: all 0.2s ease !important;
}}

.signout-btn-wrapper button:hover {{
    background: rgba(185, 140, 133, 0.14) !important;
    border-color: #b98c85 !important;
    box-shadow: 0 0 12px rgba(185, 140, 133, 0.2) !important;
    color: #b98c85 !important;
}}

/* metrics */
div[data-testid="stMetricValue"] {{
    font-size: 2.1rem !important;
    font-weight: 700 !important;
    color: #aab3bd !important;
    font-family: 'Outfit', sans-serif !important;
}}
div[data-testid="stMetricLabel"] {{
    color: #9a9da3 !important;
    font-family: 'Outfit', sans-serif !important;
    text-transform: uppercase !important;
    font-size: 0.72rem !important;
    letter-spacing: 0.05em !important;
}}
div[data-testid="stMetric"] {{
    background: linear-gradient(145deg, rgba(255, 255, 255, 0.075), rgba(255, 255, 255, 0.035)) !important;
    backdrop-filter: blur(14px) saturate(130%) !important;
    -webkit-backdrop-filter: blur(14px) saturate(130%) !important;
    border: 1px solid var(--border-color) !important;
    border-radius: 12px !important;
    min-height: 104px !important;
    padding: 14px 20px !important;
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.05) !important;
}}

/* expanders */
div[data-testid="stExpander"] {{
    background: linear-gradient(145deg, rgba(255, 255, 255, 0.055), rgba(255, 255, 255, 0.028)) !important;
    backdrop-filter: blur(16px) saturate(130%) !important;
    -webkit-backdrop-filter: blur(16px) saturate(130%) !important;
    border: 1px solid var(--border-color) !important;
    border-radius: 12px !important;
    margin-bottom: 12px !important;
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.05) !important;
}}
div[data-testid="stExpander"] details {{
    border: none !important;
}}

/* Social SSO Button Wrappers */
.google-btn-wrapper button {{
    background-color: rgba(255, 255, 255, 0.04) !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    color: #e6e7e9 !important;
    background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="16" height="16"><path fill="%23EA4335" d="M5.266 9.765A7.077 7.077 0 0 1 12 4.909c1.69 0 3.218.6 4.418 1.582L19.91 3C17.782 1.145 15.055 0 12 0 7.33 0 3.327 2.68 1.386 6.614l3.88 3.151z"/><path fill="%23FBBC05" d="M1.386 6.614A7.042 7.042 0 0 0 1 12c0 1.926.4 3.757 1.127 5.417l3.99-3.1A7.02 7.02 0 0 1 5 12c0-1.57.385-3.055 1.055-4.364L1.386 6.614z"/><path fill="%234285F4" d="M12 19.091c-1.895 0-3.59-.727-4.873-1.927l-3.99 3.1C5.127 22.955 8.355 24 12 24c5.255 0 9.71-3.327 11.373-8.082l-4.527-3.509a7.077 7.077 0 0 1-6.846 6.682z"/><path fill="%2334A853" d="M23.373 15.918L24 12c0-.7-.082-1.4-.245-2.091H12v4.182h6.818c-.295 1.582-1.2 2.92-2.545 3.818l4.527 3.509c2.655-2.455 4.573-6.073 4.573-11.518z"/></svg>') !important;
    background-repeat: no-repeat !important;
    background-position: 20px center !important;
    padding-left: 45px !important;
}}

.ms-btn-wrapper button {{
    background-color: rgba(255, 255, 255, 0.04) !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    color: #e6e7e9 !important;
    background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 23 23" width="14" height="14"><path fill="%23f25022" d="M0 0h11v11H0z"/><path fill="%237fba00" d="M12 0h11v11H12z"/><path fill="%2300a4ef" d="M0 12h11v11H0z"/><path fill="%23ffb900" d="M12 12h11v11H12z"/></svg>') !important;
    background-repeat: no-repeat !important;
    background-position: 20px center !important;
    padding-left: 45px !important;
}}

/* Interactive Product Catalog Selection Cards */
div[data-testid="stContainer"]:has(.product-card.selected) {{
    border-color: #aab3bd !important;
    background: rgba(170, 179, 189, 0.06) !important;
    box-shadow: 0 0 20px rgba(170, 179, 189, 0.15) !important;
}}

div[data-testid="stContainer"]:has(.product-card):hover {{
    border-color: rgba(255, 255, 255, 0.22) !important;
    transform: translateY(-3px) !important;
    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.3) !important;
}}

/* Style the button inside container when selected */
div[data-testid="stContainer"]:has(.product-card.selected) button {{
    background-image: linear-gradient(135deg, #aab3bd, #7c8590) !important;
    color: #ffffff !important;
    font-weight: 600 !important;
    border: none !important;
    box-shadow: 0 4px 15px rgba(170, 179, 189, 0.25) !important;
}}

.product-img-container {{
    height: 120px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    margin-bottom: 12px !important;
    width: 100% !important;
}}

.product-img {{
    max-height: 100% !important;
    max-width: 100% !important;
    object-fit: contain !important;
    border-radius: 8px !important;
}}

.product-category {{
    font-size: 0.68rem !important;
    text-transform: uppercase !important;
    color: #9a9da3 !important;
    font-weight: 600 !important;
    letter-spacing: 0.1em !important;
}}

.product-title {{
    font-size: 0.98rem !important;
    color: #ffffff !important;
    font-weight: 500 !important;
}}

.product-meta {{
    font-size: 0.76rem !important;
    color: #7b7f86 !important;
}}

.product-price {{
    font-size: 1.15rem !important;
    color: #aab3bd !important;
    font-weight: 600 !important;
}}

/* Selection Banner Info */
.selected-product-banner {{
    background: rgba(170, 179, 189, 0.08) !important;
    border: 1px solid rgba(170, 179, 189, 0.18) !important;
    border-radius: 8px !important;
    padding: 12px 18px !important;
    margin-bottom: 15px !important;
    color: #e6e7e9 !important;
    font-size: 0.95rem !important;
}}

.page-kicker {{
    color: #aab3bd !important;
    font-size: 0.76rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.12em !important;
    font-weight: 700 !important;
    margin-bottom: 6px !important;
}}

.page-title {{
    margin: 0 !important;
    font-size: 1.9rem !important;
    font-weight: 760 !important;
    color: #ffffff !important;
}}

.page-subtitle {{
    color: #9a9da3 !important;
    font-size: 0.95rem !important;
    margin-top: 7px !important;
    max-width: 760px !important;
}}

.page-header {{
    margin-bottom: 22px !important;
    border-bottom: 1px solid rgba(255,255,255,0.08) !important;
    padding-bottom: 16px !important;
}}

.status-pill {{
    display: inline-flex !important;
    align-items: center !important;
    border-radius: 999px !important;
    padding: 4px 11px !important;
    font-size: 0.74rem !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.04em !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
}}

.ai-panel {{
    background: linear-gradient(145deg, rgba(255,255,255,0.07), rgba(0,0,0,0.12)) !important;
    border: 1px solid rgba(255,255,255,0.09) !important;
    border-left: 3px solid var(--panel-accent, #aab3bd) !important;
    border-radius: 10px !important;
    padding: 16px !important;
    margin-bottom: 14px !important;
}}

.ai-eyebrow {{
    font-size: 0.72rem !important;
    color: #9a9da3 !important;
    text-transform: uppercase !important;
    font-weight: 700 !important;
    letter-spacing: 0.08em !important;
}}

.ai-status {{
    color: #ffffff !important;
    font-size: 1.08rem !important;
    font-weight: 760 !important;
    margin-top: 4px !important;
}}

.ai-reason {{
    color: #d6d7da !important;
    font-size: 0.92rem !important;
    line-height: 1.55 !important;
    margin-top: 9px !important;
}}

.ai-next {{
    color: var(--panel-accent, #aab3bd) !important;
    font-size: 0.86rem !important;
    font-weight: 650 !important;
    margin-top: 12px !important;
}}

.empty-state {{
    border: 1px dashed rgba(255,255,255,0.14) !important;
    border-radius: 12px !important;
    padding: 28px !important;
    text-align: center !important;
    color: #9a9da3 !important;
    background: rgba(255,255,255,0.025) !important;
}}

.qr-shell svg {{
    width: 180px !important;
    height: 180px !important;
    background: #ffffff !important;
    border-radius: 10px !important;
    padding: 10px !important;
}}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# --- session state ---
if "token" not in st.session_state:
    st.session_state.token = None
    st.session_state.role = None
    st.session_state.full_name = None

if "current_page" not in st.session_state:
    st.session_state.current_page = "Register a Product"

if "selected_product_id" not in st.session_state:
    st.session_state.selected_product_id = None


def auth_headers():
    return {"Authorization": f"Bearer {st.session_state.token}"}


def logout():
    st.session_state.token = None
    st.session_state.role = None
    st.session_state.full_name = None
    st.session_state.selected_product_id = None
    st.session_state.current_page = "Register a Product"
    st.rerun()


def safe_text(value):
    """Escape dynamic text before placing it inside custom HTML."""
    return html.escape(str(value or ""))


def parse_ai_explanation(ticket):
    """Return the structured AI explanation from new or legacy API payloads."""
    if ticket.get("ai_explanation"):
        return ticket["ai_explanation"]
    raw = ticket.get("ai_analysis")
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {
                "coverage_status": "LEGACY_ANALYSIS",
                "confidence_score": 50,
                "relevant_warranty_clauses": [],
                "reasoning": raw,
                "applicable_conditions": [],
                "missing_documents": [],
                "recommended_next_action": "Review this claim manually.",
                "estimated_approval_probability": ticket.get("approval_probability", 50),
                "fraud_risk_score": ticket.get("fraud_score", 0),
                "fraud_signals": [],
                "predictive_insights": [],
                "maintenance_advice": [],
            }
    return {}


def render_score_bar(label, value, color="#aab3bd"):
    """Render a compact score bar that matches the existing visual style."""
    value = max(0, min(100, int(value or 0)))
    st.markdown(f"""
    <div style="margin-bottom: 12px;">
        <div style="display: flex; justify-content: space-between; color: #9a9da3; font-size: 0.82rem; margin-bottom: 6px;">
            <span>{safe_text(label)}</span><span style="color: {color}; font-weight: 700;">{value}%</span>
        </div>
        <div style="height: 8px; background: rgba(255,255,255,0.07); border-radius: 999px; overflow: hidden;">
            <div style="height: 100%; width: {value}%; background: {color}; border-radius: 999px;"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_page_header(title, subtitle, kicker="Volta Console"):
    """Render a consistent page header."""
    st.markdown(f"""
    <div class="page-header">
        <div class="page-kicker">{safe_text(kicker)}</div>
        <h2 class="page-title">{safe_text(title)}</h2>
        <div class="page-subtitle">{safe_text(subtitle)}</div>
    </div>
    """, unsafe_allow_html=True)


def render_empty_state(title, message):
    """Render a calm empty state instead of a bare info box."""
    st.markdown(f"""
    <div class="empty-state">
        <div style="font-weight: 720; color: #ffffff; margin-bottom: 6px;">{safe_text(title)}</div>
        <div>{safe_text(message)}</div>
    </div>
    """, unsafe_allow_html=True)


def render_status_pill(label, background, color):
    """Render a small status badge."""
    return (
        f'<span class="status-pill" style="background-color: {background}; color: {color};">'
        f"{safe_text(label)}</span>"
    )


def render_ai_analysis(ticket, accent="#aab3bd"):
    """Render the upgraded explainable warranty analysis."""
    ai = parse_ai_explanation(ticket)
    if not ai:
        st.info("AI analysis is not available for this ticket yet.")
        return

    status = safe_text(ai.get("coverage_status", "NEEDS_INSPECTION")).replace("_", " ")
    reasoning = safe_text(ai.get("reasoning", "No reasoning supplied."))
    next_action = safe_text(ai.get("recommended_next_action", "Review manually."))
    st.markdown(f"""
    <div class="ai-panel" style="--panel-accent: {accent};">
        <div class="ai-eyebrow">AI Coverage Status</div>
        <div class="ai-status">{status}</div>
        <div class="ai-reason">{reasoning}</div>
        <div class="ai-next">Next action: {next_action}</div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        render_score_bar("Confidence", ai.get("confidence_score", 0), "#aab3bd")
    with c2:
        render_score_bar("Approval Probability", ai.get("estimated_approval_probability", ticket.get("approval_probability", 0)), "#8fab97")
    with c3:
        render_score_bar("Fraud Risk", ai.get("fraud_risk_score", ticket.get("fraud_score", 0)), "#b98c85")

    clauses = ai.get("relevant_warranty_clauses") or []
    missing_docs = ai.get("missing_documents") or []
    conditions = ai.get("applicable_conditions") or []
    insights = ai.get("predictive_insights") or []
    advice = ai.get("maintenance_advice") or []
    fraud_signals = ai.get("fraud_signals") or []

    tab_clauses, tab_docs, tab_risk, tab_advice = st.tabs(["Clauses", "Documents", "Risk", "Advice"])
    with tab_clauses:
        if clauses:
            for clause in clauses[:5]:
                st.markdown(f"- {safe_text(clause)}")
        else:
            st.caption("No retrieved clauses were attached.")
        if conditions:
            st.markdown("**Applicable conditions**")
            for condition in conditions:
                st.markdown(f"- {safe_text(condition)}")
    with tab_docs:
        for doc in missing_docs or ["Original purchase invoice", "Serial number photo"]:
            st.markdown(f"- {safe_text(doc)}")
    with tab_risk:
        if fraud_signals:
            for signal in fraud_signals:
                st.warning(f"{signal.get('severity', 'risk').upper()}: {signal.get('message', '')}")
        else:
            st.success("No major fraud signals detected.")
    with tab_advice:
        for item in insights + advice:
            st.markdown(f"- {safe_text(item)}")


def render_warranty_health(health):
    """Render product warranty health if the backend provides it."""
    if not health:
        return
    score = int(health.get("score", 0))
    color = "#8fab97" if score >= 80 else "#c3ab7c" if score >= 55 else "#b98c85"
    render_score_bar(f"Warranty Health: {health.get('label', 'Unknown')}", score, color)
    st.caption(f"{health.get('remaining_days', 0)} days remaining. {health.get('service_recommendation', '')}")


# --- login / register screen ---
def show_login_page():
    # Spacing and layout centering
    _, col_center, _ = st.columns([1, 1.7, 1])

    with col_center:
        # Wrap everything in a single glass container card
        with st.container(border=True):
            st.markdown(f"""
            <div style="text-align: center; margin-top: 10px; margin-bottom: 20px;">
                <img src="{logo_base64}" style="width: 100px; margin-bottom: 12px;" />
                <h1 style="font-size: 2.2rem; font-weight: 800; margin: 0; color: #ffffff; letter-spacing: -0.02em;">VOLTA</h1>
                <p style="color: #9a9da3; font-size: 0.98rem; margin-top: 4px; font-weight: 400;">AI Warranty Intelligence Platform</p>
            </div>
            """, unsafe_allow_html=True)

            tab_login, tab_register = st.tabs(["🔒 Secure Sign In", "👤 Create Account"])

            with tab_login:
                with st.form("login_form", border=False):
                    username = st.text_input("Username", placeholder="Your username")
                    password = st.text_input("Password", type="password", placeholder="Your password")
                    submitted = st.form_submit_button("Sign In to Volta", use_container_width=True)

                    if submitted:
                        try:
                            resp = requests.post(
                                f"{API_URL}/auth/login",
                                json={"username": username, "password": password},
                                timeout=10,
                            )
                            if resp.status_code == 200:
                                data = resp.json()
                                st.session_state.token = data["access_token"]
                                st.session_state.role = data["role"]
                                st.session_state.full_name = data["full_name"]
                                st.session_state.current_page = "Register a Product"
                                st.rerun()
                            else:
                                st.error(resp.json().get("detail", "Login failed."))
                        except requests.exceptions.ConnectionError:
                            st.error("Cannot reach Volta core backend. Is uvicorn running on port 8000?")

                # Default credentials caption
                st.markdown("""
                <div style="text-align: center; margin-top: 10px; margin-bottom: 15px; font-size: 0.78rem; color: #7b7f86;">
                    Demo Admin Account: username <b>admin</b> / password <b>admin123</b>
                </div>
                """, unsafe_allow_html=True)

            with tab_register:
                with st.form("register_form", border=False):
                    full_name = st.text_input("Full name", placeholder="e.g. Jane Doe")
                    email = st.text_input("Email address", placeholder="e.g. jane@example.com")
                    new_username = st.text_input("Choose a username", placeholder="e.g. janedoe")
                    new_password = st.text_input("Choose a password", type="password", placeholder="Choose a secure password")
                    submitted = st.form_submit_button("Complete Registration", use_container_width=True)

                    if submitted:
                        if not full_name or not email or not new_username or not new_password:
                            st.error("All registration fields are required.")
                        else:
                            try:
                                resp = requests.post(
                                    f"{API_URL}/auth/register",
                                    json={
                                        "username": new_username,
                                        "password": new_password,
                                        "full_name": full_name,
                                        "email": email,
                                    },
                                    timeout=10,
                                )
                                if resp.status_code == 200:
                                    st.success("Account created successfully! Go back to the Sign In tab.")
                                else:
                                    st.error(resp.json().get("detail", "Registration failed."))
                            except requests.exceptions.ConnectionError:
                                st.error("Cannot reach Volta core backend. Is uvicorn running on port 8000?")


# --- customer dashboard ---
def show_customer_dashboard():
    # Sidebar profile box
    st.sidebar.markdown(f"""
    <div style="background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.06); border-radius: 16px; padding: 20px; margin-top: 15px; margin-bottom: 24px; text-align: center;">
        <img src="{logo_base64}" style="width: 58px; margin-bottom: 8px;" />
        <div style="font-weight: 700; color: #ffffff; font-size: 1.1rem; margin-top: 4px; letter-spacing: -0.01em;">{st.session_state.full_name}</div>
        <div style="color: #aab3bd; font-size: 0.78rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.08em; margin-top: 3px;">Customer Portal</div>
    </div>
    """, unsafe_allow_html=True)

    # Sidebar custom vertical navigation tabs
    st.sidebar.markdown("<div style='margin-bottom: 10px; font-size: 0.78rem; color: #7b7f86; text-transform: uppercase; letter-spacing: 0.05em; font-weight: 600;'>Navigation</div>", unsafe_allow_html=True)

    pages = {
        "Register a Product": "📥  Register a Product",
        "My Products": "📦  My Products",
        "Raise Service Request": "🛠️  Raise Service Request",
        "My Service Requests": "📋  My Service Requests"
    }

    for pkey, plabel in pages.items():
        is_active = (st.session_state.current_page == pkey)
        st.sidebar.markdown(f"<div class='nav-item {'active' if is_active else ''}'>", unsafe_allow_html=True)
        if st.sidebar.button(plabel, key=f"nav_btn_{pkey}", use_container_width=True):
            st.session_state.current_page = pkey
            st.rerun()
        st.sidebar.markdown("</div>", unsafe_allow_html=True)

    page = st.session_state.current_page
    
    st.sidebar.markdown("<br><hr style='border-color: rgba(255,255,255,0.05);'><br>", unsafe_allow_html=True)
    st.sidebar.markdown('<div class="signout-btn-wrapper">', unsafe_allow_html=True)
    if st.sidebar.button("Sign Out", use_container_width=True, key="sign_out_btn"):
        logout()
    st.sidebar.markdown('</div>', unsafe_allow_html=True)

    page_copy = {
        "Register a Product": "Select a product and attach purchase metadata for warranty tracking, QR access, and fraud checks.",
        "My Products": "Review protected devices, warranty health, QR access, and expiry posture.",
        "Raise Service Request": "Describe a product issue and get structured AI warranty intelligence before review.",
        "My Service Requests": "Track claim status, AI reasoning, required documents, and technician updates.",
    }
    render_page_header(page, page_copy.get(page, ""), "Customer Portal")

    if page == "Register a Product":
        # Get company products
        products_resp = requests.get(f"{API_URL}/products", headers=auth_headers())
        products = products_resp.json()

        # Display 3-column Grid
        cols = st.columns(3)
        img_map = {
            "WX-200": "washing_machine.png",
            "RF-450": "refrigerator.png",
            "ST-55": "smart_tv.png",
            "LP-14P": "laptop.png",
            "MW-30": "microwave.png"
        }

        for idx, p in enumerate(products):
            col = cols[idx % 3]
            is_selected = (st.session_state.selected_product_id == p["id"])
            img_filename = img_map.get(p["model_number"], "washing_machine.png")
            img_b64 = get_image_base64(img_filename)

            with col:
                with st.container(border=True):
                    st.markdown(f"""
                    <div class="product-card {'selected' if is_selected else ''}" style="text-align: center;">
                        <div class="product-img-container">
                            <img src="{img_b64}" class="product-img" />
                        </div>
                        <span class="product-category">{safe_text(p['category'])}</span>
                        <h4 class="product-title" style="margin: 6px 0; min-height: 48px; display: flex; align-items: center; justify-content: center;">{safe_text(p['name'])}</h4>
                        <div class="product-meta">Model: {safe_text(p['model_number'])}</div>
                        <div class="product-price" style="margin-top: 8px;">INR {p['price']:,.0f}</div>
                    </div>
                    """, unsafe_allow_html=True)

                    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
                    btn_label = "Selected ✓" if is_selected else "Select Product"
                    if st.button(btn_label, key=f"select_p_{p['id']}", use_container_width=True):
                        st.session_state.selected_product_id = p["id"]
                        st.rerun()

        # Show input fields below catalog in a clean container if a product is selected
        if st.session_state.selected_product_id is not None:
            selected_product = next((p for p in products if p["id"] == st.session_state.selected_product_id), None)
            if selected_product:
                st.markdown("<br>", unsafe_allow_html=True)
                with st.container(border=True):
                    st.markdown(f"""
                    <div style="margin-bottom: 18px;">
                        <h3 style="margin: 0; font-size: 1.25rem; font-weight: 700; color: #ffffff;">Register Selected Device</h3>
                        <p style="color: #9a9da3; font-size: 0.9rem; margin-top: 4px; margin-bottom: 0;">Provide purchase details for <b>{selected_product['name']} ({selected_product['model_number']})</b></p>
                    </div>
                    """, unsafe_allow_html=True)

                    with st.form("product_registration_form", border=False):
                        serial_number = st.text_input("Serial Number", placeholder="Found on product sticker/box")
                        purchase_date = st.date_input("Purchase Date", value=date.today(), max_value=date.today())
                        invoice_number = st.text_input("Invoice Number", placeholder="Optional, improves fraud checks")
                        seller = st.text_input("Seller / Store", placeholder="Optional, e.g. Company X Store")
                        gst_number = st.text_input("GST Number", placeholder="Optional invoice GSTIN")
                        submitted = st.form_submit_button("Complete Registration", use_container_width=True)

                        if submitted:
                            if not serial_number.strip():
                                st.error("Please enter a valid serial number.")
                            else:
                                resp = requests.post(
                                    f"{API_URL}/customer/register-product",
                                    headers=auth_headers(),
                                    json={
                                        "product_id": selected_product["id"],
                                        "serial_number": serial_number.strip(),
                                        "purchase_date": purchase_date.isoformat(),
                                        "invoice_number": invoice_number.strip() or None,
                                        "seller": seller.strip() or None,
                                        "gst_number": gst_number.strip() or None,
                                    },
                                )
                                if resp.status_code == 200:
                                    data = resp.json()
                                    st.success(f"Successfully Registered! Warranty active until {data['warranty_end']}.")
                                    st.session_state.selected_product_id = None
                                    st.rerun()
                                else:
                                    st.error(resp.json().get("detail", "Registration failed."))
        else:
            render_empty_state("Choose a product to continue", "Select any catalog card above to open the registration form.")

    elif page == "My Products":
        resp = requests.get(f"{API_URL}/customer/my-products", headers=auth_headers())
        products = resp.json()

        # Overview Metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Registered Devices", len(products))
        with col2:
            active_count = sum(1 for p in products if p["warranty_active"])
            st.metric("Protected Under Warranty", active_count)
        with col3:
            avg_health = round(sum((p.get("warranty_health") or {}).get("score", 0) for p in products) / len(products)) if products else 0
            st.metric("Avg Health Score", avg_health)

        st.markdown("<br>", unsafe_allow_html=True)

        if not products:
            render_empty_state("No products registered", "Register a device first to activate warranty intelligence and QR access.")
        else:
            for p in products:
                badge_color = "#8fab97" if p["warranty_active"] else "#b98c85"
                badge_bg = "rgba(143, 171, 151, 0.15)" if p["warranty_active"] else "rgba(185, 140, 133, 0.15)"
                status_label = "Active" if p["warranty_active"] else "Expired"
                
                with st.expander(f"{p['product_name']} - Serial: {p['serial_number']}"):
                    st.markdown(f"""
                    <div style="padding: 10px 0;">
                        <div style="margin-bottom: 8px;">
                            <span style="font-weight: 500; color: #9a9da3;">Status:</span>
                            {render_status_pill(status_label, badge_bg, badge_color)}
                        </div>
                        <div style="margin-bottom: 8px;"><span style="font-weight: 500; color: #9a9da3;">Model Number:</span> {safe_text(p['model_number'])}</div>
                        <div style="margin-bottom: 8px;"><span style="font-weight: 500; color: #9a9da3;">Date of Purchase:</span> {safe_text(p['purchase_date'])}</div>
                        <div><span style="font-weight: 500; color: #9a9da3;">Warranty Term:</span> {p['warranty_start']} &rarr; {p['warranty_end']}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    render_warranty_health(p.get("warranty_health"))
                    col_qr, col_scan = st.columns([1, 2])
                    with col_qr:
                        if st.button("Show QR", key=f"qr_btn_{p['id']}", use_container_width=True):
                            qr_resp = requests.get(f"{API_URL}/api/v1/products/{p['id']}/qr", headers=auth_headers())
                            if qr_resp.status_code == 200:
                                st.session_state[f"qr_svg_{p['id']}"] = qr_resp.json()
                            else:
                                st.error("Unable to generate QR code.")
                    with col_scan:
                        if p.get("qr_token"):
                            st.caption(f"Mobile scan route: /api/v1/qr/{p['qr_token']}")
                    if st.session_state.get(f"qr_svg_{p['id']}"):
                        qr_data = st.session_state[f"qr_svg_{p['id']}"]
                        st.markdown(f'<div class="qr-shell">{qr_data["qr_svg"]}</div>', unsafe_allow_html=True)
                        st.caption(qr_data["product_url"])

    elif page == "Raise Service Request":
        resp = requests.get(f"{API_URL}/customer/my-products", headers=auth_headers())
        products = resp.json()

        if not products:
            render_empty_state("No registered devices", "Register a product before requesting AI-assisted warranty service.")
        else:
            product_map = {f"{p['product_name']} (Serial: {p['serial_number']})": p["id"] for p in products}
            
            with st.container(border=True):
                st.markdown("### Service Details")
                with st.form("service_request_form", border=False):
                    choice = st.selectbox("Which device requires service?", list(product_map.keys()))
                    issue = st.text_area("Detailed Issue Description", height=150,
                                          placeholder="Provide description. E.g. Grinding noise during washing spin cycle.")
                    submitted = st.form_submit_button("Submit Claim for AI Review", use_container_width=True)

                    if submitted:
                        if not issue.strip():
                            st.error("Please provide a detailed description of the issue.")
                        else:
                            with st.spinner("Analyzing claim guidelines with local AI..."):
                                r = requests.post(
                                    f"{API_URL}/customer/service-requests",
                                    headers=auth_headers(),
                                    json={"customer_product_id": product_map[choice], "issue_description": issue.strip()},
                                )
                            if r.status_code == 200:
                                data = r.json()
                                st.success("Service ticket filed successfully!")
                                st.subheader("AI Warranty Intelligence")
                                render_ai_analysis(data)
                            else:
                                st.error(r.json().get("detail", "Failed to submit."))

    elif page == "My Service Requests":
        resp = requests.get(f"{API_URL}/customer/service-requests", headers=auth_headers())
        requests_list = resp.json()

        # Service request metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Tickets", len(requests_list))
        with col2:
            st.metric("Pending Triage", sum(1 for r in requests_list if r["status"] == "pending"))
        with col3:
            st.metric("Resolved Cases", sum(1 for r in requests_list if r["status"] == "resolved"))

        st.markdown("<br>", unsafe_allow_html=True)

        if not requests_list:
            render_empty_state("No service requests", "Create a claim to see AI coverage, evidence requirements, and review status here.")
        else:
            status_colors = {
                "pending": ("rgba(195, 171, 124, 0.15)", "#c3ab7c", "Pending"),
                "in_progress": ("rgba(170, 179, 189, 0.15)", "#aab3bd", "In Review"),
                "resolved": ("rgba(143, 171, 151, 0.15)", "#8fab97", "Resolved"),
                "rejected": ("rgba(185, 140, 133, 0.15)", "#b98c85", "Rejected")
            }
            
            for r in requests_list:
                bg, fg, status_label = status_colors.get(r['status'], ("rgba(155, 157, 162,0.15)", "#9a9da3", "Queued"))
                
                with st.expander(f"{r['product_name']} - {r['status'].upper()}"):
                    st.markdown(f"""
                    <div style="padding: 5px 0;">
                        <div style="margin-bottom: 12px;">
                            <span style="font-weight: 500; color: #9a9da3; margin-right: 8px;">Claim Status:</span>
                            <span style="background-color: {bg}; color: {fg}; padding: 3px 10px; border-radius: 12px; font-size: 0.8rem; font-weight: 600; text-transform: uppercase;">
                                {status_label}
                            </span>
                        </div>
                        <div style="margin-bottom: 10px;"><span style="font-weight: 500; color: #9a9da3;">Reported Problem:</span> {safe_text(r['issue_description'])}</div>
                        {f'<div style="margin-top: 10px;"><span style="font-weight: 500; color: #a99a86;">Technician Notes:</span> {r["admin_notes"]}</div>' if r["admin_notes"] else ''}
                        <div style="font-size: 0.8rem; color: #7b7f86; margin-top: 10px;">Submitted: {r['created_at']}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    render_ai_analysis(r)


# --- admin dashboard ---
def show_admin_dashboard():
    # Sidebar Design
    st.sidebar.markdown(f"""
    <div style="background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.06); border-radius: 16px; padding: 20px; margin-top: 15px; margin-bottom: 24px; text-align: center;">
        <img src="{logo_base64}" style="width: 58px; margin-bottom: 8px;" />
        <div style="font-weight: 700; color: #ffffff; font-size: 1.1rem; margin-top: 4px; letter-spacing: -0.01em;">{st.session_state.full_name}</div>
        <div style="color: #a99a86; font-size: 0.78rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.08em; margin-top: 3px;">Admin Panel</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.sidebar.markdown("<div style='margin-bottom: 10px; font-size: 0.78rem; color: #7b7f86; text-transform: uppercase; letter-spacing: 0.05em; font-weight: 600;'>Navigation</div>", unsafe_allow_html=True)
    st.sidebar.markdown("<div class='nav-item active'>", unsafe_allow_html=True)
    st.sidebar.button("📋  Claims Queue", use_container_width=True, disabled=True)
    st.sidebar.markdown("</div>", unsafe_allow_html=True)

    st.sidebar.markdown("<br><hr style='border-color: rgba(255,255,255,0.05);'><br>", unsafe_allow_html=True)
    st.sidebar.markdown('<div class="signout-btn-wrapper">', unsafe_allow_html=True)
    if st.sidebar.button("Sign Out", use_container_width=True, key="sign_out_btn"):
        logout()
    st.sidebar.markdown('</div>', unsafe_allow_html=True)

    st.header("Admin Claims Management Dashboard")
    st.caption("Manage, review, and finalize customer product service requests.")

    analytics_resp = requests.get(f"{API_URL}/admin/analytics", headers=auth_headers())
    analytics = analytics_resp.json() if analytics_resp.status_code == 200 else {}

    if analytics:
        a1, a2, a3, a4 = st.columns(4)
        with a1:
            st.metric("Registered Products", analytics.get("registered_products", 0))
        with a2:
            st.metric("Open Claims", analytics.get("open_claims", 0))
        with a3:
            st.metric("Fraud Alerts", analytics.get("fraud_alerts", 0))
        with a4:
            st.metric("Approval Rate", f"{analytics.get('approval_rate', 0)}%")

        with st.container(border=True):
            m1, m2 = st.columns(2)
            with m1:
                st.markdown("#### Monthly Registrations")
                monthly = analytics.get("monthly_registrations") or []
                if monthly:
                    st.bar_chart({item["month"]: item["count"] for item in reversed(monthly)})
                else:
                    st.caption("No registration trend data yet.")
            with m2:
                st.markdown("#### Top Manufacturers")
                top_makers = analytics.get("top_manufacturers") or []
                if top_makers:
                    for item in top_makers:
                        st.markdown(f"- **{safe_text(item['manufacturer'])}**: {item['count']} registered products")
                else:
                    st.caption("No manufacturer data yet.")

    status_filter = st.selectbox("Status Filter Queue", ["All", "pending", "in_progress", "resolved", "rejected"])
    params = {} if status_filter == "All" else {"status": status_filter}

    resp = requests.get(f"{API_URL}/admin/service-requests", headers=auth_headers(), params=params)
    requests_list = resp.json()

    # Admin Metrics Grid
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Tickets", len(requests_list))
    with col2:
        st.metric("Pending Actions", sum(1 for r in requests_list if r["status"] == "pending"))
    with col3:
        st.metric("Active Workloads", sum(1 for r in requests_list if r["status"] == "in_progress"))
    with col4:
        st.metric("Closed/Resolved", sum(1 for r in requests_list if r["status"] == "resolved"))

    st.markdown("<br>", unsafe_allow_html=True)

    if not requests_list:
        st.info("No service requests match the filter criteria.")
    else:
        status_colors = {
            "pending": ("rgba(195, 171, 124, 0.15)", "#c3ab7c", "Pending"),
            "in_progress": ("rgba(170, 179, 189, 0.15)", "#aab3bd", "In Review"),
            "resolved": ("rgba(143, 171, 151, 0.15)", "#8fab97", "Resolved"),
            "rejected": ("rgba(185, 140, 133, 0.15)", "#b98c85", "Rejected")
        }

        for r in requests_list:
            bg, fg, status_label = status_colors.get(r['status'], ("rgba(155, 157, 162,0.15)", "#9a9da3", "Queued"))
            
            with st.expander(f"Ticket #{r['id']} - {r['product_name']} - {r['customer_name']}"):
                st.markdown(f"""
                <div style="padding: 5px 0;">
                    <div style="margin-bottom: 8px;"><span style="font-weight: 500; color: #9a9da3;">Customer Account:</span> {safe_text(r['customer_name'])}</div>
                    <div style="margin-bottom: 8px;"><span style="font-weight: 500; color: #9a9da3;">Reported Issue:</span> {safe_text(r['issue_description'])}</div>
                    <div style="margin-bottom: 12px;">
                        <span style="background-color: {bg}; color: {fg}; padding: 3px 10px; border-radius: 12px; font-size: 0.8rem; font-weight: 600; text-transform: uppercase;">
                            {status_label}
                        </span>
                    </div>
                    <div style="font-size: 0.8rem; color: #7b7f86; margin-bottom: 15px;">Submitted: {r['created_at']} | Last Updated: {r['updated_at']}</div>
                </div>
                """, unsafe_allow_html=True)
                render_ai_analysis(r, accent="#a99a86")

                # Balanced action layout: Notes (left) + Status/Save (right)
                col_notes, col_action = st.columns([2.5, 1])
                with col_notes:
                    notes = st.text_area("Internal Technician Notes", value=r["admin_notes"] or "", key=f"notes_text_{r['id']}", height=120)
                with col_action:
                    new_status = st.selectbox(
                        "Transition Status", ["pending", "in_progress", "resolved", "rejected"],
                        index=["pending", "in_progress", "resolved", "rejected"].index(r["status"]),
                        key=f"status_select_{r['id']}",
                    )
                    st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
                    if st.button("Save Ticket Update", key=f"save_action_{r['id']}", use_container_width=True):
                        update_resp = requests.patch(
                            f"{API_URL}/admin/service-requests/{r['id']}",
                            headers=auth_headers(),
                            json={"status": new_status, "admin_notes": notes.strip()},
                        )
                        if update_resp.status_code == 200:
                            st.toast(f"Ticket #{r['id']} successfully updated.", icon="✅")
                            st.rerun()
                        else:
                            st.error("Failed to commit database updates.")


# --- routing ---
if st.session_state.token is None:
    show_login_page()
elif st.session_state.role == "customer":
    show_customer_dashboard()
elif st.session_state.role == "admin":
    show_admin_dashboard()
