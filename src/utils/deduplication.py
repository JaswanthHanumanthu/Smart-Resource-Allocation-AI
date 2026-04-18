import pandas as pd
import numpy as np
from difflib import SequenceMatcher
from ..models.matching import calculate_distance
import google.generativeai as genai
import os

from .api_keys import get_google_api_key

def get_semantic_similarity(text1, text2, api_key=None):
    """
    Calculates semantic similarity using Gemini Embeddings if available.
    Falls back to difflib SequenceMatcher.
    """
    used_key = api_key or get_google_api_key()
    if not used_key:
        return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()
        
    try:
        genai.configure(api_key=used_key)
        # Using the embedding-001 model for fast semantic check
        res1 = genai.embed_content(model="models/embedding-001", content=text1, task_type="similarity")
        res2 = genai.embed_content(model="models/embedding-001", content=text2, task_type="similarity")
        
        vec1 = np.array(res1['embedding'])
        vec2 = np.array(res2['embedding'])
        
        # Consine Similarity
        similarity = np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
        return float(similarity)
    except Exception:
        return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()

def handle_duplication(new_report: dict, existing_df: pd.DataFrame, dist_threshold: float = 0.005, sim_threshold: float = 0.88):
    """
    Checks for duplicates and returns (is_dupe, duplicate_index).
    - dist_threshold: approx 500m
    - sim_threshold: semantic similarity threshold
    """
    if existing_df.empty:
        return False, None
    
    # Pre-filter by category
    potential_dupes = existing_df[existing_df['category'] == new_report['category']]
    if potential_dupes.empty:
        return False, None
        
    for idx, row in potential_dupes.iterrows():
        dist = calculate_distance(new_report['latitude'], new_report['longitude'], row['latitude'], row['longitude'])
        if dist <= dist_threshold:
            sim = get_semantic_similarity(new_report['description'], row['description'])
            if sim >= sim_threshold:
                return True, idx
                
    return False, None
