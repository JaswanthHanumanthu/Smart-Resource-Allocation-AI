import pandas as pd
import numpy as np

def calculate_parity_score(needs_df):
    """
    Calculates a 'Parity Score' based on the ratio of Matched vs Pending tasks
    across different geospatial sectors/categories, normalized by Urgency.
    100% = Perfectly Equitable (resources going where urgency is highest).
    < 70% = High Risk of Operational Bias.
    """
    if needs_df.empty: return 100
    
    # 1. Group by Category (Sectors)
    groups = needs_df.groupby('category')
    sector_metrix = []
    
    for name, group in groups:
        matched = len(group[group['status'] == 'Matched'])
        pending = len(group[group['status'] == 'Pending'])
        avg_urgency = group['urgency'].mean()
        
        # Sector Match Rate
        match_rate = matched / (matched + pending) if (matched + pending) > 0 else 1.0
        # Ideal Rate: Higher urgency sectors SHOULD have higher match rates
        sector_metrix.append(match_rate * (10 / avg_urgency)) # Normalized
        
    parity = (sum(sector_metrix) / len(sector_metrix)) * 100 if sector_metrix else 100
    return round(min(100, parity), 1)

def audit_for_bias(needs_df):
    """
    Analyzes data for under-served high-urgency clusters.
    Returns a list of warnings.
    """
    warnings = []
    if needs_df.empty: return warnings
    
    # Check for 'Silent Clusters': High urgency, multiple reports, but 0 matches.
    v_df = needs_df[needs_df['verified'] == True]
    high_urg = v_df[v_df['urgency'] >= 8]
    
    for category in high_urg['category'].unique():
        cat_df = high_urg[high_urg['category'] == category]
        unassigned = len(cat_df[cat_df['status'] == 'Pending'])
        if unassigned > 3:
            warnings.append({
                "severity": "CRITICAL",
                "message": f"🚨 **BIAS WARNING:** Cluster detection in '{category}' Sector. {unassigned} High-Urgency reports detected with ZERO resource allocation missions.",
                "remedy": f"Action Suggestion: Pivot generalist volunteers from low-urgency 'General' tasks to the '{category}' sector immediately."
            })
            
    return warnings
