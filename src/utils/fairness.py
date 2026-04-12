import pandas as pd
import numpy as np
import streamlit as st


@st.cache_data
def calculate_parity_score(needs_df: pd.DataFrame) -> float:
    """
    Parity score from Matched vs Pending by category, urgency-normalized.
    100 = equitable baseline; < 70 suggests possible bias (heuristic).
    """
    parity = 100.0
    if needs_df is None or needs_df.empty:
        return parity
    if not {"category", "status", "urgency"}.issubset(needs_df.columns):
        return parity

    sector_metrics: list[float] = []
    for _, group in needs_df.groupby("category"):
        matched = int((group["status"] == "Matched").sum())
        pending = int((group["status"] == "Pending").sum())
        denom = matched + pending
        match_rate = matched / denom if denom > 0 else 1.0
        avg_urgency = float(group["urgency"].mean())
        if not np.isfinite(avg_urgency) or avg_urgency <= 0:
            avg_urgency = 1.0
        sector_metrics.append(match_rate * (10.0 / avg_urgency))

    if not sector_metrics:
        return parity
    parity = (sum(sector_metrics) / len(sector_metrics)) * 100.0
    return float(round(min(100.0, parity), 1))


def generate_fairness_report(df: pd.DataFrame) -> dict:
    """
    Geographic coverage, urgency bands, and response equity by category.
    """
    if df is None or df.empty:
        return {"error": "No data available for fairness analysis."}

    required = {"latitude", "longitude", "status", "urgency", "category"}
    if not required.issubset(df.columns):
        return {
            "error": f"Missing columns for fairness analysis. Need: {sorted(required - set(df.columns))}"
        }

    report: dict = {}
    df = df.copy()

    # --- 1. Geographic Coverage ---
    lat_mid = df["latitude"].median()
    lon_mid = df["longitude"].median()

    def quadrant(row):
        ns = "North" if row["latitude"] >= lat_mid else "South"
        ew = "East" if row["longitude"] >= lon_mid else "West"
        return f"{ns}-{ew}"

    df["quadrant"] = df.apply(quadrant, axis=1)
    geo = df.groupby("quadrant").agg(
        total_needs=("status", "count"),
        matched=("status", lambda x: (x == "Matched").sum()),
    )
    geo["match_rate_pct"] = (geo["matched"] / geo["total_needs"] * 100).round(1)
    report["geographic_coverage"] = geo[
        ["total_needs", "matched", "match_rate_pct"]
    ].to_dict()

    # --- 2. Urgency Distribution ---
    bins = [0, 3, 6, 10]
    labels = ["Low (1-3)", "Medium (4-6)", "High (7-10)"]
    df["urgency_band"] = pd.cut(df["urgency"], bins=bins, labels=labels)
    urg = df.groupby("urgency_band", observed=True).agg(
        total=("status", "count"),
        matched=("status", lambda x: (x == "Matched").sum()),
        avg_urgency=("urgency", "mean"),
    )
    urg["match_rate_pct"] = (urg["matched"] / urg["total"] * 100).round(1)
    urg["avg_urgency"] = urg["avg_urgency"].round(2)
    report["urgency_distribution"] = urg[
        ["total", "matched", "match_rate_pct", "avg_urgency"]
    ].to_dict()

    # --- 3. Response Equity (by Category) ---
    resp = df.groupby("category").agg(
        total=("status", "count"),
        matched=("status", lambda x: (x == "Matched").sum()),
        avg_urgency=("urgency", "mean"),
    )
    resp["match_rate_pct"] = (resp["matched"] / resp["total"] * 100).round(1)
    resp["avg_urgency"] = resp["avg_urgency"].round(2)
    overall_match_rate = float((df["status"] == "Matched").mean() * 100)
    resp["status"] = resp["match_rate_pct"].apply(
        lambda r: "✅ Equitable" if r >= overall_match_rate else "⚠️ Under-Served"
    )
    report["response_equity"] = resp[
        ["total", "matched", "match_rate_pct", "avg_urgency", "status"]
    ].to_dict()

    report["summary"] = {
        "overall_match_rate_pct": round(overall_match_rate, 1),
        "total_needs_analyzed": int(len(df)),
        "parity_score_pct": float(calculate_parity_score(df)),
        "under_served_categories": [
            cat for cat, s in resp["status"].items() if "⚠️" in s
        ],
    }

    return report


@st.cache_data
def audit_for_bias(needs_df: pd.DataFrame) -> list:
    """High-urgency clusters with many pending items."""
    warnings: list = []
    if needs_df is None or needs_df.empty:
        return warnings
    if not {"category", "status", "urgency"}.issubset(needs_df.columns):
        return warnings

    if "verified" in needs_df.columns:
        v_df = needs_df[needs_df["verified"] == True]
    else:
        v_df = needs_df

    high_urg = v_df[v_df["urgency"] >= 8]
    for category in high_urg["category"].unique():
        cat_df = high_urg[high_urg["category"] == category]
        unassigned = len(cat_df[cat_df["status"] == "Pending"])
        if unassigned > 3:
            warnings.append(
                {
                    "severity": "CRITICAL",
                    "message": (
                        f"🚨 **BIAS WARNING:** Cluster in '{category}' sector. "
                        f"{unassigned} high-urgency reports still pending."
                    ),
                    "remedy": (
                        f"Consider shifting capacity toward '{category}'."
                    ),
                }
            )
    return warnings
