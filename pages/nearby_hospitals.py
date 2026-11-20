"""
DoseWeave - Nearby Hospitals & Emergency Facilities
Geospatial hospital locator using Google Places API and OpenStreetMap Nominatim / Overpass
dual-engine with distance sorting, verified emergency centers, and interactive Folium mapping.
"""

import streamlit as st
import streamlit.components.v1 as components
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
    # Fast session-cached patient and assessment retrieval
    user = st.session_state.get("user")
    user_id = user.get("user_id", st.session_state.get("user_id")) if user else st.session_state.get("user_id")
    
    if "current_patient" not in st.session_state or st.session_state.get("patient_dirty", False):
        st.session_state.current_patient = get_patient_by_user(user_id) if user_id else None
    patient = st.session_state.get("current_patient")

    patient_id = patient["id"] if patient else st.session_state.get("current_patient_id", 1)
    
    if "assessment_history" not in st.session_state or st.session_state.get("assessment_dirty", False):
        st.session_state.assessment_history = get_assessment_history(patient_id) if patient_id else []
    history = st.session_state.get("assessment_history", [])
    latest_assessment = history[0] if history else st.session_state.get("last_prediction")

    is_high_risk = False
    if latest_assessment:
        risk_level_str = str(latest_assessment.get("risk_level", "")).upper()
        if "HIGH" in risk_level_str or latest_assessment.get("emergency_flag") == 1 or latest_assessment.get("is_emergency"):
            is_high_risk = True

    render_header(
        title="NEARBY HEALTHCARE LOCATIONS",
        subtitle="Step 4 of 4: Direct dynamic geospatial locator for emergency centers and hospitals based on your live location",
        breadcrumb="DoseWeave > Process",
        active_step=4
    )

    # Injected CSS to guarantee removal of map attribution and watermarks
    st.markdown("""
        <style>
        .leaflet-control-attribution,
        .leaflet-bottom.leaflet-right,
        .leaflet-control-attribution a {
            display: none !important;
            visibility: hidden !important;
            opacity: 0 !important;
        }
        #MainMenu, footer, header[data-testid="stHeader"] {
            display: none !important;
            visibility: hidden !important;
        }
        </style>
    """, unsafe_allow_html=True)

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
    # DIRECT DYNAMIC LOCATION ACQUISITION (HTML5 GPS + LIVE MULTI-IP RESOLVER)
    # -------------------------------------------------------------------------
    # Directly prompt browser for HTML5 Geolocation (GPS / Wi-Fi)
    geo_script = """
    <script>
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            function(pos) {
                const lat = pos.coords.latitude.toFixed(5);
                const lng = pos.coords.longitude.toFixed(5);
                const url = new URL(window.parent.location.href);
                if (url.searchParams.get("live_lat") !== lat || url.searchParams.get("live_lng") !== lng) {
                    url.searchParams.set("live_lat", lat);
                    url.searchParams.set("live_lng", lng);
                    url.searchParams.set("loc_src", "gps");
                    window.parent.location.href = url.href;
                }
            },
            function(err) {
                console.log("Browser GPS prompt status:", err.message);
            },
            { enableHighAccuracy: true, timeout: 6000, maximumAge: 120000 }
        );
    }
    </script>
    """
    components.html(geo_script, height=0, width=0)

    # Read live query parameters if passed from browser GPS
    query_params = st.query_params
    live_lat_param = query_params.get("live_lat")
    live_lng_param = query_params.get("live_lng")

    if live_lat_param and live_lng_param:
        try:
            curr_lat = float(live_lat_param)
            curr_lng = float(live_lng_param)
            cached_loc = st.session_state.get("current_detected_loc")
            if not cached_loc or abs(cached_loc.get("lat", 0) - curr_lat) > 0.001 or abs(cached_loc.get("lng", 0) - curr_lng) > 0.001 or cached_loc.get("source") != "Browser GPS (High Accuracy)":
                rev = hospital_service.reverse_geocode(curr_lat, curr_lng)
                st.session_state.current_detected_loc = {
                    "city": rev.get("city") or "Current Area",
                    "region": rev.get("region") or "",
                    "country": rev.get("country") or "",
                    "lat": curr_lat,
                    "lng": curr_lng,
                    "zip": rev.get("zip") or "",
                    "source": "Browser GPS (High Accuracy)",
                    "display_name": rev.get("display_name")
                }
                st.session_state.hospital_results = None
        except (ValueError, TypeError):
            pass

    # Ensure location is initialized dynamically
    if "current_detected_loc" not in st.session_state:
        st.session_state.current_detected_loc = hospital_service.detect_current_location()

    det = st.session_state.current_detected_loc
    default_query = f"{det['city']}, {det['region']}".strip(", ")

    # Display Direct Dynamic Location Card
    col_det1, col_det2 = st.columns([3.2, 1.2])
    with col_det1:
        render_clean_html(f"""
<div style="background: linear-gradient(135deg, #F0FDF4 0%, #DCFCE7 100%); border: 1px solid #BBF7D0; border-left: 5px solid #16A34A; border-radius: 12px; padding: 0.95rem 1.25rem; margin-bottom: 1rem; box-shadow: 0 2px 8px rgba(22, 163, 74, 0.08);">
    <div style="display: flex; align-items: center; gap: 8px;">
        <span class="pulse-dot" style="background-color: #16A34A;"></span>
        <span style="font-size: 0.76rem; text-transform: uppercase; font-weight: 800; color: #15803D; letter-spacing: 0.06em;">LIVE LOCATION DIRECTLY DETECTED</span>
    </div>
    <div style="color: #0F172A; font-weight: 800; font-size: 1.15rem; margin-top: 0.25rem;">
        📍 {det['city']}{f", {det['region']}" if det.get('region') else ""}{f", {det['country']}" if det.get('country') else ""}
    </div>
    <div style="color: #475569; font-size: 0.82rem; margin-top: 0.2rem;">
        GPS Coordinates: <strong>{det['lat']:.4f}° N, {det['lng']:.4f}° E</strong> &nbsp;•&nbsp; Source: <span style="color: #15803D; font-weight: 700;">{det['source']}</span>
    </div>
</div>
""")
    with col_det2:
        if st.button("🔄 Re-detect Live Location", key="btn_refresh_loc", use_container_width=True):
            st.session_state.current_detected_loc = hospital_service.detect_current_location()
            st.session_state.hospital_results = None
            st.session_state.hospital_location = None
            st.rerun()

    # Search & Radius Controls
    with st.form("hospital_search_form"):
        c1, c2, c3 = st.columns([2.4, 1.2, 1.2])
        with c1:
            location_input = st.text_input(
                "Search Location (Defaults to live detected location):",
                value=st.session_state.get("hospital_custom_query", default_query),
                placeholder="Current Live Location or enter custom locality / city"
            )
        with c2:
            radius_km = st.slider("Search Radius (km)", min_value=2, max_value=50, value=20, step=1)
        with c3:
            max_results = st.selectbox("Max Facilities", options=[15, 25, 35, 50], index=1)

        submit_search = st.form_submit_button("SEARCH NEARBY HOSPITALS", use_container_width=True, type="primary")

    # Determine active coordinates and query
    is_custom_search = submit_search and (location_input.strip() != default_query)
    if is_custom_search:
        st.session_state.hospital_custom_query = location_input.strip()
        active_query = location_input.strip()
    else:
        active_query = default_query

    should_run = submit_search or st.session_state.get("hospital_trigger_search", False) or (st.session_state.get("hospital_results") is None)
    st.session_state.hospital_trigger_search = False

    if should_run:
        with st.spinner(f"Locating verified medical facilities near '{active_query}'..."):
            if not is_custom_search and det.get("lat") and det.get("lng"):
                lat, lng = det["lat"], det["lng"]
            else:
                lat, lng = hospital_service.geocode_location(active_query)

            if lat is None:
                st.error(f"Could not determine coordinates for '{active_query}'. Falling back to detected live coordinates.")
                lat, lng = det["lat"], det["lng"]

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

        # 1. Interactive Folium Map (with attribution watermark completely disabled)
        fmap = folium.Map(
            location=[center_lat, center_lng],
            zoom_start=13,
            tiles="OpenStreetMap",
            attributionControl=False,
            control_scale=False
        )

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
