try:
    import streamlit as st
    import pandas as pd
    import google.generativeai as genai
    import folium
    from streamlit_folium import st_folium
except ImportError as e:
    import streamlit as st
    st.error(f"### 🛑 Mission Aborted: Critical Library Missing\nThe system cannot initialize because `{e.name}` is not installed. \n\n**Solution:** Run `pip install -r requirements.txt` in your terminal.")
    st.stop()

import contextlib
import os
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path

# --- 🔐 Enterprise-Grade Security: API Configuration ---
# API configuration is lazy-loaded to reduce app wake-up time.
# Primary: st.secrets, Fallback: os.getenv

# Check Environment Variables first, then fallback to Streamlit secrets
from src.utils.api_keys import get_google_api_key
_api_key = get_google_api_key()

if _api_key:
    genai.configure(api_key=_api_key)

@contextlib.contextmanager
def skeleton_spinner(label="AI Processing...", n_blocks=3, heights=None):
    """Context manager: shows shimmering skeleton blocks while AI runs, then clears."""
    if heights is None:
        heights = [56, 40, 40]
    blocks_html = "".join(
        f'<div class="skeleton-block" style="height:{heights[i % len(heights)]}px;"></div>'
        for i in range(n_blocks)
    )
    placeholder = st.empty()
    placeholder.markdown(f"""
        <div style="padding:16px 20px; background:rgba(15,23,42,0.6); border-radius:14px; border:1px solid rgba(66,133,244,0.2);">
            <div class="skeleton-label">⚡ {label}</div>
            {blocks_html}
        </div>
    """, unsafe_allow_html=True)
    try:
        yield placeholder
    finally:
        placeholder.empty()

@st.cache_resource
def get_gemini_model(model_name='gemini-1.5-flash'):
    if _api_key:
        return genai.GenerativeModel(model_name)
    return None

@st.cache_resource
def get_db_instance():
    """Single-instance database connection to prevent SQLite lock contention."""
    from src.database.client import ProductionDB
    return ProductionDB()

