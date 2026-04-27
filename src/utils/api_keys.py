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

class RobustModel:
    """
    Tactical Failover Engine: Cycles through satellite models to ensure mission continuity 
    when primary quotas are exceeded.
    """
    def __init__(self, system_instruction):
        self.system_instruction = system_instruction
        self.models = ["gemini-3-flash-preview", "gemini-1.5-flash", "gemini-1.5-flash-8b", "gemini-1.5-pro"]

    def generate_content(self, contents, **kwargs):
        last_error = None
        for model_name in self.models:
            try:
                model = genai.GenerativeModel(
                    model_name=model_name,
                    system_instruction=self.system_instruction
                )
                return model.generate_content(contents, **kwargs)
            except Exception as e:
                last_error = e
                # If it's not a quota (429) or not found (404), stop cycling
                error_str = str(e).lower()
                if "429" not in error_str and "404" not in error_str:
                    break
                continue
        raise last_error

def get_model(system_instruction: str = None):
    """
    Returns a RobustModel that handles multi-satellite failover.
    """
    if not system_instruction:
        system_instruction = (
            "You are the Smart Resource Allocation Assistant. "
            "Analyze the provided Mumbai logistics data and give concise, tactical advice. "
            "Focus on saving time and lives."
        )

    return RobustModel(system_instruction=system_instruction)
