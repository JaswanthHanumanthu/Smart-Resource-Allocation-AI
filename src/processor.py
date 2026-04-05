import google.generativeai as genai
import json
import streamlit as st
import pandas as pd

def process_ngo_notes(messy_text: str, api_key: str = None) -> dict:
    """
    Takes messy NGO survey notes and uses the Gemini API to extract structured data.
    """
    # Configure API - Prioritize Secure Secrets
    try:
        # Check if already configured via app.py secrets check
        if not api_key and 'GOOGLE_API_KEY' not in st.secrets:
             raise Exception("No API Key Provided")
        
        if api_key:
            genai.configure(api_key=api_key)
        elif 'GOOGLE_API_KEY' in st.secrets:
            genai.configure(api_key=st.secrets['GOOGLE_API_KEY'])
    except Exception:
        # Fallback simulated response if no API key is present for the hackathon
        import time
        time.sleep(1) # simulate network delay
        return {
            "urgency": 8,
            "category": "Food",
            "latitude": 37.7749,
            "longitude": -122.4194,
            "description": "[SIMULATED - NO API KEY] Detected severe food shortage affecting 50 families.",
            "note": "Provide GOOGLE_API_KEY in Streamlit Secrets to use the live model."
        }
        
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = f"""
    You are an AI data extractor and translator with a strict Privacy First policy. 
    1. Analyze the following messy NGO survey notes (potentially in various languages).
    2. Detect the language of the notes.
    3. Extract the underlying event needs and translate them into English while preserving the original context.
    4. ANONYMIZE: If the notes contain any Personally Identifiable Information (PII) such as full names, phone numbers, or ID numbers, REPLACE them with "[REDACTED]".
    
    The JSON structure must exactly match the following:
    {{
        "urgency": <integer from 1 to 10>,
        "category": <one of "Food", "Medical", "Shelter", "General">,
        "latitude": <float>,
        "longitude": <float>,
        "description": <string summarizing the actual problem in English with all PII [REDACTED]>,
        "detected_language": <string, e.g., "Hindi", "Spanish", "English">,
        "people_affected": <integer, estimate how many human lives are impacted by this need>,
        "human_context_summary": <string, brief qualitative description, e.g. "Focuses on 5 elderly residents with mobility issues.">
    }}
    
    Messy Notes:
    "{messy_text}"
    
    Output strictly valid JSON and nothing else.
    """
    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        # Clean up possible markdown formatting
        if text.startswith("```json"):
            text = text[7:]
        if text.endswith("```"):
            text = text[:-3]
        return json.loads(text.strip())
    except Exception as e:
        return {"error": str(e)}

def process_field_audio(audio_data: bytes) -> dict:
    """Transcription and extraction from a field audio memo."""
    try:
        # Gemini 1.5 Flash can process audio directly
        model = genai.GenerativeModel('gemini-1.5-flash')
        # We need a mime type, assuming wav/mp3 for this prototype
        response = model.generate_content([
            "Analyze this humanitarian field recording. Extract: category (Medical, Food, Shelter, General), urgency (1-10), coordinates (if mentioned), and a brief English summary. Respond with ONLY JSON.",
            {"mime_type": "audio/mpeg", "data": audio_data}
        ])
        clean_res = response.text.replace('```json', '').replace('```', '').strip()
        import json
        return json.loads(clean_res)
    except Exception as e:
        return {"error": f"Audio Analysis Failed: {str(e)}"}

def process_field_image(image_bytes: bytes) -> dict:
    """Multimodal vision extraction with Severity Scoring."""
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = """
        You are a Humanitarian Data Expert. Analyze the attached mission photo.
        
        1. Estimate a Severity Score (1-10) based on visible damage/risk. 
        2. Categorize the incident (Food, Medical, Shelter, General).
        3. Extract any visible text context (signs, documents).
        4. Provide an English summary.
        
        Respond with ONLY JSON:
        {
            "urgency": (severity score 1-10),
            "category": "category string",
            "latitude": 37.77, (default if unknown),
            "longitude": -122.42, (default if unknown),
            "description": "brief situational summary",
            "detected_language": "English",
            "people_affected": (estimate from photo)
        }
        """
        
        img = {"mime_type": "image/jpeg", "data": image_bytes}
        response = model.generate_content([prompt, img])
        clean_res = response.text.replace('```json', '').replace('```', '').strip()
        import json
        return json.loads(clean_res)
    except Exception as e:
        return {"error": str(e)}

