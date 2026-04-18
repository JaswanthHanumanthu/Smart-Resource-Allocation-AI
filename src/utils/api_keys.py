"""
Resolve Google Gemini API key from environment (.env) or Streamlit secrets.

Load order (first usable value wins):
  1. GOOGLE_API_KEY or GEMINI_API_KEY in the process environment (including from .env)
  2. GOOGLE_API_KEY in Streamlit secrets (local .streamlit/secrets.toml or Cloud Secrets)

Placeholder values from templates are ignored so a real key in .env is not overridden by a dummy secrets entry.
"""

from __future__ import annotations

import os
from pathlib import Path

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
    Primary: Environment Variables (os.getenv)
    Fallback: st.secrets (Streamlit Cloud)
    """
    key = None

    # 1. Primary: Environment Variables (os.environ)
    key = _normalize_key(os.environ.get("GOOGLE_API_KEY"))

    # 2. Secondary Fallback: GEMINI_API_KEY (os.environ)
    if not key:
        key = _normalize_key(os.environ.get("GEMINI_API_KEY"))

    # 3. Last Fallback: Streamlit Secrets
    if not key:
        try:
            import streamlit as st
            key = _normalize_key(st.secrets.get("GOOGLE_API_KEY"))
        except Exception:
            pass

    return key
