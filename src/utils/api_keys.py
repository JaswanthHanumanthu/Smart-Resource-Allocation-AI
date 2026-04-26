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

def get_model(system_instruction: str = None):
    """
    Returns a proxy model object that:
      1. Forces the stable v1 API endpoint (not v1beta)
      2. Uses 'gemini-1.5-flash' as primary (modern, short model string)
      3. Automatically falls back to 'gemini-pro' on 404 NotFound errors
    """
    if not system_instruction:
        system_instruction = (
            "You are the Smart Resource Allocation Assistant. "
            "Analyze the provided Mumbai logistics data and give concise, tactical advice. "
            "Focus on saving time and lives."
        )

    # Force the stable v1 endpoint to avoid 404s from v1beta routing
    import google.api_core.gapic_v1.client_info as _ci
    try:
        from google.api_core.client_options import ClientOptions
        _client_options = ClientOptions(api_endpoint="generativelanguage.googleapis.com")
    except Exception:
        _client_options = None

    _PRIMARY_MODEL   = "gemini-1.5-flash"
    _FALLBACK_MODEL  = "gemini-pro"

    class _RobustModel:
        """Thin wrapper — tries primary, falls back to secondary on 404."""
        def __init__(self):
            try:
                self._primary = genai.GenerativeModel(
                    model_name=_PRIMARY_MODEL,
                    system_instruction=system_instruction,
                )
            except Exception:
                self._primary = None

            try:
                self._fallback = genai.GenerativeModel(
                    model_name=_FALLBACK_MODEL,
                    system_instruction=system_instruction,
                )
            except Exception:
                self._fallback = None

        def generate_content(self, *args, **kwargs):
            # Try primary model first
            if self._primary:
                try:
                    return self._primary.generate_content(*args, **kwargs)
                except google.api_core.exceptions.NotFound:
                    pass   # fall through to fallback
                except Exception:
                    pass   # any other error — try fallback

            # Fallback to gemini-pro
            if self._fallback:
                return self._fallback.generate_content(*args, **kwargs)

            raise RuntimeError("All Gemini models unavailable — check API key and region.")

    return _RobustModel()
