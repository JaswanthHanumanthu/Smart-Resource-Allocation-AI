import google.generativeai as genai
import os
import streamlit as st

from .api_keys import get_google_api_key
import pandas as pd
from datetime import datetime, timedelta

def ai_truth_check(text: str, api_key: str = None) -> bool:
    """
    Uses Gemini to detect if the input is a realistic emergency report or spam/placeholder text.
    Returns True if realistic, False if suspicious.
    """
    used_key = api_key or get_google_api_key()
    if not used_key:
        if "lorem ipsum" in text.lower() or len(text) < 5:
            return False
        return True
        
    try:
        from .api_keys import get_google_api_key, get_model
        genai.configure(api_key=used_key)
        model = get_model()
        prompt = f"""
        Analyze this NGO report: "{text}"
        Respond with "REALISTIC" OR "SPAM" (ONLY ONE WORD). Use spam for lorem ipsum or nonsense.
        """
        response = model.generate_content(prompt)
        res = response.text.strip().upper()
        return "REALISTIC" in res
    except Exception:
        return True

def rate_limit_check(limit: int = 10, window_hours: int = 1) -> bool:
    if 'upload_timestamps' not in st.session_state:
        st.session_state['upload_timestamps'] = []
    now = datetime.now()
    window_start = now - timedelta(hours=window_hours)
    st.session_state['upload_timestamps'] = [ts for ts in st.session_state['upload_timestamps'] if ts > window_start]
    if len(st.session_state['upload_timestamps']) >= limit: return False
    st.session_state['upload_timestamps'].append(now)
    return True

def check_anomaly(latitude: float, longitude: float, df: pd.DataFrame, threshold: int = 100, minutes: int = 1) -> bool:
    """
    Detects if sudden spikes in report frequency are occurring at a specific location.
    If 100 reports from the same 500m area occur within a minute, returns True (Anomaly).
    """
    if df.empty or 'timestamp' not in df.columns:
        return False
        
    now = datetime.now()
    start_time = now - timedelta(minutes=minutes)
    
    # Filter for last N minutes
    recent_df = df[pd.to_datetime(df['timestamp']) > start_time]
    if recent_df.empty:
        return False
        
    # Check proximity (approx 500m radius bucket)
    dist_threshold = 0.005 # Degrees
    nearby = recent_df[
        (abs(recent_df['latitude'] - latitude) < dist_threshold) & 
        (abs(recent_df['longitude'] - longitude) < dist_threshold)
    ]
    
    # We factor in the report_count if it exists
    total_count = nearby['report_count'].sum() if 'report_count' in nearby.columns else len(nearby)
    
    return total_count >= threshold

def anonymize_report_data(text: str) -> str:
    """
    Masks PII like personal names and specific door-step addresses (e.g. '123 Main St')
    to ensure community privacy in humanitarian situational reports.
    """
    import re
    # Mask street addresses and house numbers
    text = re.sub(r'\b\d{1,4}\s[A-Z][a-z]+( Street| St| Ave| Road| Rd| Lane| Ln| Blvd| Way)\b', '[STREET ADDRESS REDACTED]', text)
    # Mask specific house numbers at start of strings
    text = re.sub(r'^\d{1,5}\s', '[HOUSE NUMBER REDACTED] ', text)
    # Redact common Title + Name structures (Simple NGO Prototype)
    text = re.sub(r'(Mr\.|Mrs\.|Ms\.|Dr\.)\s[A-Z][a-z]+', '[NAME REDACTED]', text)
    return text

def mask_name(name: str) -> str:
    """
    Masks identity for the public dashboard (e.g., 'Alice' -> 'A***').
    """
    if not name: return ""
    parts = name.split()
    masked = []
    for p in parts:
        if p.endswith('.'):
            masked.append(p)
        elif len(p) > 1:
            masked.append(p[0] + "***")
        else:
            masked.append(p)
    return " ".join(masked)
