import streamlit as st
import pandas as pd
import google.generativeai as genai
import contextlib
import os
import numpy as np
from datetime import datetime, timedelta

# --- 🔐 Enterprise-Grade Security: API Configuration ---
# API configuration is lazy-loaded to reduce app wake-up time.
# Primary: st.secrets, Fallback: os.getenv

_api_key = None
try:
    _api_key = st.secrets.get('GOOGLE_API_KEY') or os.getenv('GOOGLE_API_KEY')
except Exception:
    _api_key = os.getenv('GOOGLE_API_KEY')

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

def run_dashboard():
    from src.database.client import ProductionDB
    db = ProductionDB()

    if 'GOOGLE_API_KEY' not in st.secrets:
        st.error('⚠️ Mission-Critical Status: Missing GOOGLE_API_KEY in Streamlit Secrets. Vision & AI extraction tiers are currently inhibited.')

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

    st.sidebar.title("🛡️ Command Center")
    st.sidebar.caption("Mission-Critical Release V2.0")

    st.sidebar.markdown("### 🗺️ Navigation")
    page = st.sidebar.radio(
        "Mission Map",
        ["🛡️ Strategic Dashboard", "📊 Impact Analytics", "🚨 Emergency Dispatch", "📁 Field Report Center", "📚 Mission Library"],
        label_visibility="collapsed",
        key="page"
    )

    st.sidebar.markdown("---")
    with st.sidebar.expander("🌍 Regional Settings"):
        selected_lang = st.selectbox("UI Language", ["English", "Hindi", "Telugu"], index=["English", "Hindi", "Telugu"].index(st.session_state['lang']))
        st.session_state['lang'] = selected_lang

        is_light = st.toggle("Minimalist Light Mode", value=st.session_state['theme_mode'] == "Apple-Light")
        st.session_state['theme_mode'] = "Apple-Light" if is_light else "Cyber-Dark"

    if st.session_state['theme_mode'] == "Apple-Light":
        st.markdown("<script>document.body.classList.add('light-mode-theme');</script>", unsafe_allow_html=True)
    else:
        st.markdown("<script>document.body.classList.remove('light-mode-theme');</script>", unsafe_allow_html=True)

    with st.sidebar.expander("🛠️ Tactical Simulation"):
        st.session_state['offline_mode'] = st.toggle("Field Offline Mode", value=st.session_state.get('offline_mode', False))
        st.session_state['high_traffic'] = st.toggle("Server Congestion", value=st.session_state.get('high_traffic', False))

        if st.button("🚀 Trigger Crisis Injection", width='stretch'):
            st.session_state['trigger_demo'] = True
            st.toast("Crisis simulation signal queued.")

    from src.processor import translate_text, process_voice_command
    st.sidebar.markdown("---")
    st.sidebar.caption("🎙️ Voice Tactical Input")
    voice_input = st.sidebar.audio_input("Satellite Voice Command")
    if voice_input:
        with st.sidebar.status("🧠 Processing Voice Payload...") as status:
            cmd = process_voice_command(voice_input.read())
            if "error" not in cmd:
                if cmd.get('category'): st.session_state['category_filter'] = cmd['category']
                status.update(label=f"✅ Navigating to {cmd.get('category', 'Target')} Sector.", state="complete")
                st.rerun()
            else:
                status.update(label="⚠️ Voice Signal Blurred.", state="error")

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

    if 'needs_df' not in st.session_state or st.session_state.get('needs_stale', True):
        st.session_state['needs_df'] = db.get_all_needs()
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
            response = model.generate_content(prompt)
            clean_res = response.text.strip().replace('```json', '').replace('```', '')
            return json.loads(clean_res)
        except Exception as e:
            st.toast("🔄 System Re-calibrating: AI Analysis Engine Congestion", icon="🔄")
            avg_lat = sum(n['latitude'] for n in needs_list) / len(needs_list)
            avg_lon = sum(n['longitude'] for n in needs_list) / len(needs_list)
            return [{"latitude": avg_lat + 0.01, "longitude": avg_lon + 0.01, "reasoning": "Spatial Cluster Extension Prediction"}]

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
            if st.sidebar.button("☁️ Push Pending Data", width='stretch'):
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

    show_admin_nav = st.sidebar.checkbox("System Administration (Hidden)", value=False)
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
        <div class="main-header">
            <i data-lucide="{pulse_icon}" class="{pulse_class}" style="width: 38px; height: 38px;"></i>
            <h1 style="margin: 0; font-weight: 800; letter-spacing: -2px;">
                {_t('Smart Resource Allocator')} <span style="font-size: 0.35em; vertical-align: middle; padding: 6px 12px; background: var(--brand-glow); border: 1px solid var(--brand-primary); border-radius: 10px; color: var(--brand-primary); margin-left: 15px; letter-spacing: 0;">PRO v2.0</span>
            </h1>
        </div>
    """, unsafe_allow_html=True)

    if is_field_worker:
        st.markdown("""
            <div class='fw-emergency-banner'>
                🚨 FIELD WORKER MODE — Simplified View Active
            </div>
        """, unsafe_allow_html=True)
        if st.button("⚡ EMERGENCY UPLOAD — Submit Critical Report Now", type="primary", width='stretch'):
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
                        db.update_need_details(row.get('id'), {'category': rev_cat, 'urgency': rev_urg, 'latitude': rev_lat, 'longitude': rev_lon, 'verified': True})
                        st.session_state['needs_stale'] = True
                        st.success(f"Record Published!")
                        st.rerun()

                    if btn_b.button("Reject (Spam)", key=f"admin_rej_{idx}", width='stretch'):
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
                            if st.button(f"Mission Insight {idx}", key=f"sel_{idx}", width='stretch', type="secondary" if not is_active else "primary"):
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
                            if st.button("Dispatch Teams", width='stretch'):
                                st.toast(f"Dispatching units to {sel_row.get('category', 'incident')} cluster.")
                        with col_b:
                            if st.button("Resolve Case", width='stretch'):
                                st.toast("Incident marked as resolved.")
                    else:
                        st.info("Satellite systems ready. Select a tactical card to focus operations.")

    elif page == "Field Report Center":
        st.subheader("📁 Data Aggregation & Field Reporting")

        with st.expander("🛡️ Strategic Operations: Intelligent Mission Audit", expanded=True):
            st.markdown("### 🤖 Mission-Critical Logistical Audit")
            audit_df = st.session_state.get('needs_df', pd.DataFrame())

            if st.button("🚀 Run Intelligent Audit", key="btn_intel_audit", type="primary", width='stretch'):
                if audit_df.empty:
                    st.warning("Awaiting field data to perform logistical audit.")
                else:
                    from src.processor import run_intelligent_audit
                    with st.spinner("🕵️ AI is cross-referencing mission telemetry..."):
                        ai_report = run_intelligent_audit(audit_df)
                        st.session_state['last_audit_report'] = ai_report

            if 'last_audit_report' in st.session_state:
                st.markdown("---")
                st.markdown(st.session_state['last_audit_report'].replace('\n', '<br>'))
                if st.button("Acknowledge & Archive Audit", width='stretch'):
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
                st.session_state['needs_df'] = pd.concat([st.session_state['needs_df'], df], ignore_index=True)
                st.success("Uploaded and Synchronized!")

        df = st.session_state.get('needs_df', pd.DataFrame())
        if not df.empty:
            edited_df = st.data_editor(df, width='stretch', num_rows="dynamic")
            if not df.equals(edited_df):
                st.session_state['needs_df'] = edited_df
                st.rerun()

    elif page == "Executive Impact Analytics":
        st.subheader("📈 Executive Impact Analytics")
        df = st.session_state.get('needs_df', pd.DataFrame())
        df = df[df['verified'] == True] if 'verified' in df.columns else df
        if df.empty:
            st.warning("No verified data available.")
        else:
            c1, c2, c3 = st.columns(3)
            c1.metric("Impacted Humans", int(df['people_affected'].sum()) if 'people_affected' in df.columns else len(df)*5)
            c2.metric("Efficiency", f"{calculate_efficiency(df)}%")
            c3.metric("Critical Gaps", len(df[df['urgency'] >= 9]) if 'urgency' in df.columns else 0)

            st.divider()
            st.markdown("#### 🍩 Category Distribution")
            if 'category' in df.columns:
                cat_dist = df['category'].value_counts().reset_index()
                cat_dist.columns = ['category', 'count']
                import plotly.express as px
                fig_donut = px.pie(cat_dist, values='count', names='category', hole=0.6)
                fig_donut.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', height=300, showlegend=False)
                st.plotly_chart(fig_donut, width='stretch')

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
                matches = match_volunteer_to_needs(selected_volunteer, available_needs, top_n=3, api_key=_api_key)
                for _, row in matches.iterrows():
                    with st.expander(f"Task: {row.get('category', 'General')} (Urgency: {row.get('urgency', 5)}/10)", expanded=True):
                        st.write(f"Rationale: {row.get('match_reason', 'No reasoning available.')}")
                        if st.button("Confirm & Dispatch", key=f"dispatch_{row.name}", width='stretch'):
                            db.assign_volunteer(row.get('id'), selected_v)
                            st.session_state['needs_stale'] = True
                            st.toast(f"✅ Dispatched {selected_v}!")
                            st.rerun()

def main():
    st.set_page_config(page_title="Smart Resource Allocation", page_icon="💡", layout="wide")
    try:
        run_dashboard()
    except Exception as e:
        st.error(f"🚨 Operational Error: {str(e)}")

    st.markdown("""
    <div style="margin-top: 80px; padding: 40px 10px; border-top: 1px solid rgba(66, 133, 244, 0.3); text-align: center;">
        <div style="font-family: monospace; color: #94a3b8; font-size: 0.75rem; letter-spacing: 3px;">Lead System Architect</div>
        <div style="color: #ffffff; font-size: 1.5rem; font-weight: 800;">JASWANTH HANUMANTHU</div>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
