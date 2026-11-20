"""
DoseWeave - Emergency Alert Banner Component
Renders high-acuity clinical red-flag alert box with instant navigation to emergency assistance.
"""

import streamlit as st
from typing import List

def render_emergency_alert(flagged_symptoms: List[str]):
    symptoms_str = ", ".join(flagged_symptoms) if flagged_symptoms else "Critical clinical indicators"
    st.markdown(f"""
        <div class="emergency-banner">
            <div class="emergency-banner-title">⚠️ URGENT MEDICAL ATTENTION RECOMMENDED</div>
            <div class="emergency-banner-text">
                The current clinical assessment detected acute red-flag symptoms: <strong>{symptoms_str}</strong>.
                Immediate professional emergency evaluation is strongly indicated. Do not drive yourself.
            </div>
            <div style="font-size: 0.8rem; color: #991B1B; font-weight: 600;">
                CALL 112 (Universal) / 911 / 999 OR DISPATCH EMERGENCY PARAMEDICS IMMEDIATELY.
            </div>
        </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("🚨 Find Nearest Emergency Hospital", key="alert_find_hospital", use_container_width=True, type="primary"):
            st.session_state.process_step = 4
            st.session_state.current_page = "process"
            st.rerun()
    with col2:
        if st.button("💬 Consult AI Safety Assistant", key="alert_consult_ai", use_container_width=True):
            st.session_state.process_step = 3
            st.session_state.current_page = "process"
            st.rerun()