def process_survey_image(pil_image, api_key: str = None) -> dict:
    """
    Takes a PIL Image of a handwritten NGO survey and uses Gemini 1.5 Flash to extract structured data.
    """
    used_key = api_key or os.environ.get("GEMINI_API_KEY")
    if used_key:
        genai.configure(api_key=used_key)
    else:
        # Fallback simulation for hackathon prototype
        import time
        time.sleep(1.5)
        return {
            "urgency": 9,
            "category": "Medical",
            "latitude": 37.8044,
            "longitude": -122.2712,
            "description": "[SIMULATED OCR] Handwriting read: Urgent medical supplies needed immediately for 15 wounded.",
            "note": "Provide GEMINI_API_KEY to use the live multimodal model."
        }
        
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = """
    You are an expert AI multimodal data extractor and translator with a strict Privacy First policy. 
    1. Analyze the provided image of a handwritten NGO survey (potentially in various languages).
    2. Detect the language of the handwriting.
    3. Extract the underlying event needs and translate the handwriting into English while preserving the original context.
    4. ANONYMIZE: If the handwriting contains any Personally Identifiable Information (PII) such as full names, phone numbers, or ID numbers, REPLACE them with "[REDACTED]".
    
    The JSON structure must exactly match the following:
    {
        "urgency": <integer from 1 to 10 based on text severity>,
        "category": <one of "Food", "Medical", "Shelter", "General">,
        "latitude": <float, guess roughly if only a city name is provided, default to 37.77 if unknown>,
        "longitude": <float, guess roughly if only a city name is provided, default to -122.42 if unknown>,
        "description": <string summarizing the handwriting content in English with all PII [REDACTED]>,
        "detected_language": <string, e.g., "Hindi", "Spanish", "English">
    }
    
    Output strictly valid JSON and nothing else.
    """
    try:
        response = model.generate_content([prompt, pil_image])
        text = response.text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.endswith("```"):
            text = text[:-3]
        return json.loads(text.strip())
    except Exception as e:
        return {"error": str(e)}

def summarize_situation_ai(df: pd.DataFrame, api_key: str = None) -> str:
    """
    Uses Gemini to generate a fast 2-sentence executive summary of the CSV data/dataframe state.
    """
    used_key = api_key or os.environ.get("GEMINI_API_KEY")
    if not used_key:
        import time
        time.sleep(1.5)
        unmet_df = df[df['status']=='Pending']
        pending_ct = len(unmet_df)
        if pending_ct == 0:
            return "[SIMULATION] Status Nominal: All logistical queues are clear and perfectly resourced. Maintain current operational distribution strategy."
        else:
            top_gap = unmet_df['category'].mode()[0] if not unmet_df['category'].empty else 'General'
            return f"[SIMULATION] Warning: High urgency needs are visibly rising across sectors with {pending_ct} items currently pending dispatch. Strongly recommend shifting resources into {top_gap} distribution immediately."
            
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        report_data = df.groupby(['category', 'status']).size().to_string()
        prompt = f"""You are an AI logistics director for an NGO. Look at the following raw aggregation of community needs.
Write EXACTLY a punchy 2-sentence executive summary emphasizing what is most critical, and recommending where to cleanly shift resources today.
Data counts:
{report_data}"""
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return "Error analyzing data: " + str(e)

def chat_with_data(query: str, df: pd.DataFrame, api_key: str = None) -> str:
    used_key = api_key or os.environ.get("GEMINI_API_KEY")
    if not used_key:
        import time
        time.sleep(1)
        return "[SIMULATION] Based on my scan of the live database, Dr. Alice Morgan is the optimal choice for the current fire relief task due to her Medical specialization and close geographic proximity to the incident."
        
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        # Sub-select columns to fit context window smoothly
        cols = [c for c in ['category', 'urgency', 'status', 'description', 'latitude', 'longitude'] if c in df.columns]
        report_data = df.to_string(columns=cols) if not df.empty else "Database is currently empty."
        
        prompt = f"""You are an AI assistant for an NGO Triage system. Answer the user's question accurately using ONLY the live data provided below.
If you don't know the answer based on the data, say so gracefully. Keep the response very concise and helpful.

Current Active Database:
{report_data}

User Query: {query}"""
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"Sorry, I encountered an issue checking the data: {str(e)}"


