import pandas as pd
import numpy as np
import google.generativeai as genai
import os
import json
import streamlit as st

from ..utils.api_keys import get_google_api_key


def calculate_distance(lat1, lon1, lat2, lon2):
    """Simple euclidean distance approximation for the prototype."""
    return np.sqrt((lat1 - lat2)**2 + (lon1 - lon2)**2)


@st.cache_data(show_spinner=False)
def match_volunteer_to_needs(volunteer_json: str, needs_df_json: str, top_n: int = 3, api_key: str = None) -> pd.DataFrame:
    """
    Ranks needs for a specific volunteer prioritizing Urgency > Skill > Proximity.
    Uses Gemini for XAI reasoning and refined confidence scores.

    Args use JSON strings (not dict/DataFrame) for st.cache_data hash compatibility.
    Call site:  match_volunteer_to_needs(json.dumps(vol), needs_df.to_json(), ...)
    """
    volunteer = json.loads(volunteer_json)
    needs_df = pd.read_json(needs_df_json)

    if needs_df.empty:
        return pd.DataFrame()

    df = needs_df.copy()

    # 1. Skills-First Logical Scoring
    def rank_skill(category, skills):
        skills_lower = [s.lower() for s in skills]
        skill_map = {
            "Medical":  ["medical", "first aid", "doctor", "nurse", "medic", "paramedic"],
            "Food":     ["logistics", "driving", "delivery", "cook", "food distribution"],
            "Shelter":  ["logistics", "building", "construction", "shelter management"],
            "General":  ["language", "teaching", "counseling", "translation", "general"]
        }
        relevant = skill_map.get(category, ["general"])
        if any(s in relevant for s in skills_lower):
            return 5.0   # Elite match
        elif "general" in skills_lower:
            return 1.0   # Generalist support
        return 0.1       # Minimal match

    df["skill_score"] = df["category"].apply(
        lambda cat: rank_skill(cat, volunteer.get("skills", []))
    )

    # 2. Tactical Proximity (degree-based, ~111 km per degree)
    df["distance"] = df.apply(
        lambda row: calculate_distance(
            volunteer["latitude"], volunteer["longitude"],
            row["latitude"], row["longitude"]
        ),
        axis=1
    )
    df["distance_km"] = df["distance"] * 111.0

    def score_proximity(dist_km):
        if dist_km <= 5.0:   return 4.0   # Within 5 km
        elif dist_km <= 15.0: return 1.5  # Secondary tier
        return 0.2                         # Far

    df["proximity_score"] = df["distance_km"].apply(score_proximity)

    # 3. Composite Match Score  (Skill 50% | Proximity 30% | Urgency 20%)
    df["match_score"] = (
        df["skill_score"] +          # already /5*5 = itself
        df["proximity_score"] +
        (df.get("urgency", 5) / 10.0 * 2.0)
    )

    top_matches = df.sort_values(by="match_score", ascending=False).head(top_n).copy()

    # 4. Explainable AI (XAI) via Gemini
    used_key = api_key or get_google_api_key()
    ai_results = {}

    if used_key:
        try:
            genai.configure(api_key=used_key)
            model = genai.GenerativeModel('gemini-1.5-flash')

            tasks_info = [
                {
                    "id": str(idx),
                    "category": row['category'],
                    "urgency": int(row.get('urgency', 5)),
                    "description": str(row.get('description', '')),
                    "distance_approx": f"{row['distance_km']:.1f}km"
                }
                for idx, row in top_matches.iterrows()
            ]

            prompt = f"""
            You are an expert NGO logistics coordinator.
            Evaluate the fitness of a volunteer for {len(tasks_info)} specific tasks.

            Volunteer: {volunteer['name']}
            Skills: {", ".join(volunteer.get('skills', []))}

            Tasks to evaluate:
            {json.dumps(tasks_info)}

            For EACH task, provide:
            1. A brief "Reasoning Statement" (XAI) explaining WHY this volunteer is a good match.
            2. A refined "Confidence Score" from 0.0 to 1.0.

            Output strictly valid JSON:
            {{
                "task_evaluations": [
                    {{"id": "task_index", "reasoning": "...", "confidence": 0.85}},
                    ...
                ]
            }}
            """

            response = model.generate_content(prompt)
            clean = response.text.strip('`\n ').lstrip('json').strip()
            data = json.loads(clean)
            for item in data.get('task_evaluations', []):
                try:
                    ai_results[int(item['id'])] = item
                except (ValueError, KeyError):
                    pass
        except Exception as e:
            print(f"AI Matching Error: {e}")

    # 5. Apply AI reasoning or heuristic fallback per row
    def apply_ai_reasoning(row):
        res = ai_results.get(row.name)
        if res:
            return res['reasoning'], res['confidence'] * 100.0, res['confidence'] * 10.0

        skills_str = ", ".join(volunteer.get('skills', ['General']))
        urgency_val = row.get("urgency", 5)
        urgency_lbl = (
            "High-Urgency" if urgency_val >= 8
            else "Medium-Urgency" if urgency_val >= 5
            else "Low-Urgency"
        )
        dist_km = row.get('distance_km', 0)
        dist_str = f"within {dist_km:.1f}km" if dist_km >= 0.1 else "at the exact location"
        reason = f"Heuristic: Skills ({skills_str}), {urgency_lbl}, {dist_str}."
        conf = min((row['match_score'] / 10.0) * 100.0, 100.0)
        return reason, conf, row['match_score']

    results = top_matches.apply(apply_ai_reasoning, axis=1, result_type='expand')
    top_matches["match_reason"]     = results[0]
    top_matches["confidence_score"] = results[1]
    top_matches["match_score"]      = results[2]

    return top_matches