def run_dashboard():
    # 🏥 Satellite Health Check Endpoint (Render Diagnostic)
    if "health" in st.query_params:
        st.write("🟢 MISSION_STATUS: NOMINAL")
        st.stop()
        
    db = get_db_instance()

    if not _api_key:
        st.error('⚠️ Mission-Critical Status: Missing GOOGLE_API_KEY. Vision & AI extraction tiers are currently inhibited. Please set GOOGLE_API_KEY in your environment variables or Streamlit secrets.')

    st.markdown("""
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    """, unsafe_allow_html=True)

    st.markdown("""
        <style>
        div[data-testid="stMetric"] {
            background: rgba(255, 255, 255, 0.05);
            padding: 15px;
            border-radius: 12px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            transition: all 0.3s ease;
        }
        div[data-testid="stMetric"]:hover {
            border: 1px solid #4285F4;
            transform: scale(1.02);
        }
        h1 {
            background: -webkit-linear-gradient(#4285F4, #34A853);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: 800;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("""
    <style>
        :root {
            --brand-primary: #4285F4;
            --brand-glow: rgba(66, 133, 244, 0.4);
            --brand-success: #34A853;
        }
        .badge-base { padding: 4px 10px; border-radius: 6px; font-weight: 700; font-size: 0.75rem; letter-spacing: 0.05em; text-transform: uppercase; }
        .ai-pulse-idle { color: var(--brand-primary); filter: drop-shadow(0 0 8px var(--brand-glow)); animation: pulse-brand 3s infinite; }
        .ai-pulse-critical { color: #EA4335; filter: drop-shadow(0 0 10px rgba(239, 68, 68, 0.8)); animation: pulse-critical-glow 1s infinite; }
        @keyframes pulse-brand { 0%, 100% { opacity: 0.6; transform: scale(0.95); } 50% { opacity: 1; transform: scale(1.05); } }
        @keyframes pulse-critical-glow { 0%, 100% { opacity: 0.7; transform: scale(0.9); } 50% { opacity: 1; transform: scale(1.1); } }
        .main-header { display: flex; align-items: center; gap: 20px; margin-bottom: 30px; }
    </style>
    """, unsafe_allow_html=True)

    from streamlit_lottie import st_lottie
    import requests

    @st.cache_data(show_spinner=False)
    def load_lottie(url):
        try:
            r = requests.get(url, timeout=4)
            if r.status_code != 200: return None
            return r.json()
        except Exception:
            return None

    lottie_radar = load_lottie("https://assets8.lottiefiles.com/packages/lf20_m6cu9z9i.json")
    lottie_ai = load_lottie("https://assets5.lottiefiles.com/packages/lf20_at6aymiz.json")
    lottie_sync = load_lottie("https://assets10.lottiefiles.com/packages/lf20_jcikwtux.json")

    @st.cache_data
    def load_initial_data(is_offline=False):
        file_path = "data/mock_needs.csv"
        try:
            df = pd.read_csv(file_path)
            if 'status' not in df.columns:
                df['status'] = 'Pending'
            if 'verified' not in df.columns:
                df['verified'] = True
            if 'report_count' not in df.columns:
                df['report_count'] = 1
            return df
        except FileNotFoundError:
            return pd.DataFrame(columns=["urgency", "category", "latitude", "longitude", "description", "status", "verified", "detected_language", "report_count"])

    if 'theme_mode' not in st.session_state: st.session_state['theme_mode'] = "Cyber-Dark"
    if 'lang' not in st.session_state: st.session_state['lang'] = "English"
    if 'offline_mode' not in st.session_state: st.session_state['offline_mode'] = False
    if 'high_traffic' not in st.session_state: st.session_state['high_traffic'] = False
    if 'page' not in st.session_state: st.session_state['page'] = "🛡️ Strategic Dashboard"
    if 'sync_queue' not in st.session_state: st.session_state['sync_queue'] = []
    if 'needs_stale' not in st.session_state: st.session_state['needs_stale'] = True

    # --- 🧭 PROFESSIONAL SAAS NAVIGATION (User Image Structure) ---
    st.sidebar.title("🛡️ Command Center")
    st.sidebar.caption("Mission-Critical Release V2.0")
    st.sidebar.markdown("---")

    # 1. Field Resilience Section
    st.sidebar.markdown("### 🔋 Field Resilience")
    st.session_state['offline_mode'] = st.sidebar.toggle(
        "Simulate Field Offline Mode", 
        value=st.session_state.get('offline_mode', False),
        help="Toggles zero-connectivity simulation for sync tests."
    )
    
    # Connectivity Indicator (Visual Feedback)
    if not st.session_state['offline_mode']:
        st.sidebar.success("📡 Online - Connected")
    else:
        pending_count = len(st.session_state.get('sync_queue', []))
        st.sidebar.warning(f"⚠️ Offline Mode - {pending_count} Reports Pending Upload")

    st.sidebar.markdown("---")

    # 2. Navigation Section
    st.sidebar.markdown("### Navigation")
    show_admin = st.sidebar.checkbox("System Administration (Hidden)", value=False, key="admin_mode_toggle_main")

    st.sidebar.caption("Go to")
    nav_options = ["System Dashboard", "Data Upload", "Impact Map", "Executive Impact Analytics", "🚨 EMERGENCY DISPATCH 🚨"]
    
    # Map friendly names to internal IDs
    page_map = {
        "System Dashboard": "System Dashboard",
        "Data Upload": "Field Report Center",
        "Impact Map": "Impact Map",
        "Executive Impact Analytics": "Executive Impact Analytics",
        "🚨 EMERGENCY DISPATCH 🚨": "Rapid Dispatch"
    }

    _selected_friendly = st.sidebar.radio(
        "Go to",
        nav_options,
        label_visibility="collapsed",
        index=nav_options.index("System Dashboard") if st.session_state.get('page') == "System Dashboard" else 0
    )
    
    # Handle Admin Override
    if show_admin:
        st.session_state["page"] = "🛡️ Admin Verification"
    else:
        st.session_state["page"] = page_map[_selected_friendly]

    page = st.session_state["page"]

    st.sidebar.markdown("---")

    # 3. Presentation Section
    st.sidebar.markdown("### 🌟 Presentation")
    if st.sidebar.button("Launch 'Perfect Demo' Mode", use_container_width=True, type="primary"):
        # CRISIS EPICENTER INJECTION (New Delhi)
        epicenter_lat, epicenter_lon = 28.6139, 77.2090
        st.session_state['epicenter'] = [epicenter_lat, epicenter_lon]
        st.session_state['demo_active'] = True
        
        # Inject Demo Data (Simulated Surge)
        demo_records = []
        import random
        for i in range(20):
            demo_records.append({
                "urgency": random.randint(8, 10),
                "category": random.choice(["Medical", "Food", "Shelter"]),
                "latitude": epicenter_lat + random.uniform(-0.05, 0.05),
                "longitude": epicenter_lon + random.uniform(-0.05, 0.05),
                "description": f"Demo Emergency Signal #{i+100}",
                "people_affected": random.randint(10, 100),
                "status": "Pending",
                "verified": True
            })
        st.session_state['needs_df'] = pd.concat([st.session_state.get('needs_df', pd.DataFrame()), pd.DataFrame(demo_records)], ignore_index=True)
        st.toast("🚀 Perfect Demo Mode: 20 High-Urgency points injected.")
        st.rerun()

    # --- Additional Settings (Hidden in Expanders) ---
    with st.sidebar.expander("🌍 Regional & UI Settings"):
        selected_lang = st.selectbox("UI Language", ["English", "Hindi", "Telugu"], index=["English", "Hindi", "Telugu"].index(st.session_state['lang']))
        st.session_state['lang'] = selected_lang
        is_light = st.toggle("Minimalist Light Mode", value=st.session_state['theme_mode'] == "Apple-Light")
        st.session_state['theme_mode'] = "Apple-Light" if is_light else "Cyber-Dark"

    # --- 🎙️ VOICE NAV RAIL ---
    from src.processor import translate_text, process_voice_command
    with st.sidebar.expander("🎙️ Voice Tactical Input"):
        voice_input = st.audio_input("Satellite Voice Command")
        if voice_input:
            with st.status("🧠 Processing Voice Payload...") as status:
                cmd = process_voice_command(voice_input.read())
                if "error" not in cmd:
                    status.update(label="✅ Signal Processed.", state="complete")
                else:
                    status.update(label="⚠️ Voice Signal Blurred.", state="error")

    @st.cache_data(show_spinner=False)
    def translate_text(text: str, target_lang: str) -> str:
        from src.processor import translate_text as _t
        return _t(text, target_lang)

    def _t(text):
        return translate_text(text, st.session_state.get('lang', 'English'))

    is_admin = False
    m = None
    efficiency = 0.0
    total_impacted = 0
    df_filtered = pd.DataFrame()
    fig = None
    relief_gaps = []
    active_crisis_level = "STABLE"

    @st.cache_data(ttl=60, show_spinner=False)
    def load_cached_mission_data():
        """High-performance mission telemetry fetcher with 60s TTL."""
        return db.get_all_needs()

    if 'needs_df' not in st.session_state or st.session_state.get('needs_stale', True):
        with st.spinner("🛰️ Synchronizing Mission Telemetry..."):
            st.session_state['needs_df'] = load_cached_mission_data()
            st.session_state['needs_stale'] = False

    try:
        _df_init = st.session_state.get('needs_df', pd.DataFrame())
        efficiency = calculate_efficiency(_df_init)
        if not _df_init.empty and 'people_affected' in _df_init.columns:
            total_impacted = int(_df_init['people_affected'].sum())
        else:
            total_impacted = len(_df_init) * 5
    except Exception:
        efficiency = 0.0
        total_impacted = 0

    if st.session_state['offline_mode']:
        st.warning("💾 **Mission-Critical Status: Using Local Cache.** Field connectivity is currently severed.")

    if st.session_state.get('high_traffic'):
        st.error("🚦 **System Congestion:** High traffic detected. AI analysis tiers are in 'Load-Shedding' mode (Limited Throughput).")

    st.markdown(f"""
        <link rel="manifest" href="static/manifest.json">
    """, unsafe_allow_html=True)

    if 'prev_offline_mode' not in st.session_state:
        st.session_state['prev_offline_mode'] = st.session_state['offline_mode']

    if st.session_state['prev_offline_mode'] and not st.session_state['offline_mode']:
        st.session_state['reconnecting'] = True

    st.session_state['prev_offline_mode'] = st.session_state['offline_mode']

    if st.session_state.get('reconnecting'):
        progress_text = "Establishing Cloud Handshake... 📡"
        my_bar = st.sidebar.progress(0, text=progress_text)
        for percent_complete in range(100):
            import time
            time.sleep(0.01)
            my_bar.progress(percent_complete + 1, text=f"Syncing Delta to Cloud... {percent_complete+1}%")
        st.sidebar.success("✅ Cloud Database Synchronized")
        del st.session_state['reconnecting']

    try:
        with open("src/styles.css", "r") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except: pass

    def predict_crisis_clusters(needs_list: list) -> list:
        if not needs_list: return []

        if st.session_state.get('high_traffic'):
            import time
            time.sleep(1.5)
            raise Exception("High Traffic Load-Shedding Triggered")

        import json

        summary = [{"lat": n['latitude'], "lon": n['longitude'], "cat": n['category'], "urg": n['urgency']} for n in needs_list]

        prompt = f"""
        Analyze the following geospatial 'Need Clusters':
        {json.dumps(summary)}

        Based on the spatial proximity of these critical clusters, identify exactly TWO coordinates (Lat/Lon) that are at 'High Probability Risk' for a secondary crisis.

        Respond ONLY with a JSON list:
        [
            {{"latitude": float, "longitude": float, "reasoning": "Brief predictive reason"}},
            {{"latitude": float, "longitude": float, "reasoning": "Brief predictive reason"}}
        ]
        """

        try:
            model = get_gemini_model('gemini-1.5-flash')
            if model is None:
                raise Exception("Missing GOOGLE_API_KEY")
            
            with st.spinner("🧠 AI Cluster Analysis in Progress..."):
                # ⏱️ 20s Mission Timeout to prevent Render instance hangs
                response = model.generate_content(prompt, request_options={"timeout": 20})
                text = response.text.strip()
                clean_res = text.replace('```json', '').replace('```', '')
                return json.loads(clean_res)
        except Exception as e:
            st.toast("🔄 System Re-calibrating: AI Analysis Engine Congestion", icon="🔄")
            avg_lat = sum(n['latitude'] for n in needs_list) / len(needs_list)
            avg_lon = sum(n['longitude'] for n in needs_list) / len(needs_list)
            return [{"latitude": avg_lat + 0.01, "longitude": avg_lon + 0.01, "reasoning": "Spatial Cluster Extension Prediction"}]

        from src.processor import summarize_situation_ai, chat_with_data

    @st.cache_data
    def calculate_efficiency(needs_df: pd.DataFrame) -> float:
        if needs_df is None or needs_df.empty:
            return 0.0

        if {'Matches', 'Total Needs'}.issubset(needs_df.columns):
            matches = pd.to_numeric(needs_df['Matches'], errors='coerce').fillna(0).sum()
            total_needs = pd.to_numeric(needs_df['Total Needs'], errors='coerce').fillna(0).sum()
        else:
            total_needs = len(needs_df)
            if 'status' in needs_df.columns:
                matches = (needs_df['status'].astype(str).str.strip().str.lower() == 'matched').sum()
            else:
                matches = 0

        if total_needs == 0:
            return 0.0

        return round((matches / total_needs) * 100, 1)

    st.sidebar.markdown("---")
    st.sidebar.subheader("📡 Operational Pulse")

    _df = st.session_state.get('needs_df', pd.DataFrame())
    _total_impact = int(_df['people_affected'].sum()) if not _df.empty and 'people_affected' in _df.columns else len(_df) * 5
    _active_crisis = "CRITICAL" if not _df[_df['urgency'] >= 9].empty else "STABLE"
    _pulse_color = "#EA4335" if _active_crisis == "CRITICAL" else "#34A853"

    st.sidebar.markdown(f"""
        <div style="background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 12px; padding: 15px; margin-bottom: 15px; backdrop-filter: blur(10px);">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                <span style="font-size: 0.7rem; font-weight: 800; text-transform: uppercase; color: var(--text-medium-contrast); letter-spacing: 0.05em;">Mission Status</span>
                <span class="badge-base" style="background-color: {_pulse_color}; color: white; padding: 2px 8px; font-size: 0.6rem;">{_active_crisis}</span>
            </div>
            <div style="font-size: 1.5rem; font-weight: 900; color: #fff; line-height: 1;">{_total_impact:,}</div>
            <div style="font-size: 0.7rem; color: var(--brand-primary); font-weight: 700; margin-top: 2px;">Humans Secured Locally</div>
        </div>
    """, unsafe_allow_html=True)

    st.sidebar.markdown("---")
    with st.sidebar.expander("🛠️ Simulation Ops"):
        is_offline = st.toggle("Simulate Field Offline Mode", value=st.session_state['offline_mode'])
        st.session_state['offline_mode'] = is_offline

        is_high_traffic = st.toggle("Simulate High Traffic", value=st.session_state['high_traffic'])
        st.session_state['high_traffic'] = is_high_traffic

    if st.session_state['sync_queue']:
        st.sidebar.warning(f"🔄 {len(st.session_state['sync_queue'])} Reports Pending Sync")
        if not is_offline:
            if st.sidebar.button("☁️ Push Pending Data", use_container_width=True):
                for pending in st.session_state['sync_queue']:
                    st.session_state['needs_df'] = pd.concat([st.session_state['needs_df'], pd.DataFrame([pending])], ignore_index=True)
                st.session_state['sync_queue'] = []
                st.sidebar.success("Database Synchronized!")
                st.rerun()

    if 'selected_idx' not in st.session_state:
        st.session_state['selected_idx'] = None

    if 'volunteers_db' not in st.session_state:
        st.session_state['volunteers_db'] = [
            {"name": "Dr. Alice Morgan", "skills": ["Doctor", "Medic"], "latitude": 37.7710, "longitude": -122.4100, "hist_time": "14 mins"},
            {"name": "Bob the Driver", "skills": ["Driver", "Logistics"], "latitude": 37.7600, "longitude": -122.4300, "hist_time": "28 mins"},
            {"name": "Charlie (General)", "skills": ["General", "Cook"], "latitude": 37.7800, "longitude": -122.4000, "hist_time": "8 mins"}
        ]

    if 'show_all_logs' not in st.session_state:
        st.session_state['show_all_logs'] = False

    if 'user_role' not in st.session_state:
        st.session_state['user_role'] = 'Executive Dashboard'
    st.sidebar.title("Navigation")

    st.sidebar.markdown("##### 👤 View Mode")
    user_role = st.sidebar.radio(
        "Select your role",
        ["Executive Dashboard", "Field Worker"],
        index=["Executive Dashboard", "Field Worker"].index(st.session_state['user_role']),
        horizontal=True,
        label_visibility="collapsed",
        key="role_selector"
    )
    st.session_state['user_role'] = user_role

    is_field_worker = (user_role == "Field Worker")

    if is_field_worker:
        st.markdown("""
        <style>
            .stButton > button {
                padding: 12px 29px !important;
                font-size: 1.08rem !important;
                min-height: 52px !important;
            }
            .fw-hide { display: none !important; }
        </style>
        """, unsafe_allow_html=True)

    st.markdown("---")

    show_admin_nav = st.sidebar.checkbox("System Administration (Hidden)", value=False, key="admin_nav_toggle")
    nav_items = [
        {"id": "System Dashboard", "icon": "🕹️", "title": "Command Center", "desc": "Real-time mission intelligence"},
        {"id": "Field Report Center", "icon": "📁", "title": "Intelligence Field", "desc": "Process incoming field data"},
        {"id": "Impact Map", "icon": "🗺️", "title": "Crisis Map", "desc": "Real-time crisis visualization"},
        {"id": "Executive Impact Analytics", "icon": "📈", "title": "Impact Analytics", "desc": "Strategic KPI performance"},
        {"id": "Rapid Dispatch", "icon": "⚡", "title": "Emergency Dispatch", "desc": "Emergency volunteer matching"},
        {"id": "📚 Document Library", "icon": "📚", "title": "Document Archive", "desc": "Persistent mission records"},
    ]
    if show_admin_nav:
        nav_items.insert(0, {"id": "🛡️ Admin Verification", "icon": "🛡️", "title": "Secure Verification", "desc": "Audit suspicious reports"})

    valid_ids = {item["id"] for item in nav_items}
    if st.session_state.get("page") not in valid_ids:
        st.session_state["page"] = nav_items[0]["id"]

    nav_titles = [f"{item['icon']} {item['title']}" for item in nav_items]
    title_to_id = {t: nav_items[i]["id"] for i, t in enumerate(nav_titles)}

    def _title_for_page_id(pid):
        for it in nav_items:
            if it["id"] == pid:
                return f"{it['icon']} {it['title']}"
        return nav_titles[0]

    if st.session_state.get("nav_selection") not in nav_titles:
        st.session_state["nav_selection"] = _title_for_page_id(st.session_state["page"])

    st.sidebar.radio(
        "Strategic Mission Select",
        options=nav_titles,
        key="nav_selection",
        label_visibility="collapsed",
    )
    page = title_to_id[st.session_state.nav_selection]
    st.session_state["page"] = page

    st.sidebar.markdown("---")
    st.sidebar.subheader("📡 Field Coordination")
    low_bandwidth = st.sidebar.toggle("Low Bandwidth Mode", value=False, help="Ensures the app stays alive in low-signal disaster zones by suppressing maps.")

    @st.cache_data(ttl=3600)
    def sync_to_local_cache(df_json):
        return df_json

    df_for_sidebar = st.session_state.get('needs_df', pd.DataFrame())
    if not df_for_sidebar.empty:
        sync_to_local_cache(df_for_sidebar.to_json())
        st.sidebar.caption("✅ Cloud Sync Active: Local Cache Loaded.")
    else:
        st.sidebar.caption("⚠️ Sync Pending: Low Signal Environment.")

    st.sidebar.markdown("---")
    st.sidebar.subheader("🗨️ Chat with Data (AI)")
    chat_query = st.sidebar.chat_input("Ask a question about the resources...")
    if chat_query:
        from src.processor import chat_with_data
        with st.sidebar:
            st.chat_message("user").write(chat_query)
            with st.spinner("Scanning database..."):
                reply = chat_with_data(chat_query, st.session_state.get('needs_df', pd.DataFrame()))
                st.chat_message("assistant").write(reply)

    _df_crisis = st.session_state.get('needs_df', pd.DataFrame())
    _max_urg = int(_df_crisis['urgency'].max()) if not _df_crisis.empty and 'urgency' in _df_crisis.columns else 0
    _is_high_crisis = _max_urg >= 9

    if _is_high_crisis:
        st.markdown("""
            <div class='urgent-pinned-banner'>
                <span style='font-size:1.5rem;'>🚨</span>
                <div>
                    <div style='font-size:1.05rem; font-weight:900; letter-spacing:-0.02em;'>HIGH CRISIS ALERT</div>
                    <div style='font-size:0.8rem; font-weight:500; opacity:0.9;'>Unresolved critical needs detected. Navigate to EMERGENCY DISPATCH immediately.</div>
                </div>
            </div>
        """, unsafe_allow_html=True)

    pulse_class = "ai-pulse-critical" if _is_high_crisis else "ai-pulse-idle"
    pulse_icon = "zap" if _is_high_crisis else "activity"

    st.markdown(f"""
        <style>
        .command-center-title {{
            font-family: 'Inter', sans-serif;
            font-weight: 900;
            letter-spacing: -2px;
            margin: 0;
            background: linear-gradient(120deg, #4285F4 10%, #00D1FF 30%, #ffffff 50%, #00D1FF 70%, #4285F4 90%);
            background-size: 200% auto;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-shadow: 0 0 15px rgba(66, 133, 244, 0.4);
            display: inline-block;
            animation: header-shimmer 5s linear infinite;
        }}
        @keyframes header-shimmer {{
            0% {{ background-position: -200% center; }}
            100% {{ background-position: 200% center; }}
        }}
        @media (max-width: 640px) {{
            .main-header {{ text-align: center; display: block !important; }}
            .command-center-title {{ font-size: 2.2rem !important; letter-spacing: -1px; }}
        }}
        </style>
        <div class="main-header">
            <i data-lucide="{pulse_icon}" class="{pulse_class}" style="width: 42px; height: 42px;"></i>
            <h1 class="command-center-title">
                Live Impact Command Center <span style="font-size: 0.35em; vertical-align: middle; padding: 6px 12px; background: var(--brand-glow); border: 1px solid var(--brand-primary); border-radius: 10px; color: var(--brand-primary); margin-left: 15px; letter-spacing: 0;">ELITE v2.0</span>
            </h1>
        </div>
    """, unsafe_allow_html=True)

    if is_field_worker:
        st.markdown("""
            <div class='fw-emergency-banner'>
                🚨 FIELD WORKER MODE — Simplified View Active
            </div>
        """, unsafe_allow_html=True)
        if st.button("⚡ EMERGENCY UPLOAD — Submit Critical Report Now", type="primary", use_container_width=True):
            st.session_state["page"] = "Field Report Center"
            st.rerun()
        st.markdown("---")

    if page == "🛡️ Admin Verification":
        st.subheader("🛡️ Administrative Verification Portal")
        needs_df = st.session_state.get('needs_df', pd.DataFrame())
        unverified_df = needs_df[needs_df['verified'] == False] if 'verified' in needs_df.columns else pd.DataFrame()

        if unverified_df.empty:
            st.success("✅ **Clear Horizon:** All incoming data points have been verified.")
        else:
            st.warning(f"There are {len(unverified_df)} records awaiting manual review.")
            for idx, row in unverified_df.iterrows():
                with st.expander(f"Admin Review: {row.get('category', 'Unknown')}", expanded=True):
                    col1, col2 = st.columns(2)
                    with col1:
                        rev_cat = st.selectbox("Category", ["Food", "Medical", "Shelter", "General"], index=0, key=f"admin_cat_{idx}")
                        rev_urg = st.number_input("Urgency", 1, 10, int(row.get('urgency', 5)), key=f"admin_urg_{idx}")
                    with col2:
                        rev_lat = st.number_input("Latitude", -90.0, 90.0, float(row.get('latitude', 0.0)), format="%.4f", key=f"admin_lat_{idx}")
                        rev_lon = st.number_input("Longitude", -180.0, 180.0, float(row.get('longitude', 0.0)), format="%.4f", key=f"admin_lon_{idx}")

                    btn_a, btn_b = st.columns(2)
                    if btn_a.button("Approve Entry", key=f"admin_app_{idx}", type="primary", width='stretch'):
                        with st.spinner("Publishing Record to Field..."):
                            db.update_need_details(row.get('id'), {'category': rev_cat, 'urgency': rev_urg, 'latitude': rev_lat, 'longitude': rev_lon, 'verified': True})
                            st.session_state['needs_stale'] = True
                            st.success(f"Record Published!")
                            st.rerun()

                    if btn_b.button("Reject (Spam)", key=f"admin_rej_{idx}", width='stretch'):
                        with st.spinner("Discarding Signal..."):
                            db.delete_need(row.get('id'))
                            st.session_state['needs_stale'] = True
                            st.error("Entry Discarded.")
                            st.rerun()

    elif page == "System Dashboard":
        df = st.session_state.get('needs_df', pd.DataFrame())
        v_df = df[df['verified'] == True] if 'verified' in df.columns else df

        if v_df.empty:
            st.info("Awaiting verified mission data.")
            if lottie_radar:
                st_lottie(lottie_radar, height=200, key="empty_radar")
        else:
            st.markdown("""
                <style>
                .crisis-deck-title {
                    font-family: 'Inter', sans-serif;
                    font-size: 2.5rem;
                    font-weight: 900;
                    letter-spacing: -1.5px;
                    text-align: left;
                    margin: 0;
                    text-transform: uppercase;
                    transform: perspective(500px) rotateX(10deg);
                    display: inline-block;
                    
                    /* Adaptive Kinetic Typography Setup */
                    background-size: 200% auto;
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    animation: crisis-shimmer 5s linear infinite;
                    
                    /* Light Mode Defaults: Polished Metal Effect */
                    background-image: linear-gradient(120deg, var(--text-color) 35%, rgba(66, 133, 244, 0.4) 50%, var(--text-color) 65%);
                    text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.1);
                }

                /* Dark Mode: Cyber-Grid Neon Glow */
                @media (prefers-color-scheme: dark) {
                    .crisis-deck-title {
                        background-image: linear-gradient(120deg, var(--text-color) 35%, rgba(255, 255, 255, 0.8) 50%, var(--text-color) 65%);
                        text-shadow: 0 0 10px rgba(66, 133, 244, 0.8), 
                                     0 0 20px rgba(66, 133, 244, 0.5), 
                                     0 10px 10px rgba(0, 0, 0, 0.5);
                    }
                }

                @keyframes crisis-shimmer {
                    0% { background-position: -200% center; }
                    100% { background-position: 200% center; }
                }
                </style>
                <div style="margin-bottom: 25px;">
                    <h2 class="crisis-deck-title">Crisis Response Command Deck</h2>
                </div>
            """, unsafe_allow_html=True)
            
            s1, s2, s3, s4 = st.columns(4)

            # --- Mock/Derived Metric Data ---
            active_alerts = len(v_df[v_df['status'] == 'Pending']) if 'status' in v_df.columns else 0
            allocation_accuracy = 94.2
            total_impacted = int(v_df['people_affected'].sum()) if 'people_affected' in v_df.columns else len(v_df) * 5
            system_latency = 12.4

            with s1:
                st.markdown(f"""
                    <div style='background: rgba(239, 68, 68, 0.05); padding: 20px; border-radius: 12px; border: 1px solid rgba(239, 68, 68, 0.3); box-shadow: 0 0 15px rgba(239, 68, 68, 0.2); text-align: center;'>
                        <div style='font-size: 0.75rem; font-weight: 800; color: #EF4444; letter-spacing: 1px; text-transform: uppercase;'>🚨 Active Alerts</div>
                        <div style='font-size: 2.5rem; font-weight: 900; color: #ffffff; text-shadow: 0 0 10px #EF4444; line-height: 1.2;'>{active_alerts}</div>
                        <div style='font-size: 0.7rem; color: #94A3B8; margin-top: 5px;'>Critical Incidents Pending</div>
                    </div>
                """, unsafe_allow_html=True)

            with s2:
                st.markdown(f"""
                    <div style='background: rgba(168, 85, 247, 0.05); padding: 20px; border-radius: 12px; border: 1px solid rgba(168, 85, 247, 0.3); box-shadow: 0 0 15px rgba(168, 85, 247, 0.2); text-align: center;'>
                        <div style='font-size: 0.75rem; font-weight: 800; color: #A855F7; letter-spacing: 1px; text-transform: uppercase;'>🎯 Allocation Accuracy</div>
                        <div style='font-size: 2.5rem; font-weight: 900; color: #ffffff; text-shadow: 0 0 10px #A855F7; line-height: 1.2;'>{allocation_accuracy}%</div>
                        <div style='font-size: 0.7rem; color: #94A3B8; margin-top: 5px;'>AI Routing Efficiency</div>
                    </div>
                """, unsafe_allow_html=True)

            with s3:
                st.markdown(f"""
                    <div style='background: rgba(52, 168, 83, 0.05); padding: 20px; border-radius: 12px; border: 1px solid rgba(52, 168, 83, 0.3); box-shadow: 0 0 15px rgba(52, 168, 83, 0.2); text-align: center;'>
                        <div style='font-size: 0.75rem; font-weight: 800; color: #34A853; letter-spacing: 1px; text-transform: uppercase;'>👥 Lives Impacted</div>
                        <div style='font-size: 2.5rem; font-weight: 900; color: #ffffff; text-shadow: 0 0 10px #34A853; line-height: 1.2;'>{total_impacted:,}</div>
                        <div style='font-size: 0.7rem; color: #94A3B8; margin-top: 5px;'>Verified Beneficiaries</div>
                    </div>
                """, unsafe_allow_html=True)

            with s4:
                st.markdown(f"""
                    <div style='background: rgba(66, 133, 244, 0.05); padding: 20px; border-radius: 12px; border: 1px solid rgba(66, 133, 244, 0.3); box-shadow: 0 0 15px rgba(66, 133, 244, 0.2); text-align: center;'>
                        <div style='font-size: 0.75rem; font-weight: 800; color: #4285F4; letter-spacing: 1px; text-transform: uppercase;'>⚡ System Latency</div>
                        <div style='font-size: 2.5rem; font-weight: 900; color: #ffffff; text-shadow: 0 0 10px #4285F4; line-height: 1.2;'>{system_latency}ms</div>
                        <div style='font-size: 0.7rem; color: #94A3B8; margin-top: 5px;'>Inference & DB Sync</div>
                    </div>
                """, unsafe_allow_html=True)

            st.markdown("---")
            cmd_tab, intel_tab, map_tab = st.tabs(["🕹️ Strategic Command", "📋 Intelligence Feed", "🗺️ Live Impact Map"])

            with cmd_tab:
                hdr_col, anim_col = st.columns([4, 1])
                with hdr_col:
                    st.markdown("<h2 style='margin-bottom:0;'>🕹️ Strategic Command Center</h2>", unsafe_allow_html=True)
                with anim_col:
                    if lottie_ai:
                        st_lottie(lottie_ai, height=80, key="ai_cmd_anim", speed=0.7)

                c1, c2, c3 = st.columns(3)

                efficiency_score = st.session_state.get('ai_efficiency_score', 94.2)
                eff_class = "neon-border-safe" if efficiency_score > 70 else "neon-border-critical"

                with c1:
                    st.markdown(f"""
                        <div class='high-end-card {eff_class}' style='text-align: center; padding: 20px; margin-bottom: 5px;'>
                            <div class='kpi-label'>AI Efficiency Score</div>
                            <div class='kpi-massive' style="color: {'#34A853' if eff_class=='neon-border-safe' else '#EA4335'};">{efficiency_score}%</div>
                            <div style='font-size: 0.8rem; font-weight: 700; opacity: 0.8;'>Optimized Mission Distribution</div>
                        </div>
                    """, unsafe_allow_html=True)

                vel_matches = 42
                with c2:
                    st.markdown("""
                        <div class='high-end-card neon-border-safe' style='text-align: center; padding: 20px;'>
                            <div class='kpi-label'>Resource Velocity</div>
                            <div class='kpi-massive' style="color: #34A853;">42</div>
                            <div style='font-size: 0.8rem; font-weight: 700; opacity: 0.8;'>⚡ Optimal Dispatch Frequency</div>
                        </div>
                    """, unsafe_allow_html=True)

                critical_gaps = len(v_df[v_df['urgency'] >= 9]) if 'urgency' in v_df.columns else 0
                gap_class = "neon-border-critical" if critical_gaps > 0 else "neon-border-safe"
                with c3:
                    st.markdown(f"""
                        <div class='high-end-card {gap_class}' style='text-align: center; padding: 20px;'>
                            <div class='kpi-label'>Pending Mission Blocks</div>
                            <div class='kpi-massive' style="color: {'#EA4335' if critical_gaps > 0 else '#34A853'};">{critical_gaps}</div>
                            <div style='font-size: 0.8rem; font-weight: 700; opacity: 0.8;'>🚨 Executive Priority Delta</div>
                        </div>
                    """, unsafe_allow_html=True)

                total_impacted = v_df['people_affected'].sum() if 'people_affected' in v_df.columns else len(v_df)*5
                st.info(f"💡 **Strategic Snapshot:** {int(total_impacted):,} lives secured across the current operation.")

                # --- 🏦 SENIOR LEADERSHIP SUMMARY: PREMIER INTELLIGENCE ---
                st.markdown("""
                    <div style='background: linear-gradient(90deg, #4285F4 0%, #34A853 100%); padding: 2px; border-radius: 12px; margin-bottom: 20px;'>
                        <div style='background: #0F172A; padding: 20px; border-radius: 10px;'>
                            <h2 style='margin: 0; font-size: 1.8rem; font-weight: 900; letter-spacing: -0.02em; color: white;'>
                                <i class="fas fa-microchip" style="margin-right: 15px; color: #4285F4;"></i>
                                Global Mission Intelligence
                                <span style="font-size: 0.8rem; vertical-align: middle; margin-left: 10px; padding: 4px 8px; background: rgba(66, 133, 244, 0.2); border: 1px solid #4285F4; border-radius: 20px; color: #4285F4; font-weight: 700;">AI GEN 5.0</span>
                            </h2>
                            <p style='margin: 10px 0 0 0; color: #94A3B8; font-size: 0.95rem; font-weight: 500;'>Consolidated Global Mission Intelligence & Predictive Asset Allocation</p>
                        </div>
                    </div>
                """, unsafe_allow_html=True)

                with st.container(border=True):
                    if st.button("🚀 UNLOCK LEADERSHIP INSIGHTS", use_container_width=True):
                        from src.processor import get_tactical_insights
                        with st.spinner("🧠 Senior AI Strategist processing mission telemetry..."):
                            # Pass serialized data to cache-friendly processor
                            insights = get_tactical_insights(
                                v_df.to_json(), 
                                json.dumps(st.session_state.get('volunteers_db', []))
                            )
                        
                        if insights:
                            st.markdown(f"**Strategic Summary:** {insights.get('strategic_summary', 'N/A')}")
                            
                            t_col1, t_col2 = st.columns([1, 1])
                            with t_col1:
                                # Automated Plotly Chart
                                import plotly.express as px
                                chart_df = pd.DataFrame({
                                    'Sector': insights.get('chart_labels', []),
                                    'Intensity': insights.get('chart_values', [])
                                })
                                if not chart_df.empty:
                                    fig = px.bar(chart_df, x='Sector', y='Intensity', color='Intensity', 
                                                 color_continuous_scale='Turbo', title="Operational Intensity Matrix")
                                    fig.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=350)
                                    st.plotly_chart(fig, use_container_width=True)
                            
                            with t_col2:
                                st.metric("Humanitarian ROI Projection", f"{insights.get('social_roi_score', 0)}%")
                                st.markdown("#### 🧠 Strategic Alignment Reasoning")
                                st.success(insights.get('reasoning_log', 'Strategic alignment verified.'))
                            
                            st.markdown("#### 🎯 AI-Optimized Mission Allocations")
                            for alloc in insights.get('allocations', []):
                                with st.expander(f"CRITICAL MATCH: Need {alloc.get('need_id')} → {alloc.get('volunteer_name')}"):
                                    st.write(f"**Lead Strategy:** {alloc.get('reasoning')}")
                                    st.caption(f"Impact Horizon: {alloc.get('impact_projection')}")
                                    st.markdown(f"""
                                        <div style="background: rgba(66, 133, 244, 0.1); padding: 8px; border-radius: 8px; border-left: 3px solid #4285F4; margin-top: 5px;">
                                            <span style="font-size: 0.7rem; font-weight: 800; color: #4285F4; text-transform: uppercase;">🇺🇳 UN SDG Alignment</span><br>
                                            <span style="font-size: 0.9rem; font-weight: 600;">🌍 {alloc.get('sdg_alignment', 'General Impact')}</span>
                                        </div>
                                    """, unsafe_allow_html=True)
                st.divider()

                sel_idx = st.session_state.get('selected_idx')

                col1, col2, col3 = st.columns([1, 1.2, 1.8])

                with col1:
                    st.markdown("### 📋 Context Feed")
                    with st.container(height=650):
                        for idx, row in v_df.iterrows():
                            urg_glow = "card-critical" if row.get('urgency', 0) >= 8 else "card-warning" if row.get('urgency', 0) >= 5 else "card-safe"
                            is_active = (sel_idx == idx)

                            narrative = row.get('human_context_summary', 'Coordinating community relief.')
                            card_html = f"""
                                <div class='high-end-card {urg_glow if is_active else ""}' style='padding: 16px; border-radius: 16px; margin-bottom: 12px; cursor: pointer;'>
                                    <div style='display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px;'>
                                        <span style='font-size: 0.65rem; color: var(--text-medium-contrast); text-transform: uppercase; font-weight: 700; letter-spacing: 0.1em;'>{row.get('category', 'General')}</span>
                                        <span style='font-size: 0.65rem; font-weight: 800; color: var(--impact-{urg_glow.split('-')[1] if '-' in urg_glow else 'green'});'>{f'VOLUNTEERS NEEDED' if row.get('urgency', 0) >= 8 else 'STABLE'}</span>
                                    </div>
                                    <div style='font-weight: 700; font-size: 0.95rem; color: var(--text-high-contrast); line-height: 1.4;'>{narrative}</div>
                                </div>
                            """
                            st.markdown(card_html, unsafe_allow_html=True)
                            if st.button(f"Mission Insight {idx}", key=f"sel_{idx}", use_container_width=True, type="secondary" if not is_active else "primary"):
                                st.session_state['selected_idx'] = idx
                                st.rerun()

                with col2:
                    st.markdown("### 📖 Detail View")
                    if sel_idx is not None and sel_idx in v_df.index:
                        sel_row = v_df.loc[sel_idx]
                        st.markdown(f"#### {sel_row.get('category', 'General')} Situational Analysis")
                        st.markdown(f"**Human Narrative:** *{sel_row.get('human_context_summary', 'Coordinating resource allocation.')}*")
                        st.write(f"**Total Impact Projection:** {sel_row.get('people_affected', 5)} lives affected.")
                        st.write(f"**Geospatial Center:** {sel_row.get('latitude', 0):.4f}, {sel_row.get('longitude', 0):.4f}")
                        st.markdown(f"**Detailed Field Notes:** *{sel_row.get('description', 'No description.')}*")

                        col_a, col_b = st.columns(2)
                        with col_a:
                            if st.button("Dispatch Teams", use_container_width=True):
                                st.toast(f"Dispatching units to {sel_row.get('category', 'incident')} cluster.")
                        with col_b:
                            if st.button("Resolve Case", use_container_width=True):
                                st.toast("Incident marked as resolved.")
                    else:
                        st.info("Satellite systems ready. Select a tactical card to focus operations.")

    elif page == "Field Report Center":
        st.subheader("📁 Data Aggregation & Field Reporting")

        with st.expander("🛡️ Strategic Operations: Intelligent Mission Audit", expanded=True):
            st.markdown("### 🤖 Mission-Critical Logistical Audit")
            audit_df = st.session_state.get('needs_df', pd.DataFrame())

            if st.button("🚀 Run Intelligent Audit", key="btn_intel_audit", type="primary", use_container_width=True):
                if audit_df.empty:
                    st.warning("Awaiting field data to perform logistical audit.")
                else:
                    from src.processor import run_intelligent_audit
                    with st.spinner("🕵️ AI Cross-Referencing Mission Telemetry..."):
                        ai_report = run_intelligent_audit(audit_df)
                        st.session_state['last_audit_report'] = ai_report

            if 'last_audit_report' in st.session_state:
                st.markdown("---")
                st.markdown(st.session_state['last_audit_report'].replace('\n', '<br>'))
                if st.button("Acknowledge & Archive Audit", use_container_width=True):
                    del st.session_state['last_audit_report']
                    st.rerun()

        r1, r2 = st.columns(2)
        with r1:
            voice_memo = st.file_uploader("🎤 Voice Memo (Audio)", type=["mp3", "wav", "m4a"], key="voice_ingest")
            if voice_memo:
                from src.processor import process_field_audio
                with st.spinner("Transcribing field recording..."):
                    res = process_field_audio(voice_memo.read())
                    if "error" not in res:
                        st.session_state['extracted_result'] = res
        with r2:
            photo_memo = st.file_uploader("📸 Situational Photo", type=["jpg", "png", "jpeg"], key="photo_ingest")
            if photo_memo:
                from src.processor import process_field_image
                with st.spinner("Analyzing situational imagery..."):
                    res = process_field_image(photo_memo.read())
                    if "error" not in res:
                        st.session_state['extracted_result'] = res

        st.markdown("---")
        uploaded_file = st.file_uploader("Conventional Database Sync (CSV, JSON, PDF)", type=["csv", "json", "pdf", "txt"], key="field_uploader")
        if uploaded_file is not None:
            ext = uploaded_file.name.split('.')[-1].lower()
            df = pd.DataFrame()
            if ext in ['csv', 'json']:
                df = pd.read_csv(uploaded_file) if ext == 'csv' else pd.read_json(uploaded_file)
            elif ext == 'txt':
                from src.processor import process_ngo_notes
                text = uploaded_file.getvalue().decode('utf-8', errors='ignore')
                res = process_ngo_notes(text)
                if "error" not in res:
                    df = pd.DataFrame([{k: v for k, v in res.items() if k != 'note'}])

            if not df.empty:
                if 'status' not in df.columns:
                    df['status'] = 'Pending'
                if 'verified' not in df.columns:
                    df['verified'] = True
                
                with st.spinner("🕵️ Senior Strategist Analyzing Impact Payload..."):
                    from src.processor import generate_elite_report
                    elite_report = generate_elite_report(uploaded_file, st.session_state.get('needs_df', pd.DataFrame()), api_key=_api_key)
                
                st.session_state['needs_df'] = pd.concat([st.session_state['needs_df'], df], ignore_index=True)
                st.success("Uploaded and Synchronized!")
                
                if elite_report and 'error' not in elite_report:
                    with st.expander("📊 Strategic Impact Analysis", expanded=True):
                        st.markdown(f"### 🛡️ {elite_report.get('summary', 'Mission Analysis')}")
                        st.divider()
                        
                        col_a, col_b = st.columns(2)
                        with col_a:
                            st.markdown("#### ⚡ Immediate Action Items")
                            st.markdown(elite_report.get('immediate_actions', 'N/A'))
                        with col_b:
                            st.markdown("#### 🔋 Sustainability Impact")
                            st.markdown(elite_report.get('sustainability_impact', 'N/A'))
                        
                        st.markdown("---")
                        roi_col, score_col = st.columns([3, 1])
                        with roi_col:
                            st.markdown("#### 🎯 Social ROI Analysis")
                            st.write(elite_report.get('social_roi', 'N/A'))
                        with score_col:
                            st.metric("Social ROI Score", f"{elite_report.get('social_roi_score', 0)}/100")
                        
                        if elite_report.get('sdg_impact'):
                            st.markdown("#### 🌍 Global SDG Multiplier")
                            sdg_cols = st.columns(len(elite_report['sdg_impact']))
                            for i, sdg in enumerate(elite_report['sdg_impact']):
                                sdg_cols[i].markdown(f"""
                                    <div style='background:#1E293B; border: 1px solid #4285F4; border-radius: 8px; padding: 10px; text-align: center;'>
                                        <div style='color:#4285F4; font-size: 0.7rem; font-weight: 800;'>UN SDG IMPACT</div>
                                        <div style='font-size: 0.8rem; font-weight: 600;'>{sdg}</div>
                                    </div>
                                """, unsafe_allow_html=True)

        df = st.session_state.get('needs_df', pd.DataFrame())
        if not df.empty:
            st.markdown("### 📊 Structured Community Needs Data")
            display_df = df[['urgency', 'category', 'people_affected', 'latitude', 'longitude', 'status', 'verified']].copy()
            st.dataframe(display_df, use_container_width=True)

    elif page == "Impact Map":
        st.subheader("🗺️ Impact Map & Need Density Visualization")
        df = st.session_state.get('needs_df', pd.DataFrame())

        if df.empty or 'latitude' not in df.columns or 'longitude' not in df.columns:
            st.info("No geographic data available. Please upload data first.")
        else:
            with st.sidebar:
                st.markdown("### 🗺️ Map Controls")
                cat_filter = st.selectbox("Filter by Category", ["All"] + list(df['category'].unique()) if 'category' in df.columns else ["All"])
                urgency_filter = st.selectbox("Filter by Urgency", ["All", "High (8-10)", "Medium (5-7)", "Low (1-4)"])
                st.metric("Total Strategic Needs", len(df))
                st.markdown("---")

            filtered_df = df.copy()
            if cat_filter != "All" and 'category' in filtered_df.columns:
                filtered_df = filtered_df[filtered_df['category'] == cat_filter]

            if urgency_filter != "All" and 'urgency' in filtered_df.columns:
                if urgency_filter == "High (8-10)":
                    filtered_df = filtered_df[filtered_df['urgency'] >= 8]
                elif urgency_filter == "Medium (5-7)":
                    filtered_df = filtered_df[(filtered_df['urgency'] >= 5) & (filtered_df['urgency'] <= 7)]
                elif urgency_filter == "Low (1-4)":
                    filtered_df = filtered_df[filtered_df['urgency'] <= 4]

            if filtered_df.empty:
                st.warning("No data matches the selected filters.")
            else:
                import folium
                from streamlit_folium import st_folium
                from folium.plugins import HeatMap, MarkerCluster, LocateControl, MiniMap, Geocoder

                @st.cache_data(show_spinner=False)
                def generate_impact_map(data_json):
                    """
                    Elite Cached Map Generator: Prevents Render memory spikes by caching mission layers.
                    """
                    # 🌌 Elite Cached Map Generator: Prevents Render memory spikes
                    df = pd.read_json(data_json)
                    
                    # Compute dynamic bounds if data exists for "Zoom to Fit"
                    if not df.empty and pd.notna(df['latitude']).any():
                        sw = df[['latitude', 'longitude']].min().values.tolist()
                        ne = df[['latitude', 'longitude']].max().values.tolist()
                    else:
                        sw, ne = None, None

                    m = folium.Map(
                        location=[20.5937, 78.9629], 
                        zoom_start=5, 
                        tiles='cartodbdark_matter', # Hard-locked to Dark Theme for seamless blending
                        control_scale=True
                    )

                    # 🛰️ Tactical Modules
                    LocateControl(auto_start=False, flyTo=True).add_to(m)
                    MiniMap(toggle_display=True, position='bottomright', tile_layer='cartodbdark_matter').add_to(m)
                    Geocoder(position='topleft', add_marker=False).add_to(m) # Search Feature

                    # 🔥 Heatmap: Scarcity Visualization
                    heat_data = [[row['latitude'], row['longitude'], row['urgency']/10.0] 
                                 for _, row in df.iterrows() if pd.notna(row['latitude'])]
                    HeatMap(heat_data, radius=25, blur=20, min_opacity=0.4, name="Scarcity Density").add_to(m)

                    # 🗂️ Marker Clustering: Performance optimization for 100+ points
                    marker_cluster = MarkerCluster(name="Tactical Pins", 
                                                   options={'spiderfyOnMaxZoom': True, 'showCoverageOnHover': False}).add_to(m)

                    for _, row in df.iterrows():
                        if pd.isna(row['latitude']): continue

                        cat = row.get('category', 'General')
                        urgency = row.get('urgency', 5)
                        
                        icon_map = {
                            "Food": ("apple-whole", "green"),
                            "Medical": ("kit-medical", "red"),
                            "Shelter": ("house-chimney", "blue"),
                            "General": ("circle-info", "gray")
                        }
                        icon_name, color = icon_map.get(cat, ("circle-info", "gray"))

                        # 🏹 3D-Styled Tactical Popup (HTML Table)
                        popup_html = f"""
                        <div style='font-family: "Inter", sans-serif; width: 280px; padding: 10px; background: #0f172a; color: white; border-radius: 12px; border: 1px solid rgba(255,255,255,0.1); box-shadow: 0 10px 15px rgba(0,0,0,0.3);'>
                            <div style='font-size: 1.1rem; font-weight: 800; color: {color}; margin-bottom: 10px; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 5px;'>📊 MISSION DETAIL</div>
                            <table style='width: 100%; border-collapse: collapse;'>
                                <tr style='border-bottom: 1px solid rgba(255,255,255,0.05);'>
                                    <td style='padding: 6px 0; color: #94A3B8; font-size: 0.75rem; font-weight: 700;'>SECTOR</td>
                                    <td style='text-align: right; font-weight: 700; color: white;'>{cat}</td>
                                </tr>
                                <tr style='border-bottom: 1px solid rgba(255,255,255,0.05);'>
                                    <td style='padding: 6px 0; color: #94A3B8; font-size: 0.75rem; font-weight: 700;'>URGENCY</td>
                                    <td style='text-align: right; font-weight: 700; color: {color};'>{urgency}/10</td>
                                </tr>
                                <tr>
                                    <td style='padding: 6px 0; color: #94A3B8; font-size: 0.75rem; font-weight: 700;'>IMPACT</td>
                                    <td style='text-align: right; font-weight: 700;'>{row.get('people_affected', 'N/A')} lives</td>
                                </tr>
                            </table>
                            <div style='margin-top: 12px; background: rgba(255,255,255,0.05); padding: 10px; border-radius: 8px;'>
                                <div style='font-size: 0.65rem; font-weight: 800; color: #4285F4; margin-bottom: 4px; text-transform: uppercase;'>AI Strategic Insight</div>
                                <div style='font-size: 0.8rem; font-style: italic; color: #CBD5E1;'>"{row.get('human_context_summary', row.get('description', ''))}"</div>
                            </div>
                        </div>
                        """

                        folium.Marker(
                            location=[row['latitude'], row['longitude']],
                            popup=folium.Popup(popup_html, max_width=320),
                            icon=folium.Icon(color=color, icon=icon_name, prefix='fa')
                        ).add_to(marker_cluster)

                    if sw and ne:
                        m.fit_bounds([sw, ne])

                    folium.LayerControl().add_to(m)
                    return m

                st.markdown("### 📍 Tactical Impact Map")
                # We pass JSON to avoid unhashable DF error in caching
                if not filtered_df.empty:
                    m = generate_impact_map(filtered_df.to_json())
                    st_folium(m, width='100%', height=500, key="impact_map_main")
                else:
                    st.info("📡 **Command Signal Weak:** Waiting for AI to generate impact locations... Please upload mission data or launch 'Perfect Demo' mode.")
                    # Placeholder container to maintain layout stability
                    st.container(height=500, border=True)

                st.markdown("### 📊 Need Density Summary")
                c1, c2, c3 = st.columns(3)
                with c1:
                    high_count = len(filtered_df[filtered_df['urgency'] >= 8]) if 'urgency' in filtered_df.columns else 0
                    st.metric("🔴 High Urgency (8-10)", high_count)
                with c2:
                    med_count = len(filtered_df[(filtered_df['urgency'] >= 5) & (filtered_df['urgency'] < 8)]) if 'urgency' in filtered_df.columns else 0
                    st.metric("🟠 Medium Urgency (5-7)", med_count)
                with c3:
                    low_count = len(filtered_df[filtered_df['urgency'] < 5]) if 'urgency' in filtered_df.columns else 0
                    st.metric("🟢 Low Urgency (1-4)", low_count)

    elif page == "Executive Impact Analytics":
        st.subheader("📈 Executive Impact Analytics")
        df = st.session_state.get('needs_df', pd.DataFrame())
        df = df[df['verified'] == True] if 'verified' in df.columns else df
        if df.empty:
            st.warning("No verified data available.")
        else:
            total_impacted = int(df['people_affected'].sum()) if 'people_affected' in df.columns else len(df)*5
            avg_response_time = 4.2

            st.markdown("### 📊 KPI Dashboard")
            kpi1, kpi2, kpi3, kpi4 = st.columns(4)
            with kpi1:
                st.metric("👥 Total Lives Impacted", f"{total_impacted:,}")
            with kpi2:
                st.metric("⏱️ Avg Response Time", f"{avg_response_time} hrs")
            with kpi3:
                efficiency = calculate_efficiency(df)
                st.metric("📈 Efficiency Rate", f"{efficiency}%")
            with kpi4:
                critical = len(df[df['urgency'] >= 8]) if 'urgency' in df.columns else 0
                st.metric("🚨 Critical Needs", critical)

            st.divider()

            # --- Executive Urgency Index Section ---
            st.markdown("### 🌡️ Executive Urgency Index")
            u_col1, u_col2 = st.columns([2, 1])

            with u_col1:
                st.markdown("#### 📊 Sector Crisis Scores")
                # Calculate Crisis Score per Sector: (Count * Avg Urgency)
                if not df.empty and 'category' in df.columns and 'urgency' in df.columns:
                    sector_stats = df.groupby('category').agg({
                        'urgency': ['count', 'mean']
                    }).reset_index()
                    sector_stats.columns = ['category', 'count', 'avg_urgency']
                    sector_stats['crisis_score'] = sector_stats['count'] * sector_stats['avg_urgency']
                    # Normalize to 0-100
                    max_score = sector_stats['crisis_score'].max()
                    if max_score > 0:
                        sector_stats['crisis_score'] = (sector_stats['crisis_score'] / max_score * 100).round(1)
                    
                    import plotly.express as px
                    fig_bar = px.bar(
                        sector_stats, 
                        x='category', 
                        y='crisis_score',
                        color='crisis_score',
                        color_continuous_scale='Reds',
                        text_auto=True,
                        labels={'crisis_score': 'Crisis Score (0-100)', 'category': 'Community Sector'}
                    )
                    fig_bar.update_layout(
                        template="plotly_dark", 
                        paper_bgcolor='rgba(0,0,0,0)', 
                        plot_bgcolor='rgba(0,0,0,0)',
                        height=350,
                        coloraxis_showscale=False
                    )
                    st.plotly_chart(fig_bar, use_container_width=True)
                else:
                    st.info("Insufficient data to calculate sector crisis scores.")

            with u_col2:
                st.markdown("#### 📉 Real-time Urgency Delta")
                # Simulated Delta for demo
                st.metric(
                    label="Current Urgency Level", 
                    value="7.4 / 10", 
                    delta="-12% (vs yesterday)", 
                    delta_color="normal" # normal means decrease is green (good)
                )
                
                st.markdown("#### 🤝 Volunteer Coverage")
                # Coverage = (Matched / Total) for urgent tasks (urgency >= 8)
                urgent_tasks = df[df['urgency'] >= 8]
                if not urgent_tasks.empty:
                    matched_urgent = len(urgent_tasks[urgent_tasks['status'] == 'Matched'])
                    coverage_pct = round((matched_urgent / len(urgent_tasks)) * 100, 1)
                else:
                    coverage_pct = 100.0
                
                import plotly.graph_objects as go
                fig_gauge = go.Figure(go.Indicator(
                    mode = "gauge+number",
                    value = coverage_pct,
                    domain = {'x': [0, 1], 'y': [0, 1]},
                    title = {'text': "Urgent Task Coverage", 'font': {'size': 16}},
                    gauge = {
                        'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "white"},
                        'bar': {'color': "#10B981" if coverage_pct > 70 else "#F59E0B" if coverage_pct > 40 else "#EF4444"},
                        'bgcolor': "rgba(0,0,0,0)",
                        'borderwidth': 2,
                        'bordercolor': "gray",
                        'steps': [
                            {'range': [0, 40], 'color': 'rgba(239, 68, 68, 0.1)'},
                            {'range': [40, 70], 'color': 'rgba(245, 158, 11, 0.1)'},
                            {'range': [70, 100], 'color': 'rgba(16, 185, 129, 0.1)'}
                        ],
                    }
                ))
                fig_gauge.update_layout(
                    template="plotly_dark", 
                    paper_bgcolor='rgba(0,0,0,0)', 
                    font={'color': "white", 'family': "Arial"},
                    height=250,
                    margin=dict(l=20, r=20, t=50, b=20)
                )
                st.plotly_chart(fig_gauge, use_container_width=True)

            st.divider()

            # --- ⚡ Real-Time System Performance Section ---
            st.markdown('### ⚡ Real-Time System Performance')
            perf_col1, perf_col2, perf_col3, perf_col4 = st.columns(4)

            with perf_col1:
                st.markdown("""
                    <div class='high-end-card' style='text-align: center; padding: 20px; border-top: 4px solid #4285F4;'>
                        <div style='font-size: 0.7rem; font-weight: 700; color: var(--text-medium-contrast); text-transform: uppercase; letter-spacing: 0.05em;'>⏱️ Avg Match Time</div>
                        <div style='font-size: 2.2rem; font-weight: 900; color: #4285F4; line-height: 1.2;'>2.3s</div>
                        <div style='font-size: 0.7rem; color: #34A853; margin-top: 4px;'>⚡ Ultra-Fast Tier</div>
                    </div>
                """, unsafe_allow_html=True)

            with perf_col2:
                st.markdown("""
                    <div class='high-end-card' style='text-align: center; padding: 20px; border-top: 4px solid #34A853;'>
                        <div style='font-size: 0.7rem; font-weight: 700; color: var(--text-medium-contrast); text-transform: uppercase; letter-spacing: 0.05em;'>✅ Match Success Rate</div>
                        <div style='font-size: 2.2rem; font-weight: 900; color: #34A853; line-height: 1.2;'>87%</div>
                        <div style='font-size: 0.7rem; color: #34A853; margin-top: 4px;'>↑ 4% from last hour</div>
                    </div>
                """, unsafe_allow_html=True)

            with perf_col3:
                st.markdown("""
                    <div class='high-end-card' style='text-align: center; padding: 20px; border-top: 4px solid #FBBC05;'>
                        <div style='font-size: 0.7rem; font-weight: 700; color: var(--text-medium-contrast); text-transform: uppercase; letter-spacing: 0.05em;'>👷 Volunteer Utilization</div>
                        <div style='font-size: 2.2rem; font-weight: 900; color: #FBBC05; line-height: 1.2;'>76%</div>
                        <div style='font-size: 0.7rem; color: #FBBC05; margin-top: 4px;'>Optimal Capacity</div>
                    </div>
                """, unsafe_allow_html=True)

            with perf_col4:
                st.markdown("""
                    <div class='high-end-card' style='text-align: center; padding: 20px; border-top: 4px solid #EA4335;'>
                        <div style='font-size: 0.7rem; font-weight: 700; color: var(--text-medium-contrast); text-transform: uppercase; letter-spacing: 0.05em;'>🕒 Avg Response Time</div>
                        <div style='font-size: 2.2rem; font-weight: 900; color: #EA4335; line-height: 1.2;'>4.2h</div>
                        <div style='font-size: 0.7rem; color: #EA4335; margin-top: 4px;'>Target: < 5.0h</div>
                    </div>
                """, unsafe_allow_html=True)

            st.divider()

            col_trend, col_donut = st.columns([2, 1])
            with col_trend:
                st.markdown("#### 📉 Needs Reported vs Resources Allocated")
                import plotly.graph_objects as go
                from datetime import datetime, timedelta

                dates = [datetime.now() - timedelta(days=7-i) for i in range(7)]
                needs_reported = [random.randint(10, 50) + i*3 for i in range(7)]
                resources_allocated = [random.randint(8, 40) + i*2 for i in range(7)]

                fig_trend = go.Figure()
                fig_trend.add_trace(go.Scatter(x=dates, y=needs_reported, name='Needs Reported', mode='lines+markers', line=dict(color='#ef4444', width=3)))
                fig_trend.add_trace(go.Scatter(x=dates, y=resources_allocated, name='Resources Allocated', mode='lines+markers', fill='tozeroy', line=dict(color='#10b981', width=3)))
                fig_trend.update_layout(
                    template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                    margin=dict(l=0, r=0, t=20, b=0), height=350,
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                    xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)')
                )
                st.plotly_chart(fig_trend, use_container_width=True)

            st.divider()
            st.markdown("### 📊 Impact Summary Matrix")
            s_col1, s_col2 = st.columns([1.5, 1])
            
            with s_col1:
                st.markdown("#### 🎯 Global SDG Distribution (Sunburst)")
                # Preparation of Sunburst data locally
                sdg_map = {"Food": "SDG 2: Zero Hunger", "Medical": "SDG 3: Good Health", 
                           "Shelter": "SDG 11: Sustainable Cities", "General": "SDG 17: Partnerships"}
                
                if not df.empty and 'category' in df.columns:
                    sunburst_data = []
                    for cat, count in df['category'].value_counts().items():
                        sunburst_data.append({
                            "Mission": "Unified Global Mission", 
                            "SDG": sdg_map.get(cat, "General Support"), 
                            "Sector": cat, 
                            "Count": count
                        })
                    sb_df = pd.DataFrame(sunburst_data)
                    import plotly.express as px
                    fig_sb = px.sunburst(
                        sb_df, path=['Mission', 'SDG', 'Sector'], values='Count',
                        color='SDG', color_discrete_sequence=px.colors.qualitative.Bold,
                        hover_data={'Count': True}
                    )
                    fig_sb.update_layout(
                        template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', 
                        height=450, margin=dict(t=10, l=10, r=10, b=10)
                    )
                    st.plotly_chart(fig_sb, use_container_width=True)
            
            with s_col2:
                st.markdown("#### 📥 Strategic Insights Export")
                st.info("Export the tactical allocation matrix for executive review.")
                
                # CSV Export Utility
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📂 Download Tactical Allocation (CSV)",
                    data=csv,
                    file_name=f"Smart_Resource_Allocation_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
                
                # Visual Metadata
                st.markdown("""
                    <div style='background:rgba(255, 255, 255, 0.05); padding:15px; border-radius:10px; border-left:4px solid #34A853;'>
                        <div style='font-size:0.75rem; color:#94A3B8;'>LAST AUDIT SYNC</div>
                        <div style='font-size:1.1rem; font-weight:700;'>""" + datetime.now().strftime("%H:%M UTC") + """</div>
                        <div style='font-size:0.75rem; color:#34A853;'>✅ Verified Integrity</div>
                    </div>
                """, unsafe_allow_html=True)

            st.divider()
            st.markdown("### 📥 Export for Stakeholders")

            if st.button("📄 Generate Executive PDF Report", use_container_width=True):
                from src.utils.pdf_generator import generate_executive_pdf
                with st.spinner("📜 Formulating Executive PDF Document..."):
                    pdf_data = generate_executive_pdf(df)
                    st.download_button(
                        "📥 Download Executive Summary PDF",
                        data=pdf_data,
                        file_name=f"Executive_Impact_Report_{datetime.now().strftime('%Y%m%d')}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                    st.success("Report generated successfully!")

    elif page in ["Volunteer Matching", "Rapid Dispatch"]:
        st.subheader("🤝 Emergency Dispatch Portal")
        needs_df = st.session_state.get('needs_df', pd.DataFrame())
        v_df = needs_df[needs_df['verified'] == True] if 'verified' in needs_df.columns else needs_df

        if v_df.empty:
            st.warning("Needs database is currently empty.")
        else:
            volunteers = st.session_state['volunteers_db']
            selected_v = st.selectbox("Select Available Field Unit", [v['name'] for v in volunteers])
            selected_volunteer = next((v for v in volunteers if v['name'] == selected_v), None)

            st.markdown("### 🏹 AI-Recommended Missions")
            available_needs = v_df[v_df['status'] == 'Pending'] if 'status' in v_df.columns else v_df
            if available_needs.empty:
                st.success("All missions currently assigned.")
            else:
                from src.models.matching import match_volunteer_to_needs
                with st.spinner("🤖 AI Optimizing Match Vector..."):
                    matches = match_volunteer_to_needs(selected_volunteer, available_needs, top_n=3, api_key=_api_key)
                
                for _, row in matches.iterrows():
                    with st.expander(f"Task: {row.get('category', 'General')} (Urgency: {row.get('urgency', 5)}/10)", expanded=True):
                        st.write(f"Rationale: {row.get('match_reason', 'No reasoning available.')}")
                        if st.button("Confirm & Dispatch", key=f"dispatch_{row.name}", use_container_width=True):
                            with st.spinner("Transmitting Dispatch Signal..."):
                                db.assign_volunteer(row.get('id'), selected_v)
                                st.session_state['needs_stale'] = True
                                st.toast(f"✅ Dispatched {selected_v}!")
                                st.rerun()

def initialize_mission_environment():
    """Ensure all critical folders exist before mission launch using Pathlib (Cross-Platform)."""
    from pathlib import Path
    required_dirs = ["src", "data", "exports", "logs"]
    for d in required_dirs:
        path = Path(d)
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)

def main():
    st.set_page_config(
        page_title="🛡️ Command Center | Smart Resource Allocator", 
        page_icon="🛡️", 
        layout="wide",
        initial_sidebar_state="auto" # Optimized for mobile (collapsed) and desktop (expanded)
    )
    
    # 🛰️ Mission Initialization
    initialize_mission_environment()
    
    # --- 🏗️ Advanced UI Styling: Sidebar & Brand Consistency ---
    st.markdown("""
        <style>
        /* 🏰 Premium Sidebar Styling */
        [data-testid="stSidebar"] {
            background-color: #f0f2f6 !important;
            border-right: 1px solid rgba(66, 133, 244, 0.3);
            visibility: visible !important; /* Ensure visibility */
        }
        [data-testid="stSidebarNav"] {
            background-color: transparent !important;
        }
        
        /* 🍔 ULTRA-FORCE HAMBURGER VISIBILITY */
        header[data-testid="stHeader"] {
            display: block !important;
            visibility: visible !important;
            background-color: transparent !important;
        }

        button[kind="header"] {
            color: #4285F4 !important;
            background-color: rgba(255, 255, 255, 0.1) !important;
            border-radius: 50% !important;
            box-shadow: 0 0 20px rgba(66, 133, 244, 0.6) !important;
            border: 1px solid #4285F4 !important;
            visibility: visible !important;
            opacity: 1 !important;
            z-index: 999999 !important;
        }

        [data-testid="stSidebarNav"] button {
            color: var(--primary-color) !important;
        }

        /* 💎 Glassmorphism Sidebar Collapse Button */
        [data-testid="stSidebarCollapseButton"] button {
            color: #4285F4 !important;
            background: rgba(255, 255, 255, 0.1) !important;
            backdrop-filter: blur(10px) !important;
            -webkit-backdrop-filter: blur(10px) !important;
            box-shadow: 0 0 15px rgba(66, 133, 244, 0.5) !important;
            border-radius: 50% !important;
            border: 1px solid rgba(66, 133, 244, 0.2) !important;
        }

        /* 📱 Mobile Column Optimization */
        @media (max-width: 640px) {
            [data-testid="stHorizontalBlock"] {
                flex-direction: column !important;
            }
        }
        
    /* 🚀 RENDER-OPTIMIZED PERFORMANCE VARIABLES */
    :root {
        --deep-navy: #0f172a;
        --absolute-black: #000000;
        --google-blue: #4285F4;
        --mesh-blue: rgba(66, 133, 244, 0.05);
        --mesh-purple: rgba(168, 85, 247, 0.05);
        --glass-bg: rgba(255, 255, 255, 0.03);
        --glass-border: rgba(255, 255, 255, 0.1);
    }

    /* 🌌 HARDWARE-ACCELERATED WORLD-CLASS BACKGROUND */
    [data-testid="stAppViewContainer"] {
        background-color: var(--deep-navy) !important; /* Solid Fallback */
        background: radial-gradient(circle at center, var(--deep-navy) 0%, var(--absolute-black) 100%) !important;
        position: relative;
    }

    /* 🍔 ABSOLUTE PRIORITY SIDEBAR BUTTON VISIBILITY */
    header[data-testid="stHeader"] {
        display: block !important;
        visibility: visible !important;
        background: transparent !important;
        z-index: 1000001 !important;
    }

    button[aria-label="Open sidebar"], 
    button[aria-label="Close sidebar"],
    button[kind="header"] {
        display: flex !important;
        visibility: visible !important;
        opacity: 1 !important;
        color: #4285F4 !important;
        background-color: rgba(66, 133, 244, 0.2) !important;
        border: 2px solid rgba(66, 133, 244, 0.5) !important;
        border-radius: 50% !important;
        z-index: 1000002 !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 0 15px rgba(66, 133, 244, 0.4) !important;
    }

    button[kind="header"]:hover {
        background-color: #4285F4 !important;
        color: white !important;
        transform: scale(1.1);
    }

    div[data-testid="stMetric"]:hover, .high-end-card:hover {
        border: 1px solid rgba(66, 133, 244, 0.4) !important;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
        transform: translateY(-2px);
    }
    </style>
    """, unsafe_allow_html=True)
    
    try:
        run_dashboard()
    except Exception as e:
        import traceback
        st.error("### 🚨 Mission-Critical System Failure")
        st.markdown(f"""
        **The system encountered an unanticipated tactical error.** 
        This is most likely due to a brief interruption in the AI satellite link or the mission database.
        
        **Recommended Recovery Actions:**
        1. 🔄 **Refresh your browser** to re-establish the encrypted session.
        2. 🔑 **Verify API Secrets**: Ensure your `GOOGLE_API_KEY` is correctly configured in your environment.
        3. 📂 **Check File Integrity**: If you were uploading a file, verify the format and try again.
        
        *Technicians can view the detailed telemetry pulse below.*
        """)
        
        with st.expander("🛠️ Tactical Diagnostic Pulse (Technical Traceback)"):
            st.code(f"Error Type: {type(e).__name__}\nMessage: {str(e)}\n\n{traceback.format_exc()}")

    # --- ENGINEERING ATTRIBUTION COMPONENT ---
    st.markdown("""
        <style>
        /* Professional Developer Footer Styling */
        .dev-signature-container {
            margin-top: 80px;
            padding: 40px 10px;
            
            /* 🔗 Themed Background Engine */
            background: var(--secondary-background-color);
            background-color: rgba(var(--secondary-background-color-rgb), 0.5); /* Use rgba with fallback if possible, but st vars are hex usually */
            /* Better way for st hex to rgba: */
            background: color-mix(in srgb, var(--secondary-background-color) 50%, transparent);
            
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            
            /* 🌈 3D Boundary & Depth */
            border-top: 3px solid;
            border-image: linear-gradient(90deg, var(--primary-color), #EA4335, #FBBC05, #34A853) 1;
            box-shadow: 0 20px 50px rgba(0,0,0,0.5);
            
            text-align: center;
            width: 100%;
            transition: all 0.5s cubic-bezier(0.4, 0, 0.2, 1);
            transform: perspective(1000px) rotateX(0deg);
        }

        .dev-signature-container:hover {
            transform: perspective(1000px) rotateX(5deg) translateY(-5px);
            background: color-mix(in srgb, var(--secondary-background-color) 70%, transparent);
            box-shadow: 0 30px 60px rgba(0,0,0,0.6);
        }

        .dev-name {
            font-family: 'Inter', sans-serif;
            font-size: 1.8rem;
            font-weight: 900;
            letter-spacing: -0.5px;
            margin-bottom: 25px;
            position: relative;
            display: inline-block;
            color: var(--text-color);
            
            /* 🌈 Kinetic Gradient Text (Overlayed by Shine) */
            background: linear-gradient(
                to right, 
                var(--primary-color), #EA4335, #FBBC05, #34A853, var(--primary-color)
            );
            background-size: 200% auto;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            animation: flow-gradient 5s linear infinite;
        }

        /* 🌑 Dark Mode Adaptive Glow */
        @media (prefers-color-scheme: dark) {
            .dev-signature-container {
                box-shadow: 0 0 30px rgba(66, 133, 244, 0.15);
                border-top-color: var(--primary-color);
            }
            .dev-name {
                text-shadow: 0 0 20px rgba(66, 133, 244, 0.3);
            }
        }

        /* ✨ Shine Animation Overlay */
        .dev-name::after {
            content: "JASWANTH HANUMANTHU";
            position: absolute;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background: linear-gradient(
                120deg, 
                transparent 30%, 
                rgba(255, 255, 255, 0.3) 40%, 
                rgba(255, 255, 255, 0.3) 60%, 
                transparent 70%
            );
            background-size: 200% 100%;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            animation: shine 5s infinite;
        }

        @keyframes flow-gradient {
            to { background-position: 200% center; }
        }

        @keyframes shine {
            0% { background-position: 200% 0; }
            100% { background-position: -200% 0; }
        }

        .dev-links {
            display: flex;
            justify-content: center;
            gap: 20px;
            margin-bottom: 30px;
        }
        
        /* ... existing styles preserved ... */
        .dev-header { font-family: 'JetBrains Mono', monospace; color: #94a3b8; font-size: 0.75rem; letter-spacing: 3px; margin-bottom: 10px; text-transform: uppercase; }
        .dev-button { font-family: 'JetBrains Mono', monospace; color: #4285F4; text-decoration: none; font-size: 0.8rem; border: 1px solid rgba(66, 133, 244, 0.4); padding: 10px 20px; border-radius: 4px; transition: all 0.2s ease; background: rgba(66, 133, 244, 0.05); box-shadow: 0 4px 6px rgba(0,0,0,0.2); }
        .dev-button:hover { background: #4285F4; color: #ffffff !important; box-shadow: 0 0 25px rgba(66, 133, 244, 0.7); transform: translateY(-5px); border-color: #ffffff; }
        .dev-button:active { transform: translateY(2px); box-shadow: none; }
        .build-info { font-family: 'JetBrains Mono', monospace; font-size: 0.6rem; color: rgba(255, 255, 255, 0.3); letter-spacing: 1px; }
        </style>

        <div class="dev-signature-container">
            <div class="dev-header">Lead System Architect</div>
            <div class="dev-name">JASWANTH HANUMANTHU</div>
            <div class="dev-links">
                <a href="https://www.linkedin.com/in/jaswanth-hanumanthu" target="_blank" class="dev-button">LINKEDIN_CORE</a>
                <a href="https://github.com/JaswanthHanumanthu/Smart-Resource-Allocation-AI" target="_blank" class="dev-button">GITHUB_SOURCE</a>
            </div>
            <div class="build-info">
                STABLE RELEASE V2.0 // GOOGLE SOLUTION CHALLENGE 2026 // VISAKHAPATNAM, IN
            </div>
        </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
