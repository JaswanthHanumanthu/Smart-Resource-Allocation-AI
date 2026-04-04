import os
import pandas as pd
from datetime import datetime

LOG_FILE = "data/system_logs.csv"

def log_event(event_type: str, reason: str):
    """
    Logs an event to system_logs.csv for audit purposes.
    """
    os.makedirs("data", exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = {
        "timestamp": timestamp,
        "event_type": event_type,
        "reason": reason
    }
    
    new_log_df = pd.DataFrame([log_entry])
    
    if os.path.exists(LOG_FILE):
        try:
            log_df = pd.read_csv(LOG_FILE)
            log_df = pd.concat([log_df, new_log_df], ignore_index=True)
            log_df.to_csv(LOG_FILE, index=False)
        except Exception:
            # If CSV is corrupted or locked, overwrite nicely
            new_log_df.to_csv(LOG_FILE, index=False)
    else:
        new_log_df.to_csv(LOG_FILE, index=False)

def calculate_efficiency(df: pd.DataFrame) -> float:
    """
    Calculates efficiency as (Resolved Tasks / Total Verified Tasks) * 100.
    Handles divide by zero gracefully.
    """
    if df.empty:
        return 0.0
        
    verified_df = df[df['verified'] == True]
    if verified_df.empty:
        return 0.0
        
    resolved_count = len(verified_df[verified_df['status'] == 'Matched'])
    total_verified = len(verified_df)
    
    return round((resolved_count / total_verified) * 100, 1)
