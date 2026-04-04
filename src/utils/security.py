import google.generativeai as genai
import os
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

def ai_truth_check(text: str, api_key: str = None) -> bool:
    """
    Uses Gemini to detect if the input is a realistic emergency report or spam/placeholder text.
    Returns True if realistic, False if suspicious.
    """
    used_key = api_key or os.environ.get("GEMINI_API_KEY")
    if not used_key:
        if "lorem ipsum" in text.lower() or len(text) < 5:
            return False
        return True
        
    try:
        genai.configure(api_key=used_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
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
