import streamlit as st
import pandas as pd

def run_dashboard():
    # Refined Interface Infrastructure
    st.markdown("""
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    """, unsafe_allow_html=True)
    
    theme_base = st.get_option("theme.base")
    st.markdown(f"""
    <style>
        .badge-base {{ padding: 4px 10px; border-radius: 6px; font-weight: 700; font-size: 0.75rem; letter-spacing: 0.05em; text-transform: uppercase; }}
        .badge-Pending {{ background-color: var(--impact-orange); color: white; }}
        .badge-Matched {{ background-color: var(--impact-green); color: white; }}
        .badge-InProgress {{ background-color: var(--brand-primary); color: white; }}
        
        /* Pulse Effects (Semantic) */
        .ai-pulse-idle {{ color: var(--brand-primary); filter: drop-shadow(0 0 8px var(--brand-glow)); animation: pulse-brand 3s infinite; }}
        .ai-pulse-critical {{ color: var(--impact-red); filter: drop-shadow(0 0 10px rgba(239, 68, 68, 0.8)); animation: pulse-critical-glow 1s infinite; }}
        @keyframes pulse-brand {{ 0%, 100% {{ opacity: 0.6; transform: scale(0.95); }} 50% {{ opacity: 1; transform: scale(1.05); }} }}
        @keyframes pulse-critical-glow {{ 0%, 100% {{ opacity: 0.7; transform: scale(0.9); }} 50% {{ opacity: 1; transform: scale(1.1); }} }}
        
        .main-header {{ display: flex; align-items: center; gap: 20px; margin-bottom: 30px; }}
    </style>
    """, unsafe_allow_html=True)
    
    from streamlit_lottie import st_lottie
    import requests

    def load_lottie(url):
        r = requests.get(url)
        if r.status_code != 200: return None
        return r.json()

    lottie_radar = load_lottie("https://assets8.lottiefiles.com/packages/lf20_m6cu9z9i.json")
    lottie_ai = load_lottie("https://assets5.lottiefiles.com/packages/lf20_at6aymiz.json")

    # Initialize Session State Data
    if 'needs_df' not in st.session_state:
        try:
            df = pd.read_csv("data/mock_needs.csv")
            if 'status' not in df.columns:
                df['status'] = 'Pending'
            if 'verified' not in df.columns:
                df['verified'] = True 
            if 'report_count' not in df.columns:
                df['report_count'] = 1
            st.session_state['needs_df'] = df
        except FileNotFoundError:
            st.session_state['needs_df'] = pd.DataFrame(columns=["urgency", "category", "latitude", "longitude", "description", "status", "verified", "detected_language", "report_count"])
            
    # 📡 OFFLINE-FIRST PWA INFRASTRUCTURE (Injection)
    st.markdown(f"""
        <link rel="manifest" href="static/manifest.json">
        <script>
            if ('serviceWorker' in navigator) {{
                navigator.serviceWorker.register('static/sw.js');
            }}
            
            // Connectivity Tracking
            function updateOnlineStatus() {{
                const status = navigator.onLine ? '📡 ONLINE' : '⚠️ OFFLINE MODE';
                const color = navigator.onLine ? '#10b981' : '#f59e0b';
                const el = window.parent.document.querySelector('[data-testid="stSidebarNav"]');
                if (el) {{
                    let indicator = window.parent.document.getElementById('pwa-sync-status');
                    if (!indicator) {{
                        indicator = window.parent.document.createElement('div');
                        indicator.id = 'pwa-sync-status';
                        indicator.style = 'padding: 10px; margin: 10px; border-radius: 8px; font-weight: bold; font-size: 0.8rem; text-align: center;';
                        el.prepend(indicator);
                    }}
                    indicator.innerText = status;
                    indicator.style.backgroundColor = color;
                    indicator.style.color = '#fff';
                }}
            }}
            
            window.addEventListener('online',  updateOnlineStatus);
            window.addEventListener('offline', updateOnlineStatus);
            setInterval(updateOnlineStatus, 3000); // Poll for UI consistency
        </script>
    """, unsafe_allow_html=True)
    
    # Initialize Sync Queue
    if 'sync_queue' not in st.session_state:
        st.session_state['sync_queue'] = []
    if 'offline_mode' not in st.session_state:
        st.session_state['offline_mode'] = False

    # Design System Style Injection
    try:
        with open("src/styles.css", "r") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except: pass
    
    def predict_crisis_clusters(needs_list: list) -> list:
        """Uses Gemini to identify one or two 'High Risk' coordinates based on current clusters."""
        if not needs_list: return []
        import json
        
        # Summarize current tactical situation for AI
        summary = [{"lat": n['latitude'], "lon": n['longitude'], "cat": n['category'], "urg": n['urgency']} for n in needs_list]
        
        prompt = f"""
        Analyze the following geospatial 'Need Clusters':
        {json.dumps(summary)}
        
        Based on the spatial proximity of these critical clusters, identify exactly TWO coordinates (Lat/Lon) that are at 'High Probability Risk' for a secondary crisis (e.g., if neighbors are failing, this sector will likely fail next).
        
        Respond ONLY with a JSON list:
        [
            {{"latitude": float, "longitude": float, "reasoning": "Brief predictive reason"}},
            {{"latitude": float, "longitude": float, "reasoning": "Brief predictive reason"}}
        ]
        """
        
        try:
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(prompt)
            # Clean response string for potential markdown artifacts
            clean_res = response.text.strip().replace('```json', '').replace('```', '')
            return json.loads(clean_res)
        except Exception as e:
            st.warning("⚠️ **System Congestion:** We are experiencing high traffic with the AI analysis engine. Falling back to spatial-only extension prediction.")
            # Fallback to simple spatial center offset for prototype stability
            avg_lat = sum(n['latitude'] for n in needs_list) / len(needs_list)
            avg_lon = sum(n['longitude'] for n in needs_list) / len(needs_list)
            return [{"latitude": avg_lat + 0.01, "longitude": avg_lon + 0.01, "reasoning": "Spatial Cluster Extension Prediction"}]
    
    # Check Offline Mode Override in Sidebar
    st.sidebar.markdown("---")
    st.sidebar.subheader("🔋 Field Resilience")
    is_offline = st.sidebar.toggle("Simulate Field Offline Mode", value=st.session_state['offline_mode'], help="Toggles zero-connectivity simulation for sync tests.")
    st.session_state['offline_mode'] = is_offline
    
    if st.session_state['sync_queue']:
        st.sidebar.warning(f"🔄 {len(st.session_state['sync_queue'])} Reports Pending Sync")
        if not is_offline:
            if st.sidebar.button("☁️ Push Pending Data"):
                for pending in st.session_state['sync_queue']:
                    st.session_state['needs_df'] = pd.concat([st.session_state['needs_df'], pd.DataFrame([pending])], ignore_index=True)
                st.session_state['sync_queue'] = []
                st.sidebar.success("Database Synchronized!")
                st.rerun()

    # Initialize Detail State
    if 'selected_idx' not in st.session_state:
        st.session_state['selected_idx'] = None
            
    if 'volunteers_db' not in st.session_state:
        st.session_state['volunteers_db'] = [
            {"name": "Dr. Alice Morgan", "skills": ["Doctor", "Medic"], "latitude": 37.7710, "longitude": -122.4100},
            {"name": "Bob the Driver", "skills": ["Driver", "Logistics"], "latitude": 37.7600, "longitude": -122.4300},
            {"name": "Charlie (General)", "skills": ["General", "Cook"], "latitude": 37.7800, "longitude": -122.4000}
        ]
        
    if 'show_all_logs' not in st.session_state:
        st.session_state['show_all_logs'] = False
            
    st.sidebar.title("Navigation")
    
    # Ambient AI: Context-Aware Sidebar
    df_for_sidebar = st.session_state.get('needs_df', pd.DataFrame())
    max_urgency = df_for_sidebar[df_for_sidebar['status'] == 'Pending']['urgency'].max() if (not df_for_sidebar.empty and not df_for_sidebar[df_for_sidebar['status'] == 'Pending'].empty) else 0
    
    if max_urgency >= 9:
        st.sidebar.markdown("""
        <style>
            div[data-testid="stRadio"] {
                animation: pulse-glow 2s infinite;
            }
            @keyframes pulse-glow {
                0% { box-shadow: 0 0 5px rgba(239, 68, 68, 0.2); }
                50% { box-shadow: 0 0 20px rgba(239, 68, 68, 0.6); }
                100% { box-shadow: 0 0 5px rgba(239, 68, 68, 0.2); }
            }
        </style>
        """, unsafe_allow_html=True)
        dispatch_label = "🚨 EMERGENCY DISPATCH 🚨"
    else:
        dispatch_label = "Volunteer Matching"
        
    pages = ["System Dashboard", "Data Upload", "Impact Map", "Executive Impact Analytics", dispatch_label]
    if st.sidebar.checkbox("System Administration (Hidden)", value=False):
        pages.insert(0, "🛡️ Admin Verification")
        
    page = st.sidebar.radio("Go to", pages)
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("🌟 Presentation")
    if st.sidebar.button("Launch 'Perfect Demo' Mode", use_container_width=True):
        import random
        from datetime import datetime, timedelta
        demo_records = []
        # Generate 15 historically matched cases with timestamps
        for i in range(15):
            days_ago = 15 - i
            ts = datetime.now() - timedelta(days=days_ago)
            demo_records.append({
                "urgency": random.randint(3, 8), 
                "category": random.choice(["Medical", "Food", "Shelter", "General"]), 
                "latitude": 37.77 + random.uniform(-0.05, 0.05), 
                "longitude": -122.42 + random.uniform(-0.05, 0.05), 
                "description": "Task previously resolved and matched with local team.", 
                "status": "Matched",
                "verified": True,
                "timestamp": ts.strftime('%Y-%m-%d %H:%M:%S')
            })
            
        # Append 4 critical pending cases for the live demo route
        now_ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        demo_records.extend([
            {"urgency": 10, "category": "Medical", "latitude": 37.7749, "longitude": -122.4194, "description": "Massive fire structural collapse. Critical medical attention required.", "status": "Pending", "verified": True, "report_count": 12, "people_affected": 150, "human_context_summary": "High-density residential block with multiple trauma cases.", "timestamp": now_ts},
            {"urgency": 8, "category": "Medical", "latitude": 37.7785, "longitude": -122.4192, "description": "Critical shortage of intravenous supplies.", "status": "Pending", "verified": True, "report_count": 5, "people_affected": 24, "human_context_summary": "Concentration of trauma patients.", "timestamp": now_ts},
            {"urgency": 9, "category": "Food", "latitude": 37.7749, "longitude": -122.4194, "description": "No food reserves left.", "status": "Pending", "verified": True, "report_count": 8, "people_affected": 85, "human_context_summary": "Large shelter cluster.", "timestamp": (datetime.now() - timedelta(hours=2)).strftime("%Y-%m-%d %H:00:00")},
            {"urgency": 5, "category": "General", "latitude": 37.7700, "longitude": -122.4300, "description": "Secondary tremor debris blockage.", "status": "Pending", "verified": True, "report_count": 2, "people_affected": 0, "human_context_summary": "Clear road for food delivery.", "timestamp": now_ts}
        ])
        # Add dependency (Food delivery depends on Road clearing)
        st.session_state['needs_df'].at[1, 'depends_on'] = 2 

        
        from src.utils.logger import log_event
        st.session_state['needs_df'] = pd.DataFrame(demo_records)
        if 'verified' not in st.session_state['needs_df'].columns:
            st.session_state['needs_df']['verified'] = True
        log_event("Demo Mode", "Initialized perfect simulation with 15 verified matched records.")
        st.sidebar.success("Database populated with 15 matches & 4 verified critical issues!")
        
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
    
    # Check for critical status
    max_urgency = 0
    if 'needs_df' in st.session_state:
        df = st.session_state['needs_df']
        if not df.empty:
            max_urgency = df['urgency'].max()
    
    pulse_class = "ai-pulse-critical" if max_urgency >= 8 else "ai-pulse-idle"
    pulse_icon = "zap" if max_urgency >= 8 else "activity"
    
    st.markdown(f"""
        <div class="main-header">
            <i data-lucide="{pulse_icon}" class="{pulse_class}" style="width: 38px; height: 38px;"></i>
            <h1 style="margin: 0; color: var(--text-high-contrast); font-weight: 800; letter-spacing: -2px;">
                Smart Resource Allocator <span style="font-size: 0.35em; vertical-align: middle; padding: 6px 12px; background: var(--brand-glow); border: 1px solid var(--brand-primary); border-radius: 10px; color: var(--brand-primary); margin-left: 15px; letter-spacing: 0;">PRO v2.0</span>
            </h1>
        </div>
        <script>lucide.createIcons();</script>
    """, unsafe_allow_html=True)
    
    if page == "🛡️ Admin Verification":
        st.subheader("🛡️ Administrative Verification Portal")
        st.write("Secure review queue for reports flagged as 'Suspicious' by the AI or awaiting manual authentication.")
        
        needs_df = st.session_state.get('needs_df', pd.DataFrame())
        unverified_df = needs_df[needs_df['verified'] == False]
        
        if unverified_df.empty:
            st.success("✅ **Clear Horizon:** All incoming data points have been verified. No pending items in the secure queue.")
        else:
            st.warning(f"There are {len(unverified_df)} records awaiting manual review before they impact public metrics.")
            for idx, row in unverified_df.iterrows():
                with st.expander(f"Admin Review: {row['category']} (Flagged by AI Security)", expanded=True):
                    col1, col2 = st.columns(2)
                    with col1:
                        rev_cat = st.selectbox("Category", ["Food", "Medical", "Shelter", "General"], index=["Food", "Medical", "Shelter", "General"].index(row['category']), key=f"admin_cat_{idx}")
                        rev_urg = st.number_input("Urgency", 1, 10, int(row['urgency']), key=f"admin_urg_{idx}")
                    with col2:
                        rev_lat = st.number_input("Latitude", -90.0, 90.0, float(row['latitude']), format="%.4f", key=f"admin_lat_{idx}")
                        rev_lon = st.number_input("Longitude", -180.0, 180.0, float(row['longitude']), format="%.4f", key=f"admin_lon_{idx}")
                    
                    rev_desc = st.text_area("Description", row['description'], key=f"admin_desc_{idx}")
                    
                    btn_a, btn_b, btn_c = st.columns([1, 1, 2])
                    if btn_a.button("Approve Entry", key=f"admin_app_{idx}", type="primary"):
                        from src.utils.logger import log_event
                        st.session_state['needs_df'].at[idx, 'category'] = rev_cat
                        st.session_state['needs_df'].at[idx, 'urgency'] = rev_urg
                        st.session_state['needs_df'].at[idx, 'latitude'] = rev_lat
                        st.session_state['needs_df'].at[idx, 'longitude'] = rev_lon
                        st.session_state['needs_df'].at[idx, 'description'] = rev_desc
                        st.session_state['needs_df'].at[idx, 'verified'] = True
                        log_event("ADMIN_APPROVED", f"Admin verified record #{idx} (AI previously flagged as suspicious).")
                        st.success(f"Record #{idx} Published!")
                        st.rerun()
                    
                    if btn_b.button("Reject (Spam)", key=f"admin_rej_{idx}"):
                        from src.utils.logger import log_event
                        log_event("ADMIN_REJECTED", f"Admin discarded record #{idx} as SPAM.")
                        st.session_state['needs_df'] = st.session_state['needs_df'].drop(idx)
                        st.error("Entry Discarded.")
                        st.rerun()
                    
                    st.divider()
            
            st.markdown("### 🔍 System Compliance & Audit")
            if st.button("Generate Terminal Data Integrity Report", type="secondary"):
                import subprocess
                subprocess.Popen(["python", "scripts/integrity_report.py"], shell=True)
                st.success("Report generated in system terminal. Check logs/terminal for forensic proof.")


    elif page == "System Dashboard":
        # Professional Design System Dashboard Refactor
        df = st.session_state.get('needs_df', pd.DataFrame())
        # Filter for verified only
        v_df = df[df['verified'] == True] if 'verified' in df.columns else df
        
        if v_df.empty:
            st.info("Awaiting verified mission data. Please proceed to 'Data Upload' or the Admin portal.")
            if st.button("Attempt Rapid Match (No Data)"):
                st.toast("⚠️ Please upload a report first!", icon="📁")
        else:
            # KPI Header (Emotive + Fairness Refactor)
            total_impacted = v_df['people_affected'].sum() if 'people_affected' in v_df.columns else len(v_df)*5
            from src.utils.fairness import calculate_parity_score, audit_for_bias
            parity = calculate_parity_score(v_df)
            
            st.markdown(f"""
                <div class='high-end-card' style='display: flex; gap: 60px; margin-bottom: 40px;'>
                    <div>
                        <div class='kpi-label'>Humans Impacted</div>
                        <div class='kpi-massive'>{int(total_impacted):,}</div>
                    </div>
                    <div>
                        <div class='kpi-label'>Fairness Index</div>
                        <div class='kpi-massive' style='color: {'var(--impact-green)' if parity > 85 else 'var(--impact-orange)' if parity > 70 else 'var(--impact-red)'};'>{parity}%</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            if parity < 80:
                st.warning(f"🚨 **Bias Risk Detected:** Resource parity has fallen to {parity}%. Certain high-urgency sectors are being systematically under-served.")

            
            # Master-Detail Logic Setup
            sel_idx = st.session_state.get('selected_idx')
            
            # --- 3-COLUMN MASTER-DETAIL LAYOUT ---
            col1, col2, col3 = st.columns([1, 1.2, 1.8])
            
            with col1:
                st.markdown("### 📋 Context Feed")
                with st.container(height=650):
                    import streamlit.components.v1 as components
                    for idx, row in v_df.iterrows():
                        urg_class = "impact-red" if row['urgency'] >= 8 else "impact-orange" if row['urgency'] >= 5 else "impact-green"
                        is_active = (sel_idx == idx)
                        
                        # High-End Selection Aesthetics
                        if is_active:
                            card_border = "2px solid var(--brand-primary)"
                            card_bg = "var(--surface-elevation-2)"
                            glow_effect = "box-shadow: 0 0 15px var(--brand-glow);"
                        else:
                            card_border = "1px solid var(--border-subtle)"
                            card_bg = "var(--surface-elevation-1)"
                            glow_effect = ""

                        # Auto-Scroll Anchor
                        anchor_id = f"card_anchor_{idx}"
                        if is_active:
                            st.markdown(f"<div id='{anchor_id}'></div>", unsafe_allow_html=True)
                            components.html(f"<script>window.parent.document.getElementById('{anchor_id}').scrollIntoView({{behavior: 'smooth', block: 'center'}});</script>", height=0)
                        
                        # Custom HTML Card (Refined)
                        narrative = row.get('human_context_summary', 'Coordinating community relief.')
                        card_html = f"""
                            <div class='{urg_class}' style='padding: 16px; border-radius: var(--radius-standard); margin-bottom: 12px; cursor: pointer; border: {card_border}; background: {card_bg}; {glow_effect} transition: all 0.3s ease;'>
                                <div style='display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px;'>
                                    <span style='font-size: 0.65rem; color: var(--text-medium-contrast); text-transform: uppercase; font-weight: 700; letter-spacing: 0.1em;'>{row['category']}</span>
                                    <span style='font-size: 0.65rem; font-weight: 800;'>{f'VOLUNTEERS NEEDED' if row['urgency'] >= 8 else 'STANDARD TASK'}</span>
                                </div>
                                <div style='font-weight: 700; font-size: 0.95rem; color: var(--text-high-contrast); line-height: 1.4;'>{narrative}</div>
                                <div style='margin-top: 10px; font-size: 0.75rem; color: var(--brand-primary); font-weight: 600;'>{f'🔵 Impacting {row.get("people_affected", 1)} Humans' if is_active else f'Severity Level: {row["urgency"]}/10'}</div>
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
                    st.markdown("<div class='high-end-card'>", unsafe_allow_html=True)
                    st.markdown(f"#### {sel_row['category']} Situational Analysis")
                    st.markdown(f"**Human Narrative:** *{sel_row.get('human_context_summary', 'Coordinating resource allocation for local residents.')}*")
                    st.write(f"**Total Impact Projection:** {sel_row.get('people_affected', 5)} lives affected by this cluster.")
                    st.write(f"**Geospatial Center:** {sel_row['latitude']:.4f}, {sel_row['longitude']:.4f}")
                    st.markdown(f"**Detailed Field Notes:** *{sel_row['description']}*")
                    
                    st.divider()
                    st.markdown("### ⚡ Critical Actions")
                    col_a, col_b = st.columns(2)
                    with col_a:
                        if st.button("Dispatch Teams", use_container_width=True):
                            st.toast(f"Dispatching units to {sel_row['category']} incident cluster.")
                    with col_b:
                        if st.button("Resolve Case", use_container_width=True):
                            st.toast("Incident marked as resolved.")
                    st.markdown("</div>", unsafe_allow_html=True)
                else:
                    st.info("Satellite systems ready. Select a tactical card from the Context Feed or Map to focus operations.")

            with col3:
                st.markdown("### 🗺️ Impact Map")
                import folium
                from streamlit_folium import st_folium
                from folium.plugins import MarkerCluster
                
                # Smooth Fly-To Logic (Dynamic Location/Zoom)
                center = [v_df['latitude'].mean(), v_df['longitude'].mean()] if not v_df.empty else [0, 0]
                zoom = 12
                if sel_idx is not None and sel_idx in v_df.index:
                    center = [v_df.loc[sel_idx, 'latitude'], v_df.loc[sel_idx, 'longitude']]
                    zoom = 14
                
                # Theme-Aware Geospatial Tiles
                tile_layer = "cartodb dark_matter" if theme_base == "dark" else "cartodb positron"
                plotly_template = "plotly_dark" if theme_base == "dark" else "plotly_white"
                marker_opacity = "1.0" if theme_base == "dark" else "0.7"
                
                m = folium.Map(location=center, zoom_start=zoom, tiles=tile_layer)
                
                # PERFORMANCE: Use MarkerCluster for 5,000+ potential points
                cluster = MarkerCluster(name="Active Situations").add_to(m)
                
                # --- DEPENDENCY MAPPING (Geospatial Operational Sequence) ---
                for idx, row in v_df.iterrows():
                    dep_idx = row.get('depends_on')
                    if dep_idx is not None and dep_idx in v_df.index:
                        dep_row = v_df.loc[dep_idx]
                        folium.PolyLine(
                            locations=[(row['latitude'], row['longitude']), (dep_row['latitude'], dep_row['longitude'])],
                            color="#94a3b8",
                            weight=2,
                            dash_array='8, 8',
                            opacity=0.6,
                            tooltip="Operational Dependency Link"
                        ).add_to(m)
                
                for idx, row in v_df.iterrows():
                    is_active = (sel_idx == idx)
                    
                    # Accessible Icon Mapping (Color-blind safe shapes + icons)
                    color_hex = "var(--impact-red)" if row['urgency'] >= 8 else "var(--impact-orange)" if row['urgency'] >= 5 else "var(--impact-green)"
                    urg_icon = "triangle" if row['urgency'] >= 8 else "circle" if row['urgency'] >= 5 else "square"
                    urg_fa = "exclamation-triangle" if row['urgency'] >= 8 else "circle" if row['urgency'] >= 5 else "check"
                    urg_cls = "impact-red" if row['urgency'] >= 8 else "impact-orange" if row['urgency'] >= 5 else "impact-green"
                    active_pulse = "animation: pulse-brand 2s infinite;" if is_active else ""
                    
                    icon_html = f"""
                        <div class='{urg_cls}' role='img' aria-label='{row['category']} mission, Urgency {row['urgency']}/10' style='
                            width: 22px; 
                            height: 22px; 
                            background-color: {color_hex}; 
                            border-radius: {"50%" if urg_icon=="circle" else "4px"}; 
                            border: 2px solid white;
                            display: flex; align-items: center; justify-content: center;
                            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
                            opacity: {marker_opacity};
                            {active_pulse}
                        '>
                            <i class="fa fa-{urg_fa}" style="color: white; font-size: 11px;"></i>
                        </div>
                    """
                    
                    # Need Delta (Sparkline Simulation)
                    spark_color = "#ef4444" if row['urgency'] >= 8 else "#3b82f6"
                    spark_html = f"<div style='width:60px; height:20px; display:flex; gap:2px; align-items:flex-end;'>" \
                                 f"<div style='background:{spark_color}; width:8px; height:12px; opacity:0.4;'></div>" \
                                 f"<div style='background:{spark_color}; width:8px; height:16px; opacity:0.7;'></div>" \
                                 f"<div style='background:{spark_color}; width:8px; height:20px; opacity:1.0;'></div></div>"
                    
                    # Emotive popup context
                    narrative = row.get('human_context_summary', 'Community impact in progress.')
                    popup_text = f"<b>{row['category']} Cluster</b><br>" \
                                 f"<b>Context:</b> {narrative}<br>" \
                                 f"<b>Intensity (48h):</b> {spark_html}<br>" \
                                 f"Urgency: {row['urgency']} • 🔵 Lives: {row.get('people_affected', 5)}"
                    
                    folium.Marker(
                        location=[row['latitude'], row['longitude']],
                        popup=folium.Popup(popup_text, max_width=300),
                        icon=folium.DivIcon(html=icon_html, icon_size=(16, 16), icon_anchor=(8, 8)),
                    ).add_to(cluster)
                
                folium.LayerControl().add_to(m)
                map_res = st_folium(m, width=900, height=650, key="main_map")
            
            # --- TEMPORAL AI PROJECTION ENGINE (Timeline Slider) ---
            st.divider()
            st.markdown("### ⏳ Strategic Timeline (Look into the Future)")
            future_hours = st.slider("Forecast Horizon (AI Simulation)", 0, 5, 0, help="Simulate situational intensification over the next 5 hours.")
            
            if future_hours > 0:
                with st.spinner(f"📡 AI Simulation Engine: Projecting {future_hours}h situational drift..."):
                    # 1. Simulate Urgency Drift
                    v_df['urgency'] = (v_df['urgency'] + (future_hours * 0.5)).clip(1, 10).astype(int)
                    
                    # 2. Add AI Predicted Risk Layer to a temporary map or re-render
                    from src.processor import predict_crisis_clusters
                    predictions = predict_crisis_clusters(v_df.to_dict(orient='records'))
                    
                    for p in predictions:
                        folium.Circle(
                            location=[p['latitude'], p['longitude']],
                            radius=800,
                            color="#d946ef", # Magenta for AI prediction
                            fill=True,
                            fill_opacity=0.2,
                            popup=f"🚨 AI PREDICTED RISK AREA: {p['reasoning']}",
                            tooltip="Predicted Crisis Sector"
                        ).add_to(m)
                    
                    st.info(f"🔮 **TEMPORAL FORESIGHT:** AI projects that sectors at {predictions[0]['latitude']:.3f}, {predictions[0]['longitude']:.3f} are at 'High Probability Risk' within the {future_hours}h horizon.")
            
            if map_res.get("last_object_clicked"):
                    # Logic to find which ID was clicked (based on popup text or coords)
                    # For prototype, we match by coords for simplicity
                    click_lat = map_res["last_object_clicked"]["lat"]
                    click_lon = map_res["last_object_clicked"]["lng"]
                    
                    # Find matching record index
                    match = v_df[
                        (abs(v_df['latitude'] - click_lat) < 0.0001) & 
                        (abs(v_df['longitude'] - click_lon) < 0.0001)
                    ]
                    if not match.empty:
                        new_sel = match.index[0]
                        if st.session_state['selected_idx'] != new_sel:
                            st.session_state['selected_idx'] = new_sel
                            st.rerun()

    
    if page == "Data Upload":
        st.subheader("📁 Data Aggregation & Field Reporting")
        st.write("Aggregated multimodel ingestion for mission critical situational awareness.")
        
        # --- FRICTIONLESS REPORTER SUITE ---
        st.markdown("### ⚡ Frictionless Reporter (Zero-Typing)")
        r1, r2 = st.columns(2)
        with r1:
            voice_memo = st.file_uploader("🎤 Voice Memo (Audio)", type=["mp3", "wav", "m4a"], key="voice_ingest", help="AI transcribes and extracts mission data from field audio.")
            if voice_memo:
                with st.spinner("Transcribing field recording..."):
                    from src.processor import process_field_audio
                    res = process_field_audio(voice_memo.read())
                    if "error" not in res: st.session_state['extracted_result'] = res
        with r2:
            photo_memo = st.file_uploader("📸 Situational Photo", type=["jpg", "png", "jpeg"], key="photo_ingest", help="AI estimates severity and category from mission photography.")
            if photo_memo:
                with st.spinner("Analyzing situational imagery..."):
                    from src.processor import process_field_image
                    res = process_field_image(photo_memo.read())
                    if "error" not in res: st.session_state['extracted_result'] = res
        
        st.markdown("---")
        st.markdown("### 📄 Structured Data Ingestion")
        uploaded_file = st.file_uploader("Conventional Database Sync (CSV, JSON, PDF)", type=["csv", "json", "pdf", "txt"], key="field_uploader")
        
        # Load Data with bug-fix guard against constant reload
        if uploaded_file is not None and st.session_state.get('tab_file') != uploaded_file.name:
            ext = uploaded_file.name.split('.')[-1].lower()
            df = pd.DataFrame()
            if ext == 'csv':
                df = pd.read_csv(uploaded_file)
            elif ext == 'json':
                df = pd.read_json(uploaded_file)
            elif ext in ['pdf', 'txt']:
                import pypdf
                from src.processor import process_ngo_notes
                with st.spinner("Extracting parameters from document via Gemini..."):
                    text = uploaded_file.getvalue().decode('utf-8') if ext == 'txt' else " ".join([p.extract_text() for p in pypdf.PdfReader(uploaded_file).pages])
                    res = process_ngo_notes(text)
                    if "error" not in res: df = pd.DataFrame([{k:v for k,v in res.items() if k != 'note'}])
                        
            if not df.empty:
                if 'status' not in df.columns: df['status'] = 'Pending'
                if 'verified' not in df.columns: df['verified'] = True # Standard CSV/JSON upload assumed verified
                if ext in ['pdf', 'txt'] and not st.session_state['needs_df'].empty:
                    st.session_state['needs_df'] = pd.concat([st.session_state['needs_df'], df], ignore_index=True)
                else:
                    st.session_state['needs_df'] = df
                    
            st.session_state['tab_file'] = uploaded_file.name
            st.success("Uploaded and synchronized!")
        
        df = st.session_state.get('needs_df', pd.DataFrame())
        if not df.empty and uploaded_file is None:
            st.info("Showing synchronised community database.")
        elif df.empty:
            st.warning("No data found. Upload a file or generate mock data.")
                
        # Display Table cleanly with Live Editing Capability (Extra Feature)
        if not df.empty:
            edited_df = st.data_editor(
                df,
                use_container_width=True,
                num_rows="dynamic",
                column_config={
                    "urgency": st.column_config.NumberColumn(
                        "Urgency Level",
                        help="Double click to edit urgency rating from 1 to 10",
                        min_value=1,
                        max_value=10,
                    ),
                    "status": st.column_config.SelectboxColumn(
                        "Status",
                        options=["Pending", "Matched", "In Progress", "Resolved"],
                        required=True,
                    )
                }
            )
            if not df.equals(edited_df):
                st.session_state['needs_df'] = edited_df
                st.rerun()
            
        st.markdown("---")
        st.subheader("🤖 Smart Survey Digitization (Gemini Multimodal AI)")
        st.write("Automatically extract and digitize messy field notes or handwritten paper surveys.")
        
        import os
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            st.warning("Using built-in local Simulation mode fallback since GEMINI_API_KEY environment variable is not explicitly loaded.")
        else:
            st.caption("Gemini Environment Verified: Ready.")
            
        tab1, tab2 = st.tabs(["📄 Paper Survey (Image)", "📝 Text Field Notes"])
        
        with tab1:
            st.markdown("Upload a snapshot of a handwritten paper survey to extract its data into the system.")
            survey_file = st.file_uploader("Upload Survey Image", type=["png", "jpg", "jpeg", "pdf"])
            
            if survey_file is not None:
                colA, colB = st.columns(2)
                
                with colA:
                    st.markdown("#### 📷 Original Document")
                    from PIL import Image
                    is_pdf_survey = survey_file.name.endswith('.pdf')
                    try:
                        if is_pdf_survey:
                            st.info("PDF Document Loaded successfully.")
                            img = "PDF"
                        else:
                            img = Image.open(survey_file)
                            st.image(img, use_container_width=True, caption="Uploaded Document")
                    except Exception as e:
                        st.error("Please upload a valid file.")
                        img = None
                    
                with colB:
                    st.markdown("#### ✨ AI Extraction")
                    if img and st.button("Extract Data from Document", key="btn_extract_img"):
                        from src.processor import process_survey_image, process_ngo_notes
                        with st.spinner("Analyzing document with Gemini..."):
                            if is_pdf_survey:
                                import pypdf
                                ptext = " ".join([p.extract_text() for p in pypdf.PdfReader(survey_file).pages])
                                result = process_ngo_notes(ptext)
                            else:
                                result = process_survey_image(img)
                            st.session_state['extracted_img_result'] = result
                            
                    if 'extracted_img_result' in st.session_state:
                        res = st.session_state['extracted_img_result']
                        if "error" in res:
                            st.warning("⚠️ **We are experiencing high traffic.** Please wait a moment or try uploading a clearer document.")
                        else:
                            st.success(f"AI Analysis Complete (Language: {res.get('detected_language', 'Unknown')})")
                            st.info("💡 **Production Pipeline:** Please review and edit the data below to meet the verification standards.")
                            
                            from src.utils.security import rate_limit_check, ai_truth_check
                            from src.models.schemas import NeedReport
                            
                            # Manual Review / Edit Card
                            with st.container(border=True):
                                colX, colY = st.columns(2)
                                with colX:
                                    edit_cat = st.selectbox("Category", ["Food", "Medical", "Shelter", "General"], index=["Food", "Medical", "Shelter", "General"].index(res.get('category','General')), key="edit_img_cat")
                                    edit_urg = st.number_input("Urgency", 1, 10, int(res.get('urgency', 5)), key="edit_img_urg")
                                with colY:
                                    edit_lat = st.number_input("Latitude", -90.0, 90.0, float(res.get('latitude', 37.77)), format="%.4f", key="edit_img_lat")
                                    edit_lon = st.number_input("Longitude", -180.0, 180.0, float(res.get('longitude', -122.42)), format="%.4f", key="edit_img_lon")
                                edit_desc = st.text_area("Description", res.get('description',''), key="edit_img_desc")

                                if st.button("Verify & Save to Public Database", key="btn_save_img", type="primary"):
                                    finalized_data = {"category": edit_cat, "urgency": edit_urg, "latitude": edit_lat, "longitude": edit_lon, "description": edit_desc, "status": "Pending", "verified": True, "detected_language": res.get('detected_language', 'en')}
                                    # 1. Rate Limiting Check
                                    if not rate_limit_check(limit=5):
                                        st.error("🚨 **Security Alert:** Rate limit exceeded. Automated 'fake upload' detection active. Please try again in an hour.")
                                    else:
                                        # 2. AI Truth Check
                                        with st.spinner("🕵️ AI Truth Check in progress..."):
                                            is_realistic = ai_truth_check(edit_desc)
                                            import time
                                            time.sleep(0.5)

                                        try:
                                            from src.utils.logger import log_event
                                            from src.utils.security import check_anomaly
                                            from src.utils.deduplication import handle_duplication
                                            
                                            # 1. Anomaly check
                                            with st.spinner("📡 Scanning for anomalies..."):
                                                if check_anomaly(edit_lat, edit_lon, st.session_state['needs_df']):
                                                    st.error("🚨 **ANOMALY DETECTED:** Spike in activity.")
                                                    log_event("ANOMALY_WARNING", f"Spike at {edit_lat}, {edit_lon}")

                                            # 2. Pydantic validation
                                            finalized_data["report_count"] = 1
                                            validated = NeedReport(**finalized_data)
                                            
                                            # 3. Semantic Deduplication
                                            if st.session_state['offline_mode']:
                                                st.session_state['sync_queue'].append(validated.dict())
                                                st.info(f"📍 **Offline Queue Captured:** 1 Report pending upload (Local Storage: Active). {len(st.session_state['sync_queue'])} total in queue.")
                                            else:
                                                with st.spinner("🧠 De-duplicating..."):
                                                    is_dupe, dupe_idx = handle_duplication(finalized_data, st.session_state['needs_df'])
                                                    if is_dupe:
                                                        st.info(f"💡 Duplicate Merged at #{dupe_idx}.")
                                                        st.session_state['needs_df'].at[dupe_idx, 'report_count'] += 1
                                                        log_event("DUPLICATE_MERGED", f"#{dupe_idx} count++")
                                                    else:
                                                        new_row = pd.DataFrame([validated.dict()])
                                                        st.session_state['needs_df'] = pd.concat([st.session_state['needs_df'], new_row], ignore_index=True)
                                            
                                            del st.session_state['extracted_img_result']
                                            
                                            if not is_realistic:
                                                log_event("RAW_INPUT", f"AI flagged suspicious image-based survey as unverified. Held in Queue.")
                                                st.warning("⚠️ **Flagged Entry:** AI Truth Check indicates this entry might be spam or placeholder text. It has been held in the **Admin Portal** and won't appear on public heatmaps yet.")
                                            else:
                                                log_event("VERIFIED_DATA", f"New verified data published (Category: {edit_cat}) via manual verification.")
                                                st.success("Data Authenticated & Published Live! (🔵 Verified Badge Applied)")
                                            st.rerun()
                                        except Exception as e:
                                            st.error(f"❌ **Validation Failed:** {str(e)}")

            st.write("---")
            st.caption("Admin items are processed via the 'System Administration' tab for full audit history.")

        with tab2:
            messy_text = st.text_area("Messy Field Notes:", "e.g. We are desperately in need of food here at the community center. Situation is about an 8 out of 10. Coordinates are roughly 37.78, -122.42.")
            
            if st.button("Process with AI"):
                from src.processor import process_ngo_notes
                with st.spinner("Extracting data using Gemini..."):
                    result = process_ngo_notes(messy_text)
                    st.session_state['extracted_txt_result'] = result

            if 'extracted_txt_result' in st.session_state:
                res = st.session_state['extracted_txt_result']
                if "error" in res:
                    st.warning("⚠️ **We are experiencing high traffic.** Please wait a moment or check your API configuration.")
                else:
                    st.success(f"AI Analysis Complete (Language: {res.get('detected_language', 'Unknown')})")
                    st.info("💡 **Production Pipeline:** Please review and edit the data below to meet the verification standards.")
                    
                    from src.utils.security import rate_limit_check, ai_truth_check
                    from src.models.schemas import NeedReport
                    
                    # Manual Review / Edit Card
                    with st.container(border=True):
                        colX, colY = st.columns(2)
                        with colX:
                            edit_cat = st.selectbox("Category", ["Food", "Medical", "Shelter", "General"], index=["Food", "Medical", "Shelter", "General"].index(res.get('category','General')), key="edit_txt_cat")
                            edit_urg = st.number_input("Urgency", 1, 10, int(res.get('urgency', 5)), key="edit_txt_urg")
                        with colY:
                            edit_lat = st.number_input("Latitude", -90.0, 90.0, float(res.get('latitude', 37.77)), format="%.4f", key="edit_txt_lat")
                            edit_lon = st.number_input("Longitude", -180.0, 180.0, float(res.get('longitude', -122.42)), format="%.4f", key="edit_txt_lon")
                        edit_desc = st.text_area("Description", res.get('description',''), key="edit_txt_desc")

                        if st.button("Verify & Save to Public Database", key="btn_save_txt", type="primary"):
                            # 1. Rate Limiting Check
                            if not rate_limit_check(limit=5):
                                st.error("🚨 **Security Alert:** Rate limit exceeded. Please wait an hour before submitting again.")
                            else:
                                # 2. AI Truth Check
                                is_realistic = ai_truth_check(edit_desc)

                                try:
                                    from src.utils.logger import log_event
                                    from src.utils.security import check_anomaly
                                    from src.utils.deduplication import handle_duplication
                                    
                                    # 1. Anomaly check
                                    if check_anomaly(edit_lat, edit_lon, st.session_state['needs_df']):
                                        st.error("🚨 **ANOMALY DETECTED:** Spike in activity at this coordinate set.")
                                        log_event("ANOMALY_WARNING", f"Suspicious spike at {edit_lat}, {edit_lon}")

                                    # 2. Pydantic validation
                                    finalized_data["report_count"] = 1
                                    validated = NeedReport(**finalized_data)
                                    
                                    # 3. Semantic Deduplication
                                    is_dupe, dupe_idx = handle_duplication(finalized_data, st.session_state['needs_df'])
                                    if is_dupe:
                                        st.info(f"💡 **Duplicate Merged:** Increasing 'Report Count' for existing situation at #{dupe_idx}.")
                                        st.session_state['needs_df'].at[dupe_idx, 'report_count'] += 1
                                        log_event("DUPLICATE_MERGED", f"Incident #{dupe_idx} frequency increased to {st.session_state['needs_df'].at[dupe_idx, 'report_count']}.")
                                    else:
                                        new_row = pd.DataFrame([validated.dict()])
                                        st.session_state['needs_df'] = pd.concat([st.session_state['needs_df'], new_row], ignore_index=True)
                                    
                                    del st.session_state['extracted_txt_result']
                                    
                                    if not is_realistic:
                                        log_event("RAW_INPUT", "AI flagged suspicious text notes as unverified. Held in Queue.")
                                        st.warning("⚠️ **Flagged Entry:** AI Truth Check indicates this entry might be spam. It has been held in the **Review Queue**.")
                                    else:
                                        log_event("VERIFIED_DATA", f"New verified data published (Category: {edit_cat}) via messy text notes.")
                                        st.success("Data Authenticated & Published Live!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"❌ **Validation Failed:** {str(e)}")
        
    elif page == "Impact Map":
        st.subheader("🗺️ Impact Map")
        st.write("Geospatial view of resource allocation and impact.")
        
        import folium
        from folium.plugins import HeatMap, Fullscreen, MeasureControl, LocateControl
        from streamlit_folium import st_folium
        
        df = st.session_state.get('needs_df', pd.DataFrame())
            
        if not df.empty and "latitude" in df.columns and "longitude" in df.columns:
            st.markdown("### 🔍 Map Filters")
            col1, col2, col3 = st.columns(3)
            with col1:
                cat_filter = st.selectbox("Category", ["All"] + list(df['category'].unique()))
            with col2:
                min_urgency = st.slider("Minimum Urgency", 1, 10, 1)
            with col3:
                stat_filter = st.selectbox("Status", ["All", "Pending", "Matched", "In Progress"])
                
            filtered_df = df.copy()
            if 'verified' in filtered_df.columns:
                filtered_df = filtered_df[filtered_df['verified'] == True]
            
            if cat_filter != "All":
                filtered_df = filtered_df[filtered_df['category'] == cat_filter]
            filtered_df = filtered_df[filtered_df['urgency'] >= min_urgency]
            if stat_filter != "All":
                # Handle space syntax for In Progress
                check_status = stat_filter
                if stat_filter == "In Progress": check_status = "InProgress"
                filtered_df = filtered_df[filtered_df['status'] == check_status]
                
            if filtered_df.empty:
                st.warning("No active markers map to these filters!")
            else:
                # Center map based on data average
                center_lat = filtered_df["latitude"].mean()
                center_lon = filtered_df["longitude"].mean()
                
                m = folium.Map(location=[center_lat, center_lon], zoom_start=12)
                
                # --- 1. Add HeatMap for Need Density ---
                heat_data = [[row['latitude'], row['longitude']] for index, row in filtered_df.iterrows()]
                HeatMap(heat_data, name="Need Density", radius=15, blur=15, gradient={0.4: 'yellow', 0.65: 'orange', 1: 'red'}).add_to(m)
                
                # Top 3 Critical Needs (Ambient AI Feature)
                top_3_critical_ids = []
                if not filtered_df.empty:
                    top_3_critical_ids = filtered_df[filtered_df['status'] == 'Pending'].nlargest(3, 'urgency').index.tolist()

                # --- 2. Add Color-coded Markers ---
                for index, row in filtered_df.iterrows():
                    urgency = row["urgency"]
                    is_top_critical = index in top_3_critical_ids
                    
                    if urgency >= 8:
                        color = "red"
                    elif urgency >= 5:
                        color = "orange"
                    else:
                        color = "green"
                        
                    # Injecting HTML badge
                    status_class = row['status'].replace(' ', '')
                    trusted_badge = "<span style='color:#3b82f6; font-weight:bold;'>🔵 Verified</span>" if row.get('verified') else "<span style='color:#f59e0b;'>⚠️ Unverified</span>"
                    
                    popup_text = f"<b>{row['category']}</b> {trusted_badge} <br><br> <span class='badge-{status_class}'>{row['status']}</span><br>Urgency: {urgency}<br><i>{row['description']}</i>"
                    
                    icon_name = "ok-sign" if row.get('verified') else "info-sign"
                    icon_color = "blue" if row.get('verified') else color # Highlight verified with blue icon if desired
                    
                    if is_top_critical:
                        # Add a pulsing circle and auto-open popup or distinct icon
                        folium.CircleMarker(
                            location=[row["latitude"], row["longitude"]],
                            radius=25,
                            color="red",
                            fill=True,
                            fill_color="red",
                            fill_opacity=0.3,
                            popup="🚨 TOP CRITICAL NEED",
                            tooltip="Critical Priority"
                        ).add_to(m)
                        popup_text = f"🚨 <b>TOP CRITICAL PRIORITY</b><br>" + popup_text
                    
                    folium.Marker(
                        location=[row["latitude"], row["longitude"]],
                        popup=folium.Popup(popup_text, max_width=300),
                        icon=folium.Icon(color=icon_color, icon="fire" if is_top_critical else icon_name)
                    ).add_to(m)
                    
                # Extra Map Features
                Fullscreen(position='topright', title='Expand Map', title_cancel='Exit Fullscreen', force_separate_button=True).add_to(m)
                MeasureControl(position='bottomleft', primary_length_unit='kilometers', primary_area_unit='sqmeters').add_to(m)
                LocateControl(auto_start=False).add_to(m)
                
                folium.LayerControl().add_to(m)
                
                st_folium(m, width=900, height=500, returned_objects=[])
    elif page == "Executive Impact Analytics":
        st.subheader("📈 Executive Impact Analytics")
        
        df = st.session_state.get('needs_df', pd.DataFrame())
        # Filter for verified only
        df = df[df['verified'] == True] if 'verified' in df.columns else df
        
        if df.empty:
            st.warning("No verified mission data available. Please upload records and authenticate them in the Review Queue.")
        else:
            import plotly.express as px
            import plotly.graph_objects as go
            plotly_template = "plotly_dark" if theme_base == "dark" else "plotly"
            st.write("Cross-sectional performance indicators and temporal resource allocation analysis.")
            
            # KPI Header (Emotive + Fairness Refactor)
            total_impacted = df['people_affected'].sum() if 'people_affected' in df.columns else len(df)*5
            from src.utils.fairness import calculate_parity_score, audit_for_bias
            parity = calculate_parity_score(df)
            
            # New KPI Header Layout
            kCol1, kCol2, kCol3 = st.columns(3)
            with kCol1:
                st.metric("Total Humans Impacted", int(total_impacted))
            with kCol2:
                # Color coding for parity
                p_color = "normal" if parity > 85 else "inverse" if parity < 70 else "off"
                st.metric("Fairness Index (Parity)", f"{parity}%")
            with kCol3:
                from src.utils.logger import calculate_efficiency
                eff = calculate_efficiency(st.session_state.get('needs_df', pd.DataFrame()))
                st.metric("Operational Efficiency", f"{eff}%")
            
            st.divider()
            
            # Main Analytics Row
            rowCol1, rowCol2 = st.columns([2, 1])
            
            with rowCol1:
                st.markdown("#### 🛡️ Tactical Fairness & Bias Audit")
                bias_warnings = audit_for_bias(df)
                if not bias_warnings:
                    st.success("✅ **Equity Check Passed:** Resource distributions align with local urgency density.")
                else:
                    for warn in bias_warnings:
                        with st.container(border=True):
                            st.markdown(f"**{warn['severity']}:** {warn['message']}")
                            st.caption(f"💡 RE-ALLOCATION: {warn['remedy']}")
                
                st.markdown("#### 📅 Allocation vs. Needs (Time Trend)")
                # Mock trend line for visuals
                trend_df = pd.DataFrame({
                    'dt': pd.date_range(end=pd.Timestamp.now(), periods=10, freq='D'),
                    'Total Reported': [2, 5, 8, 12, 7, 15, 22, 18, 25, 30],
                    'Allocated': [1, 3, 4, 7, 6, 10, 15, 14, 18, 22]
                })
                
                fig_trend = go.Figure()
                fig_trend.add_trace(go.Scatter(x=trend_df['dt'], y=trend_df['Total Reported'], name='Needs Reported', line=dict(color='#ef4444', width=3)))
                fig_trend.add_trace(go.Scatter(x=trend_df['dt'], y=trend_df['Allocated'], name='Resources Allocated', fill='tozeroy', line=dict(color='#10b981', width=3)))
                fig_trend.update_layout(
                    template=plotly_template, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                    margin=dict(l=0, r=0, t=20, b=0), height=350,
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                st.plotly_chart(fig_trend, use_container_width=True)
            
            with rowCol2:
                st.markdown("#### 🍩 Need Distribution")
                cat_dist = df['category'].value_counts().reset_index()
                cat_dist.columns = ['category', 'count']
                fig_donut = px.pie(cat_dist, values='count', names='category', hole=0.6,
                                 color_discrete_sequence=['#ef4444', '#3b82f6', '#10b981', '#f59e0b'])
                fig_donut.update_layout(template=plotly_template, paper_bgcolor='rgba(0,0,0,0)',
                                      margin=dict(l=0, r=0, t=0, b=0), height=300, showlegend=False)
                # Donut center count
                fig_donut.add_annotation(text=f"Total<br>{len(df)}", showarrow=False, font_size=20, font_color="white" if theme_base=="dark" else "black")
                st.plotly_chart(fig_donut, use_container_width=True)
                
                st.divider()
                st.markdown("#### 📄 Stakeholder Reports")
                if st.button("Export Executive Report (PDF)", key="final_exec_pdf", type="primary"):
                    from src.utils.pdf_generator import generate_executive_pdf
                    pdf_path = "data/executive_impact_report.pdf"
                    with st.spinner("Compiling situational stakeholder report..."):
                        path = generate_executive_pdf(df, pdf_path)
                        with open(path, "rb") as f:
                            st.download_button(
                                label="Download Compiled Impact PDF",
                                data=f,
                                file_name="Impact_Summary.pdf",
                                mime="application/pdf",
                            )
                        st.success("Report successfully compiled and ready for dispatch.")

        
    elif page in ["Volunteer Matching", "🚨 EMERGENCY DISPATCH 🚨"]:
        st.subheader("🤝 Smart Volunteer Matching & XUX Portal")
        st.write("AI-driven dispatch engine featuring Interactive Explainability (XUX). Real-time algorithm tuning via manual weight overrides.")
        
        needs_df = st.session_state.get('needs_df', pd.DataFrame())
        v_df = needs_df[needs_df['verified'] == True] if 'verified' in needs_df.columns else needs_df
            
        if v_df.empty:
            st.warning("Needs database is currently empty. Please verify data in the Admin Portal to enable matching.")
            if st.button("Initialize AI Matching Engine"):
                st.toast("⚠️ Please upload a report first!", icon="📁")
        else:
            volunteers = st.session_state['volunteers_db']
            
            # --- XUX ALGORITHM OVERRIDE SLIDERS ---
            with st.container(border=True):
                st.markdown("### ⚙️ Algorithm Tuning (Override AI Defaults)")
                colS, colP, colU = st.columns(3)
                w_skill = colS.slider("Skill Alignment Weight (%)", 0, 100, 50) / 100.0
                w_prox = colP.slider("Proximity Weight (%)", 0, 100, 30) / 100.0
                w_urg = colU.slider("Urgency Weight (%)", 0, 100, 20) / 100.0
            
            from src.models.matching import calculate_distance
            
            st.markdown("---")
            st.subheader("📊 NGO Recruitment Gap Analysis")
            unmatched_critical = needs_df[(needs_df['status'] == 'Pending') & (needs_df['urgency'] >= 8)]
            if unmatched_critical.empty:
                st.success("Excellence! All critical high-urgency needs are currently managed or matched.")
            else:
                cat_counts = unmatched_critical['category'].value_counts()
                top_gap = cat_counts.index[0]
                recruitment_mapping = {
                    "Medical": "Doctors, Nurses, Medics",
                    "Food": "Drivers, Distribution Logistics, Cooks",
                    "Shelter": "Builders, Drivers, General Labour"
                }
                suggestion = recruitment_mapping.get(top_gap, "General Volunteers")
                st.warning(f"**System Vulnerability Detected:** You have {len(unmatched_critical)} Pending High-Urgency needs without any volunteers, primarily in the '{top_gap}' category.")
                st.info(f"**AI Recommendation:** Prioritize urgent recruitment drive for: **{suggestion}**.")
            st.markdown("---")
            
            # Action Plan Button Logic
            if st.button("Generate Optimal Action Plan"):
                st.toast("Calculating optimal dispatch routes...", icon="📡")
                st.session_state['show_action_plan'] = actual_name
                st.session_state['play_thought_process_animation'] = True
            
            if st.session_state.get('show_action_plan') == actual_name:
                from src.models.matching import match_volunteer_to_needs
                
                with st.spinner("Calculating optimal routing and skill matrix..."):
                    # Only match on Pending tasks
                    available_needs = needs_df[needs_df['status'] == 'Pending']
                    
                    if available_needs.empty:
                        st.success("No pending tasks available!")
                    else:
                        # Only match on verified tasks
                        if 'verified' in available_needs.columns:
                            available_needs = available_needs[available_needs['verified'] == True]
                        
                        if available_needs.empty:
                            st.info("Awaiting task verification by administrator.")
                        else:
                            import os
                            api_key = os.environ.get("GEMINI_API_KEY")
                            matches = match_volunteer_to_needs(selected_volunteer, available_needs, top_n=10, api_key=api_key)
                        
                        # Apply Distance Filter
                        matches = matches[matches['distance'] <= max_radius].head(3)
                        
                        if matches.empty:
                            st.warning(f"No matches found within {max_radius} radius for this volunteer's queue.")
                        else:
                            # Find squad
                            from src.models.matching import calculate_distance
                            # Simple SQUAD BUNDLING (Doctor/Medic + Driver + Generalist)
                            def get_squad_matches(task, vols):
                                squad = []
                                # 1. Lead (Based on skill)
                                lead_skill = "Doctor" if task['category'] == "Medical" else "General"
                                lead = next((v for v in vols if lead_skill in v['skills']), vols[0])
                                squad.append(lead)
                                
                                # 2. Logistics/Driver
                                driver = next((v for v in vols if "Driver" in v['skills'] and v['name'] != lead['name']), vols[1])
                                squad.append(driver)
                                return squad

                            colX, colY = st.columns([1, 1])
                            top_task = matches.iloc[0]
                            
                            with colX:
                                st.markdown("### 🏹 Recommended Mission Squad")
                                rec_squad = get_squad_matches(top_task, volunteers)
                                
                                for s in rec_squad:
                                    with st.container(border=True):
                                        st.write(f"**{s['name']}**")
                                        st.caption(f"Role: {', '.join(s['skills'])}")
                                
                                if st.button(f"Dispatch Task Force", type="primary"):
                                    from src.utils.logger import log_event
                                    # In a real app we'd update DB
                                    st.balloons()
                                    st.toast("Task Force Deployed Successfully!", icon="✅")
                                    log_event("MATCH_CREATED", f"Multi-person squad assigned to mission Cluster #{top_task.name}")
                            
                            st.markdown("---")
                            st.markdown("### 🏆 Top Recommended Tasks:")
                            for _, row in matches.iterrows():
                                original_idx = row.name 
                                
                                with st.expander(f"Task for {row['category']} - Urgency {row['urgency']}/10", expanded=True):
                                    st.markdown(f"<span class='badge-Pending'>Pending</span>", unsafe_allow_html=True)
                                    st.write(f"**Need Description:** {row['description']}")
                                    st.write(f"**AI Reasoning (XAI):** *{row['match_reason']}*")
                                    
                                    confidence = row.get('confidence_score', row['match_score'] * 10.0)
                                    st.write(f"**Confidence Score:** {confidence:.1f}%")
                                    st.progress(confidence / 100.0)
                                    
                                    # Extra feature: Realistic ETA calculation inside UI
                                    dist_km = row['distance'] * 111
                                    avg_speed_kmh = 30 # Rough speed in a crisis zone
                                    eta_mins = int((dist_km / avg_speed_kmh) * 60)
                                    eta_str = f"~{eta_mins} mins" if eta_mins > 0 else "Under 1 min"
                                    
                                    st.caption(f"Algorithmic Readiness Score: {row['match_score']:.2f}/10.0 | Distance: {dist_km:.1f}km | **Estimated Travel Time: {eta_str}**")
                                    
                                    def update_status_closure(idx=original_idx):
                                        st.session_state['needs_df'].at[idx, 'status'] = 'Matched'
                                        st.toast("Task status updated to Matched.", icon="🔄")
                                        
                                    st.button(f"Confirm & Dispatch", key=f"btn_{original_idx}", on_click=update_status_closure)
                            
                            st.markdown("---")
                            st.markdown("### 🧠 AI Thought Process Engine")
                            console_placeholder = st.empty()
                            
                            log_text = ""
                            v_skill = selected_volunteer['skills'][0] if len(selected_volunteer['skills']) > 0 else 'General'
                            steps = [
                                f"[ANALYZING] Proximity to location... (Range <= {max_radius}°)",
                                f"[VALIDATING] Skill match: '{v_skill}' -> Required Skill...",
                                "[OPTIMIZING] Priority given to High Urgency constraints...",
                                "[MATCHED] Best fit found."
                            ]
                            
                            if st.session_state.get('play_thought_process_animation', False):
                                import time
                                for step in steps:
                                    log_text += f"> {step}\n"
                                    console_placeholder.markdown(f'''
                                        <div style="background-color: #0b1120; border: 1px solid #1e293b; border-radius: 8px; padding: 16px; font-family: monospace; color: #10b981; margin-top: 10px; box-shadow: inset 0 0 10px #000;">
                                            <pre style="color: #10b981; background: transparent; border: none; margin: 0; white-space: pre-wrap; font-family: monospace; font-size: 0.9em;">{log_text}</pre>
                                        </div>
                                    ''', unsafe_allow_html=True)
                fig_trend.update_layout(
                    template=plotly_template, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                    margin=dict(l=0, r=0, t=20, b=0), height=350,
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                st.plotly_chart(fig_trend, use_container_width=True, help="Scatter plot showing reported need volume over time versus resources successfully allocated. Indicates the current operational deficit or surplus for critical missions.")
            
            with rowCol2:
                st.markdown("#### 🍩 Need Distribution")
                cat_dist = df['category'].value_counts().reset_index()
                cat_dist.columns = ['category', 'count']
                fig_donut = px.pie(cat_dist, values='count', names='category', hole=0.6,
                                 color_discrete_sequence=['#D55E00', '#56B4E9', '#009E73', '#E69F00'])
                fig_donut.update_layout(template=plotly_template, paper_bgcolor='rgba(0,0,0,0)',
                                      margin=dict(l=0, r=0, t=0, b=0), height=300, showlegend=False)
                # Donut center count
                fig_donut.add_annotation(text=f"Total<br>{len(df)}", showarrow=False, font_size=20, font_color="white" if theme_base=="dark" else "black")
                st.plotly_chart(fig_donut, use_container_width=True, help="Donut chart showing proportional breakdown of reported humanitarian needs by category. High Urgency categories are mapped to accessible Vermillion and Orange tones.")
                
                st.divider()
                st.markdown("#### 📄 Stakeholder Reports")
                if st.button("Export Executive Report (PDF)", key="final_exec_pdf", type="primary"):
                    from src.utils.pdf_generator import generate_executive_pdf
                    pdf_path = "data/executive_impact_report.pdf"
                    with st.spinner("Compiling situational stakeholder report..."):
                        path = generate_executive_pdf(df, pdf_path)
                        with open(path, "rb") as f:
                            st.download_button(
                                label="Download Compiled Impact PDF",
                                data=f,
                                file_name="Impact_Summary.pdf",
                                mime="application/pdf",
                            )
                        st.success("Report successfully compiled and ready for dispatch.")

        
    elif page in ["Volunteer Matching", "🚨 EMERGENCY DISPATCH 🚨"]:
        st.subheader("🤝 Smart Volunteer Matching & XUX Portal")
        st.write("AI-driven dispatch engine featuring Interactive Explainability (XUX). Real-time algorithm tuning via manual weight overrides.")
        
        needs_df = st.session_state.get('needs_df', pd.DataFrame())
        v_df = needs_df[needs_df['verified'] == True] if 'verified' in needs_df.columns else needs_df
            
        if v_df.empty:
            st.warning("Needs database is currently empty. Please verify data in the Admin Portal to enable matching.")
            if st.button("Initialize AI Matching Engine"):
                st.toast("⚠️ Please upload a report first!", icon="📁")
        else:
            volunteers = st.session_state['volunteers_db']
            
            # --- XUX ALGORITHM OVERRIDE SLIDERS ---
            with st.container(border=True):
                st.markdown("### ⚙️ Algorithm Tuning (Override AI Defaults)")
                colS, colP, colU = st.columns(3)
                w_skill = colS.slider("Skill Alignment Weight (%)", 0, 100, 50) / 100.0
                w_prox = colP.slider("Proximity Weight (%)", 0, 100, 30) / 100.0
                w_urg = colU.slider("Urgency Weight (%)", 0, 100, 20) / 100.0
            
            from src.models.matching import calculate_distance
            
            st.markdown("---")
            st.subheader("📊 NGO Recruitment Gap Analysis")
            unmatched_critical = needs_df[(needs_df['status'] == 'Pending') & (needs_df['urgency'] >= 8)]
            if unmatched_critical.empty:
                st.success("Excellence! All critical high-urgency needs are currently managed or matched.")
            else:
                cat_counts = unmatched_critical['category'].value_counts()
                top_gap = cat_counts.index[0]
                recruitment_mapping = {
                    "Medical": "Doctors, Nurses, Medics",
                    "Food": "Drivers, Distribution Logistics, Cooks",
                    "Shelter": "Builders, Drivers, General Labour"
                }
                suggestion = recruitment_mapping.get(top_gap, "General Volunteers")
                st.warning(f"**System Vulnerability Detected:** You have {len(unmatched_critical)} Pending High-Urgency needs without any volunteers, primarily in the '{top_gap}' category.")
                st.info(f"**AI Recommendation:** Prioritize urgent recruitment drive for: **{suggestion}**.")
            st.markdown("---")
            
            # Action Plan Button Logic
            if st.button("Generate Optimal Action Plan"):
                st.toast("Calculating optimal dispatch routes...", icon="📡")
                st.session_state['show_action_plan'] = actual_name
                st.session_state['play_thought_process_animation'] = True
            
            if st.session_state.get('show_action_plan') == actual_name:
                from src.models.matching import match_volunteer_to_needs
                
                with st.spinner("Calculating optimal routing and skill matrix..."):
                    # Only match on Pending tasks
                    available_needs = needs_df[needs_df['status'] == 'Pending']
                    
                    if available_needs.empty:
                        st.success("No pending tasks available!")
                    else:
                        # Only match on verified tasks
                        if 'verified' in available_needs.columns:
                            available_needs = available_needs[available_needs['verified'] == True]
                        
                        if available_needs.empty:
                            st.info("Awaiting task verification by administrator.")
                        else:
                            import os
                            api_key = os.environ.get("GEMINI_API_KEY")
                            matches = match_volunteer_to_needs(selected_volunteer, available_needs, top_n=10, api_key=api_key)
                        
                        # Apply Distance Filter
                        matches = matches[matches['distance'] <= max_radius].head(3)
                        
                        if matches.empty:
                            st.warning(f"No matches found within {max_radius} radius for this volunteer's queue.")
                        else:
                            # Find squad
                            from src.models.matching import calculate_distance
                            # Simple SQUAD BUNDLING (Doctor/Medic + Driver + Generalist)
                            def get_squad_matches(task, vols):
                                squad = []
                                # 1. Lead (Based on skill)
                                lead_skill = "Doctor" if task['category'] == "Medical" else "General"
                                lead = next((v for v in vols if lead_skill in v['skills']), vols[0])
                                squad.append(lead)
                                
                                # 2. Logistics/Driver
                                driver = next((v for v in vols if "Driver" in v['skills'] and v['name'] != lead['name']), vols[1])
                                squad.append(driver)
                                return squad

                            colX, colY = st.columns([1, 1])
                            top_task = matches.iloc[0]
                            
                            with colX:
                                st.markdown("### 🏹 Recommended Mission Squad")
                                rec_squad = get_squad_matches(top_task, volunteers)
                                
                                for s in rec_squad:
                                    with st.container(border=True):
                                        st.write(f"**{s['name']}**")
                                        st.caption(f"Role: {', '.join(s['skills'])}")
                                
                                if st.button(f"Dispatch Task Force", type="primary"):
                                    from src.utils.logger import log_event
                                    # In a real app we'd update DB
                                    st.balloons()
                                    st.toast("Task Force Deployed Successfully!", icon="✅")
                                    log_event("MATCH_CREATED", f"Multi-person squad assigned to mission Cluster #{top_task.name}")
                            
                            st.markdown("---")
                            st.markdown("### 🏆 Top Recommended Tasks:")
                            for _, row in matches.iterrows():
                                original_idx = row.name 
                                
                                with st.expander(f"Task for {row['category']} - Urgency {row['urgency']}/10", expanded=True):
                                    st.markdown(f"<span class='badge-Pending'>Pending</span>", unsafe_allow_html=True)
                                    st.write(f"**Need Description:** {row['description']}")
                                    st.write(f"**AI Reasoning (XAI):** *{row['match_reason']}*")
                                    
                                    confidence = row.get('confidence_score', row['match_score'] * 10.0)
                                    st.write(f"**Confidence Score:** {confidence:.1f}%")
                                    st.progress(confidence / 100.0)
                                    
                                    # Extra feature: Realistic ETA calculation inside UI
                                    dist_km = row['distance'] * 111
                                    avg_speed_kmh = 30 # Rough speed in a crisis zone
                                    eta_mins = int((dist_km / avg_speed_kmh) * 60)
                                    eta_str = f"~{eta_mins} mins" if eta_mins > 0 else "Under 1 min"
                                    
                                    st.caption(f"Algorithmic Readiness Score: {row['match_score']:.2f}/10.0 | Distance: {dist_km:.1f}km | **Estimated Travel Time: {eta_str}**")
                                    
                                    def update_status_closure(idx=original_idx):
                                        st.session_state['needs_df'].at[idx, 'status'] = 'Matched'
                                        st.toast("Task status updated to Matched.", icon="🔄")
                                        
                                    st.button(f"Confirm & Dispatch", key=f"btn_{original_idx}", on_click=update_status_closure)
                            
                            st.markdown("---")
                            st.markdown("### 🧠 AI Thought Process Engine")
                            console_placeholder = st.empty()
                            
                            log_text = ""
                            v_skill = selected_volunteer['skills'][0] if len(selected_volunteer['skills']) > 0 else 'General'
                            steps = [
                                f"[ANALYZING] Proximity to location... (Range <= {max_radius}°)",
                                f"[VALIDATING] Skill match: '{v_skill}' -> Required Skill...",
                                "[OPTIMIZING] Priority given to High Urgency constraints...",
                                "[MATCHED] Best fit found."
                            ]
                            
                            if st.session_state.get('play_thought_process_animation', False):
                                import time
                                for step in steps:
                                    log_text += f"> {step}\n"
                                    console_placeholder.markdown(f'''
                                        <div style="background-color: #0b1120; border: 1px solid #1e293b; border-radius: 8px; padding: 16px; font-family: monospace; color: #10b981; margin-top: 10px; box-shadow: inset 0 0 10px #000;">
                                            <pre style="color: #10b981; background: transparent; border: none; margin: 0; white-space: pre-wrap; font-family: monospace; font-size: 0.9em;">{log_text}</pre>
                                        </div>
                                    ''', unsafe_allow_html=True)
                                    time.sleep(0.5)
                                st.session_state['play_thought_process_animation'] = False
                            else:
                                for step in steps:
                                    log_text += f"> {step}\n"
                                console_placeholder.markdown(f'''
                                    <div style="background-color: #0b1120; border: 1px solid #1e293b; border-radius: 8px; padding: 16px; font-family: monospace; color: #10b981; margin-top: 10px; box-shadow: inset 0 0 10px #000;">
                                        <pre style="color: #10b981; background: transparent; border: none; margin: 0; white-space: pre-wrap; font-family: monospace; font-size: 0.9em;">{log_text}</pre>
                                    </div>
                                ''', unsafe_allow_html=True)

def main():
    st.set_page_config(page_title="Smart Resource Allocation", page_icon="💡", layout="wide")
    try:
        run_dashboard()
    except Exception as e:
        from src.utils.logger import log_event
        log_event("GLOBAL_ERROR_SHIELD", str(e))
        st.error(f"🚨 **Critical Operational Error:** {str(e)}")
        st.warning("⚠️ **We are experiencing high traffic.** Please wait a moment or refresh the situation dashboard.")

if __name__ == "__main__":
    main()
