with open('app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

start_idx = -1
end_idx = -1

for i, line in enumerate(lines):
    if '# 1. Field Resilience Section' in line:
        start_idx = i
        break

for i in range(start_idx + 1, len(lines)):
    if '# --- ? SHINING HIGHLIGHT FOR ACTIVE TOOLS ---' in line:
        pass
    if 'active_tools_css = ""' in lines[i]:
        end_idx = i
        break

if start_idx != -1 and end_idx != -1:
    new_sidebar = '''    # 1. Expanders Grouping
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
            
            try:
                if not _df.empty:
                    _active_crisis = "CRITICAL" if not _df[_df['urgency'] >= 9].empty else "STABLE"
                else:
                    _active_crisis = "STABLE"
            except:
                _active_crisis = "STABLE"
                
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
    new_lines = lines[:start_idx] + [new_sidebar] + lines[end_idx+1:]
    with open('app.py', 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    print(f"Replaced from {start_idx} to {end_idx}")
else:
    print(f"Failed to find indices: {start_idx}, {end_idx}")

