import re

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. API Keys
content = content.replace(
'''# --- ?? Enterprise-Grade Security: API Configuration ---
from src.utils.api_keys import get_google_api_key
_api_key = get_google_api_key()

if _api_key:
    genai.configure(api_key=_api_key)''',
'''# --- ?? Enterprise-Grade Security: API Configuration ---
import streamlit as st
import google.generativeai as genai
try:
    _api_key = st.secrets["GOOGLE_API_KEY"]
except Exception:
    _api_key = None

if _api_key:
    genai.configure(api_key=_api_key)''')

# 2. Map Logic
content = content.replace(
'''    if 'needs_df' not in st.session_state or st.session_state.get('needs_stale', True):
        with st.spinner("??? Synchronizing Mission Telemetry..."):
            st.session_state['needs_df'] = load_cached_mission_data()
            st.session_state['needs_stale'] = False''',
'''    if 'needs_df' not in st.session_state or st.session_state.get('needs_stale', True):
        with st.spinner("??? Synchronizing Mission Telemetry..."):
            db_df = load_cached_mission_data()
            if db_df.empty:
                global_baseline = [
                    {"id": "DEMO_1", "category": "Medical", "urgency": 9, "latitude": 28.6139, "longitude": 77.2090, "city": "Delhi", "description": "Critical", "people_affected": 1250, "status": "Pending", "verified": False},
                    {"id": "DEMO_2", "category": "Food", "urgency": 7, "latitude": 40.7128, "longitude": -74.0060, "city": "New York", "description": "Node leveling", "people_affected": 800, "status": "Verified", "verified": True},
                    {"id": "DEMO_3", "category": "Shelter", "urgency": 8, "latitude": -1.2921, "longitude": 36.8219, "city": "Nairobi", "description": "Displacement", "people_affected": 3200, "status": "Escalated", "verified": False},
                    {"id": "DEMO_4", "category": "Water", "urgency": 10, "latitude": 19.0760, "longitude": 72.8777, "city": "Mumbai", "description": "Desalination", "people_affected": 15000, "status": "Critical", "verified": False},
                    {"id": "DEMO_5", "category": "Power", "urgency": 6, "latitude": 34.0522, "longitude": -118.2437, "city": "Los Angeles", "description": "Grid stabilizing", "people_affected": 450, "status": "Stabilizing", "verified": True}
                ]
                st.session_state['needs_df'] = pd.DataFrame(global_baseline)
            else:
                st.session_state['needs_df'] = db_df
            st.session_state['needs_stale'] = False''')


# 3. Container fixes
content = content.replace(
'''        # --- ??? TOP-TIER MISSION TILE NAVIGATION (Bottom Realignment) ---
        st.markdown("<div style='height: 100px'></div>", unsafe_allow_html=True)
        st.divider()''',
'''        # --- ??? TOP-TIER MISSION TILE NAVIGATION (Bottom Realignment) ---
        with st.container():
            st.markdown("<div style='height: 100px'></div>", unsafe_allow_html=True)
        st.divider()''')


# 4. Sidebar Wipe (Regex replace between # 1. Field Resilience Section and # --- ? SHINING HIGHLIGHT FOR ACTIVE TOOLS ---)
pattern = r'# 1\. Field Resilience Section.*?# --- ? SHINING HIGHLIGHT FOR ACTIVE TOOLS ---'
new_sidebar = '''# 1. Expanders Grouping
    with st.sidebar:
        with st.expander("?? Crisis Ops", expanded=True):
            st.session_state['offline_mode'] = st.toggle("Simulate Field Offline Mode", value=st.session_state.get('offline_mode', False))
            show_admin = st.checkbox("System Administration (Hidden)", value=False)
            nav_options = ["System Dashboard", "Data Upload", "Impact Map", "Executive Impact Analytics", "?? EMERGENCY DISPATCH ??"]
            page_map = {"System Dashboard": "System Dashboard", "Data Upload": "Field Report Center", "Impact Map": "Impact Map", "Executive Impact Analytics": "Executive Impact Analytics", "?? EMERGENCY DISPATCH ??": "Rapid Dispatch"}
            _sel = st.radio("Go to", nav_options, index=0, label_visibility="collapsed")
            if show_admin:
                st.session_state["page"] = "??? Admin Verification"
            else:
                st.session_state["page"] = page_map[_sel]
            
            if st.button("Launch 'Perfect Demo' Mode", use_container_width=True, type="primary"):
                epicenter_lat, epicenter_lon = 28.6139, 77.2090
                st.session_state['demo_active'] = True
                demo_records = []
                import random
                for i in range(20):
                    demo_records.append({"urgency": random.randint(8, 10), "category": random.choice(["Medical", "Food", "Shelter"]), "latitude": epicenter_lat + random.uniform(-0.05, 0.05), "longitude": epicenter_lon + random.uniform(-0.05, 0.05), "description": f"Demo #{i+100}", "people_affected": random.randint(10, 100), "status": "Pending", "verified": True})
                import pandas as pd
                st.session_state['needs_df'] = pd.concat([st.session_state.get('needs_df', pd.DataFrame()), pd.DataFrame(demo_records)], ignore_index=True)
                st.toast("?? Perfect Demo Mode Activated.")
                st.rerun()

        with st.expander("?? Stats & Metrics"):
            st.session_state['high_traffic'] = st.toggle("Simulate High Traffic", value=st.session_state.get('high_traffic', False))
            _df = st.session_state.get('needs_df', pd.DataFrame())
            _total_impact = int(_df['people_affected'].sum()) if not _df.empty and 'people_affected' in _df.columns else len(_df) * 5
            _active_crisis = "CRITICAL" if not _df[_df[_df.columns.intersection(['urgency'])] >= 9].empty else "STABLE"
            
            st.markdown(f'<div style="padding:10px; background:rgba(255,255,255,0.05); border-radius:10px;">Impact: {_total_impact:,}<br>Status: {_active_crisis}</div>', unsafe_allow_html=True)
            if st.session_state.get('sync_queue'):
                st.warning(f"?? {len(st.session_state['sync_queue'])} Reports Pending Sync")

        from src.processor import process_voice_command, translate_text
        with st.expander("??? Tactical Tools"):
            st.session_state['lang'] = st.selectbox("UI Language", ["English", "Hindi", "Telugu"])
            is_light = st.toggle("Minimalist Light Mode")
            st.session_state['theme_mode'] = "Apple-Light" if is_light else "Cyber-Dark"
            low_bandwidth = st.toggle("?? Low Bandwidth Mode", value=False)
            sat_overlay = st.toggle("??? Satellite Intel Overlay", value=False)
            st.session_state['map_style'] = 'satellite' if sat_overlay else 'dark'
            
            voice_input = st.audio_input("Satellite Voice Command")
            if voice_input:
                cmd = process_voice_command(voice_input.read())
                if "error" not in cmd: st.success("? Voice Processed")
                else: st.error("?? Voice Error")

    page = st.session_state["page"]
    active_tools_css = ""
'''
content = re.sub(pattern, new_sidebar, content, flags=re.DOTALL)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Replacement successful")
