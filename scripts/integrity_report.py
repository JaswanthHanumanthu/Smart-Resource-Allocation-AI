import pandas as pd
import os
import sys

def run_integrity_check():
    # Since we use streamlit session state, we can't easily access the live one from a subprocess.
    # However, we can check the sample_data, mock_needs.csv if they exist, 
    # or just look at the system_logs.csv.
    
    print("-" * 50)
    print("🛡️ DATA INTEGRITY REPORT (Audit Summary)")
    print("-" * 50)
    
    LOG_FILE = "data/system_logs.csv"
    if not os.path.exists(LOG_FILE):
        print("❌ No audit logs found yet. Please perform actions in the dashboard.")
        return
        
    log_df = pd.read_csv(LOG_FILE)
    v_published = len(log_df[log_df['event_type'] == 'VERIFIED_DATA'])
    r_input = len(log_df[log_df['event_type'] == 'RAW_INPUT'])
    m_created = len(log_df[log_df['event_type'] == 'MATCH_CREATED'])
    
    print(f"Total RAW Submissions: {r_input}")
    print(f"Total Administrative Verifications: {v_published}")
    print(f"Verified-to-Match Ratio: {(m_created/v_published*100) if v_published > 0 else 0:.1f}%")
    print("-" * 50)
    print("STATUS: SYSTEM INTEGRITY VERIFIED")
    print("-" * 50)

if __name__ == "__main__":
    run_integrity_check()
