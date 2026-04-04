import pandas as pd
import numpy as np
import google.generativeai as genai
import os
import json

def calculate_distance(lat1, lon1, lat2, lon2):
    """Simple euclidean distance approximation for the prototype."""
    return np.sqrt((lat1 - lat2)**2 + (lon1 - lon2)**2)

def match_volunteer_to_needs(volunteer: dict, needs_df: pd.DataFrame, top_n: int = 3, api_key: str = None) -> pd.DataFrame:
    """
    Ranks needs for a specific volunteer prioritizing Urgency > Skill > Proximity.
    Uses Gemini for XAI reasoning and refined confidence scores.
    """
    if needs_df.empty:
        return pd.DataFrame()
        
    df = needs_df.copy()
    
    # 1. Skill Match Scoring (Heuristic for initial ranking)
    def rank_skill(category, skills):
        skills = [s.lower() for s in skills]
        if category == "Medical" and any(s in ["doctor", "nurse", "medic"] for s in skills):
            return 2.0
        elif category == "Food" and any(s in ["driver", "general", "cook", "logistics"] for s in skills):
            return 1.5
        elif category == "Shelter" and any(s in ["builder", "general", "driver"] for s in skills):
            return 1.5
        elif "general" in skills:
            return 1.0
        return 0.5
        
    df["skill_score"] = df["category"].apply(lambda cat: rank_skill(cat, volunteer["skills"]))
    
    # 2. Proximity Scoring
    df["distance"] = df.apply(
        lambda row: calculate_distance(volunteer["latitude"], volunteer["longitude"], row["latitude"], row["longitude"]), 
        axis=1
    )
    max_dist = df["distance"].max() if df["distance"].max() > 0 else 1
    df["proximity_score"] = 1.0 - (df["distance"] / max_dist)
    
    # 3. Overall Weighted Matching Score (out of 10 for initially sorting)
    df["urgency_norm"] = df["urgency"] / 10.0
    df["match_score"] = (
        (df["urgency_norm"] * 5.0) +
        (df["skill_score"] / 2.0 * 3.0) +
        (df["proximity_score"] * 2.0)
    )
    
    # Sort by heuristic match score and take top_n
    top_matches = df.sort_values(by="match_score", ascending=False).head(top_n)
    
    # --- 4. Explainable AI (XAI) Logic via Gemini ---
    used_key = api_key or os.environ.get("GEMINI_API_KEY")
    ai_results = {}
    
    if used_key:
        try:
            genai.configure(api_key=used_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            # Formulate a batch prompt for efficiency
            tasks_info = []
            for idx, row in top_matches.iterrows():
                tasks_info.append({
                    "id": str(idx),
                    "category": row['category'],
                    "urgency": row['urgency'],
                    "description": row['description'],
                    "distance_approx": f"{row['distance']*111:.1f}km"
                })
            
            prompt = f"""
            You are an expert NGO logistics coordinator. 
            Evaluate the fitness of a volunteer for {len(tasks_info)} specific tasks.
            
            Volunteer: {volunteer['name']}
            Skills: {", ".join(volunteer['skills'])}
            
            Tasks to evaluate:
            {json.dumps(tasks_info)}
            
            For EACH task, provide:
            1. A brief "Reasoning Statement" (XAI) explaining WHY this volunteer is a good match based on their skills, the task urgency, and proximity.
            2. A refined "Confidence Score" from 0.0 to 1.0 (as a float).
            
            Output strictly valid JSON in this format:
            {{
                "task_evaluations": [
                    {{
                        "id": "task_index",
                        "reasoning": "...",
                        "confidence": 0.XX
                    }},
                    ...
                ]
            }}
            """
            
            response = model.generate_content(prompt)
            data = json.loads(response.text.strip('` \n').replace('json', ''))
            for eval_item in data['task_evaluations']:
                ai_results[int(eval_item['id'])] = eval_item
        except Exception as e:
            # Fallback will handle this below
            print(f"AI Matching Error: {e}")
            
    # Apply AI reasoning or fallback to heuristic
    def apply_ai_reasoning(row):
        res = ai_results.get(row.name)
        if res:
            return res['reasoning'], res['confidence'] * 100.0, res['confidence'] * 10.0
        
        # Fallback heuristic logic from old version
        vol_name = volunteer.get('name', 'Volunteer')
        skills = ", ".join(volunteer.get('skills', ['General']))
        urgency_lbl = "High-Urgency" if row["urgency"] >= 8 else ("Medium-Urgency" if row["urgency"] >= 5 else "Low-Urgency")
        dist_km = row['distance'] * 111
        dist_string = f"within {dist_km:.1f}km" if dist_km >= 0.1 else "at the exact location"
        
        fallback_reason = f"Heuristic Match: Based on skills ({skills}) and {urgency_lbl} status within {dist_string}."
        confidence = (row['match_score'] / 10.0) * 100.0
        return fallback_reason, confidence, row['match_score']
        
    results = top_matches.apply(apply_ai_reasoning, axis=1, result_type='expand')
    top_matches["match_reason"] = results[0]
    top_matches["confidence_score"] = results[1]
    top_matches["match_score"] = results[2]
    
    return top_matches
