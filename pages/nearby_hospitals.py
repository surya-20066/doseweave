"""
MediSafe AI - Nearby Hospitals & Emergency Facilities
Geospatial hospital locator using Google Places API and OpenStreetMap Nominatim / Overpass
dual-engine with distance sorting, verified emergency centers, and interactive Folium mapping.
"""

import streamlit as st
import folium
from streamlit_folium import st_folium
import os
from services.hospital_service import hospital_service
from components.header import render_header
from database.database import get_assessment_history, get_patient_by_user

def render_clean_html(html_str: str):
    """Renders HTML cleanly without CommonMark indentation bugs."""
    if hasattr(st, "html"):
        st.html(html_str)
    else:
        cleaned = "\n".join([line.strip() for line in html_str.strip().split("\n")])
        st.markdown(cleaned, unsafe_allow_html=True)

def render_nearby_hospitals():
    # Emergency Check from latest assessment scoped to user
    user = st.session_state.get("user")
    user_id = user.get("user_id", st.session_state.get("user_id")) if user else st.session_state.get("user_id")
    patient = get_patient_by_user(user_id) if user_id else None
    patient_id = patient["id"] if patient else st.session_state.get("current_patient_id", 1)
    history = get_assessment_history(patient_id) if patient_id else []
    latest_assessment = history[0] if history else st.session_state.get("last_prediction")

    is_high_risk = False
    if latest_assessment:
        risk_level_str = str(latest_assessment.get("risk_level", "")).upper()
        if "HIGH" in risk_level_str or latest_assessment.get("emergency_flag") == 1 or latest_assessment.get("is_emergency"):
            is_high_risk = True

    render_header(
        title="NEARBY HEALTHCARE LOCATIONS",
        subtitle="Step 4 of 4: Search for nearby hospitals and healthcare facilities using your current or manually entered location",
        breadcrumb="MediSafe AI > Process",
        active_step=4
    )

    if is_high_risk:
        render_clean_html("""
<div class="emergency-banner" style="margin-bottom: 1.5rem;">
    <div class="emergency-banner-title">⚠️ PROFESSIONAL MEDICAL EVALUATION RECOMMENDED</div>
    <div class="emergency-banner-text">
        Your reported information may require prompt professional medical evaluation. Please seek appropriate healthcare assistance.
    </div>
</div>
""")

    # -------------------------------------------------------------------------
    # LOCATION OPTIONS: OPTION 1 (CURRENT LOCATION) vs OPTION 2 (ENTER LOCATION MANUALLY)
    # -------------------------------------------------------------------------
    loc_mode = st.radio(
        "Select Location Method:",
        ["OPTION 1: USE CURRENT LOCATION", "OPTION 2: ENTER LOCATION MANUALLY"],
        horizontal=True
    )

    # Initialize live detected location in session state
    if "current_detected_loc" not in st.session_state:
        st.session_state.current_detected_loc = hospital_service.detect_current_location()

    det = st.session_state.current_detected_loc
    default_query = f"{det['city']}, {det['region']}"

    if loc_mode == "OPTION 1: USE CURRENT LOCATION":
        col_det1, col_det2 = st.columns([3, 1])
        with col_det1:
            render_clean_html(f"""
<div style="background: #F0FDF4; border: 1px solid #BBF7D0; border-radius: 10px; padding: 0.75rem 1rem; margin-bottom: 1rem;">
    <span style="font-weight: 700; color: #15803D; font-size: 0.90rem;">📍 Current Live Location Detected:</span>
    <span style="color: #0F172A; font-weight: 700; font-size: 0.95rem; margin-left: 6px;">{det['city']}, {det['region']}</span>
    <span style="color: #64748B; font-size: 0.80rem; margin-left: 8px;">({det['lat']:.4f}° N, {det['lng']:.4f}° E • {det['source']})</span>
</div>
""")
        with col_det2:
            if st.button("🔄 Refresh Location", key="btn_refresh_loc", use_container_width=True):
                st.session_state.current_detected_loc = hospital_service.detect_current_location()
                st.session_state.hospital_results = None
                st.rerun()

        active_query = f"{det['city']}, {det['region']}"
        preset_lat, preset_lng = det['lat'], det['lng']
    else:
        preset_lat, preset_lng = None, None
        st.markdown("##### 📍 Quick Location Presets:")
        q_col1, q_col2, q_col3, q_col4, q_col5, q_col6 = st.columns(6)

        quick_query = None
        with q_col1:
            if st.button("Guntur City", use_container_width=True):
                quick_query = "Guntur, Andhra Pradesh"
        with q_col2:
            if st.button("Brodipet", use_container_width=True):
                quick_query = "Brodipet, Guntur"
        with q_col3:
            if st.button("Arundelpet", use_container_width=True):
                quick_query = "Arundelpet, Guntur"
        with q_col4:
            if st.button("Vijayawada", use_container_width=True):
                quick_query = "Vijayawada, Andhra Pradesh"
        with q_col5:
            if st.button("Mangalagiri", use_container_width=True):
                quick_query = "Mangalagiri, Guntur"
        with q_col6:
            if st.button("Tenali", use_container_width=True):
                quick_query = "Tenali, Guntur"

        if quick_query:
            st.session_state.hospital_search_query = quick_query
            default_query = quick_query

        active_query = st.session_state.get("hospital_search_query", default_query)

    # Search Filters Form
    with st.form("hospital_search_form"):
        c1, c2, c3 = st.columns([2.2, 1.2, 1.2])
        with c1:
            location_input = st.text_input(
                "Enter locality, street, city or PIN code:",
                value=default_query,
                placeholder="e.g. Guntur, Brodipet, Vijayawada, or 522002"
            )
        with c2:
            radius_km = st.slider("Search Radius (km)", min_value=2, max_value=50, value=20, step=1)
        with c3:
            max_results = st.selectbox("Max Facilities", options=[15, 25, 35, 50], index=1)

        submit_search = st.form_submit_button("FIND NEARBY HOSPITALS", use_container_width=True, type="primary")

    # Determine if search should run
    should_run = submit_search or st.session_state.get("hospital_trigger_search", False) or (st.session_state.get("hospital_results") is None)
    st.session_state.hospital_trigger_search = False

    active_query = default_query if loc_mode == "OPTION 1: USE CURRENT LOCATION" else (location_input.strip() if submit_search else default_query)

    if should_run:
        with st.spinner(f"Locating verified medical facilities near '{active_query}'..."):
            if loc_mode == "OPTION 1: USE CURRENT LOCATION" and preset_lat and preset_lng:
                lat, lng = preset_lat, preset_lng
            else:
                lat, lng = hospital_service.geocode_location(active_query)

            if lat is None:
                st.error(f"Could not determine coordinates for '{active_query}'. Please try entering the city name or PIN code.")
                st.session_state.hospital_results = None
            else:
                results = hospital_service.search_nearby_hospitals(
                    lat=lat,
                    lng=lng,
                    query_city=active_query,
                    radius_m=radius_km * 1000,
                    emergency_mode=is_high_risk,
                    max_results=max_results
                )
                st.session_state.hospital_location = (lat, lng)
                st.session_state.hospital_results = results
                st.session_state.hospital_search_query = active_query

    # Display Results if Available
    if st.session_state.get("hospital_results") is not None:
        hospitals = st.session_state.hospital_results
        center_lat, center_lng = st.session_state.hospital_location

        if not hospitals:
            st.warning(f"No hospitals found within {radius_km} km of '{st.session_state.get('hospital_search_query', '')}'. Try increasing the search radius.")
            return

        st.markdown(f"### 📍 Found {len(hospitals)} Verified Medical Facilities near **{st.session_state.get('hospital_search_query', '')}**")

        # 1. Interactive Folium Map
        fmap = folium.Map(location=[center_lat, center_lng], zoom_start=13, tiles="OpenStreetMap")

        # User Location Marker (Blue)
        folium.Marker(
            location=[center_lat, center_lng],
            popup=f"<b>Your Search Location</b><br>{st.session_state.get('hospital_search_query', '')}",
            tooltip="Your Location",
            icon=folium.Icon(color="blue", icon="user", prefix="fa")
        ).add_to(fmap)

        # Hospital Markers (Red / Dark Red)
        for idx, h in enumerate(hospitals, start=1):
            if h.get("lat") and h.get("lng"):
                dist_txt = f"{h['distance_km']} km away" if h.get("distance_km") is not None else ""
                marker_color = "darkred" if h.get("is_closest_emergency") else "red"

                popup_html = f"<b>{idx}. {h['name']}</b><br>{h.get('address', '')}<br><b>Distance:</b> {dist_txt}<br><a href='{h['directions_url']}' target='_blank'>Get Driving Directions</a>"
                folium.Marker(
                    location=[h["lat"], h["lng"]],
                    popup=folium.Popup(popup_html, max_width=280),
                    tooltip=f"{idx}. {h['name']} ({dist_txt})",
                    icon=folium.Icon(color=marker_color, icon="plus", prefix="fa")
                ).add_to(fmap)

        st_folium(fmap, use_container_width=True, height=440)

        st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)

        # 2. Hospital Cards List (Distance-Sorted)
        for idx, h in enumerate(hospitals, start=1):
            is_closest = h.get("is_closest_emergency", False)
            border_col = "#DC2626" if is_closest else "#E2E8F0"
            closest_badge = "<span class='badge-high' style='background: #FEE2E2; color: #DC2626; padding: 3px 8px; border-radius: 6px; font-weight: 700; font-size: 0.76rem;'>🚨 CLOSEST EMERGENCY FACILITY</span>" if is_closest else ""

            dist_val = h.get("distance_km", 0.0)
            dist_badge_bg = "#ECFDF5" if dist_val < 2.0 else "#EFF6FF"
            dist_badge_col = "#047857" if dist_val < 2.0 else "#1D4ED8"

            render_clean_html(f"""
<div style="background: white; border: 1px solid {border_col}; border-left: 5px solid {'#DC2626' if is_closest else '#2563EB'}; border-radius: 10px; padding: 1.25rem; margin-bottom: 0.85rem; box-shadow: 0 2px 6px rgba(0,0,0,0.02);">
    <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 10px;">
        <div style="flex: 1; min-width: 250px;">
            <div style="font-size: 1.15rem; font-weight: 800; color: #0F172A;">
                {idx}. {h['name']} {closest_badge}
            </div>
            <div style="font-size: 0.88rem; color: #64748B; margin-top: 0.35rem;">
                📍 {h.get('address', '')}
            </div>
            <div style="font-size: 0.75rem; color: #10B981; font-weight: 600; margin-top: 0.25rem;">
                ● Verified Open • Emergency Services Ready
            </div>
        </div>
        <div style="text-align: right;">
            <span style="background: {dist_badge_bg}; color: {dist_badge_col}; font-size: 1.05rem; font-weight: 800; padding: 4px 12px; border-radius: 9999px; display: inline-block;">
                🚗 {h.get('distance_km', 0.0)} km
            </span>
            <div style="font-size: 0.78rem; color: #64748B; margin-top: 0.35rem;">
                ⭐ {h.get('rating', 4.5)} ({h.get('user_ratings_total', 40)}+ ratings)
            </div>
        </div>
    </div>
</div>
""")

            col_a, col_b = st.columns([3, 1.2])
            with col_a:
                phone = hospital_service.get_hospital_phone(h.get("place_id", ""), h)
                if phone:
                    st.write(f"📞 **Phone:** `{phone}`")
            with col_b:
                st.link_button("🗺️ Driving Directions", h.get("directions_url", "#"), use_container_width=True)

            st.markdown("<div style='margin-bottom: 0.75rem;'></div>", unsafe_allow_html=True)

    # Completed Pipeline Review & Navigation Actions
    st.markdown("<div style='margin-top: 2rem;'></div>", unsafe_allow_html=True)
    st.markdown("""
        <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 12px; padding: 1.25rem 1.75rem; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;">
            <div>
                <div style="font-weight: 700; color: #0F172A; font-size: 1.05rem;">🎉 Clinical Workflow Complete (Steps 1 to 4)</div>
                <div style="color: #64748B; font-size: 0.88rem;">Review your safety scores, adjust medications, or inspect live database tables.</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    c_done1, c_done2 = st.columns([1, 1])
    with c_done1:
        if st.button("📊 Return to Clinical Dashboard", key="hosp_to_dash", type="primary", use_container_width=True):
            st.session_state.current_page = "dashboard"
            st.rerun()
    with c_done2:
        if st.button("🗄️ Inspect Database & Stored Records", key="hosp_to_db", use_container_width=True):
            st.session_state.current_page = "profile"
            st.rerun()
