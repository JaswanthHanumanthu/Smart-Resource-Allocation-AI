"""
Resolve Google Gemini API key from environment (.env) or Streamlit secrets.
"""

from __future__ import annotations

import os
from pathlib import Path
import google.generativeai as genai
import google.api_core.exceptions

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

try:
    from dotenv import load_dotenv
    load_dotenv(_PROJECT_ROOT / ".env")
except ImportError:
    pass

_PLACEHOLDER_KEYS = frozenset(
    {
        "",
        "dev_key_placeholder",
        "your-api-key-here",
        "changeme",
        "paste-your-key-here",
        "sk-placeholder",
    }
)

def _normalize_key(raw: str | None) -> str | None:
    if raw is None:
        return None
    s = str(raw).strip()
    if not s:
        return None
    if s == "DEV_KEY_PLACEHOLDER" or s.lower() in _PLACEHOLDER_KEYS:
        return None
    return s

def get_google_api_key() -> str | None:
    """Return a usable API key, or None if not configured.
    Primary: st.secrets (Streamlit Cloud)
    Fallback: Environment Variables (os.getenv)
    """
    key = None

    # 1. Primary: Streamlit Secrets (Recommended for Cloud)
    try:
        import streamlit as st
        key = _normalize_key(st.secrets.get("GOOGLE_API_KEY"))
    except Exception:
        pass

    # 2. Secondary: Environment Variables (os.environ)
    if not key:
        key = _normalize_key(os.environ.get("GOOGLE_API_KEY"))

    # 3. Tertiary Fallback: GEMINI_API_KEY (os.environ)
    if not key:
        key = _normalize_key(os.environ.get("GEMINI_API_KEY"))

    return key

def get_model(system_instruction: str = None):
    """
    Returns a standard Gemini 1.5 Flash model.
    """
    if not system_instruction:
        system_instruction = (
            "You are the Smart Resource Allocation Assistant. "
            "Analyze the provided Mumbai logistics data and give concise, tactical advice. "
            "Focus on saving time and lives."
        )

    model_name = "gemini-3-flash-preview"
    
    return genai.GenerativeModel(
        model_name=model_name,
        system_instruction=system_instruction,
    )
