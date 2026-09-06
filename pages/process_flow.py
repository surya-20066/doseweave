"""
MediSafe AI - Continuous Process Flow Controller
Orchestrates the 4-step sequential clinical pipeline:
  Step 1: COLLECT USER DATA
  Step 2: ANALYSE THE RISK
  Step 3: AI RECOMMENDATION SYSTEM
  Step 4: NEARBY HEALTHCARE LOCATIONS

Features progressive step activation:
  - Step 1: Active
  - Step 2: Locked until Step 1 data is saved
  - Step 3: Locked until Step 2 risk analysis is completed
  - Step 4: Available / Active after recommendations
"""

import streamlit as st
from database.database import get_patient_by_user, get_assessment_history

# Import the 4 underlying pages
from pages.patient_info import render_patient_info
from pages.risk_prediction import render_risk_prediction
from pages.ai_analysis import render_ai_analysis
from pages.nearby_hospitals import render_nearby_hospitals

def render_process_flow():
    user = st.session_state.get("user")
    if not user:
        st.session_state.current_page = "login"
        st.rerun()
        return

    user_id = user.get("user_id", st.session_state.get("user_id", 1))

    # Determine completion status of each step
    patient = get_patient_by_user(user_id)
    has_patient_profile = (patient is not None)

    history = get_assessment_history(patient["id"]) if has_patient_profile else []
    has_risk_assessment = (len(history) > 0 or "last_prediction" in st.session_state)

    has_recommendations = (
        "ai_text_response" in st.session_state 
        or "image_analysis_result" in st.session_state 
        or "last_recommendations" in st.session_state
    )

    # Progression logic
    step1_completed = has_patient_profile
    step2_completed = has_risk_assessment
    step3_completed = has_recommendations
    step4_completed = False

    # Current process step state: 1, 2, 3, or 4
    if "process_step" not in st.session_state:
        # Default smart landing:
        if not step1_completed:
            st.session_state.process_step = 1
        elif not step2_completed:
            st.session_state.process_step = 2
        elif not step3_completed:
            st.session_state.process_step = 3
        else:
            st.session_state.process_step = 1

    current_step = st.session_state.process_step

    # -------------------------------------------------------------------------
    # PROCESS STEP NAVIGATION TABS (Direct Clickable Access to Any Step)
    # -------------------------------------------------------------------------
    st.markdown("""
        <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 14px; padding: 1rem 1.4rem; margin-bottom: 1.5rem; box-shadow: 0 2px 8px rgba(0,0,0,0.03);">
            <div style="font-size: 0.72rem; font-weight: 800; color: #2563EB; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.4rem;">
                CLINICAL PROCESS WORKFLOW
            </div>
            <div style="font-size: 1.15rem; font-weight: 800; color: #0F172A; margin-bottom: 0.75rem;">
                Flexible 4-Step Clinical Intelligence Pipeline
            </div>
            <div style="font-size: 0.85rem; color: #64748B;">
                Click any step at any time to freely document patient data, evaluate ML risk, query AI safety recommendations, or locate nearby healthcare facilities.
            </div>
        </div>
    """, unsafe_allow_html=True)

    # 4 Process Tabs - All completely unlocked and directly clickable
    t_col1, t_col2, t_col3, t_col4 = st.columns(4)

    # Step 1 Button
    with t_col1:
        s1_badge = "✓" if step1_completed else "●"
        s1_label = f"{s1_badge} 1. COLLECT DATA"
        s1_type = "primary" if current_step == 1 else "secondary"
        if st.button(s1_label, key="step_tab_1", use_container_width=True, type=s1_type):
            st.session_state.process_step = 1
            st.rerun()

    # Step 2 Button - Unlocked for direct access anytime
    with t_col2:
        s2_badge = "✓" if step2_completed else ("●" if current_step == 2 else "⚡")
        s2_label = f"{s2_badge} 2. ANALYSE RISK"
        s2_type = "primary" if current_step == 2 else "secondary"
        if st.button(s2_label, key="step_tab_2", use_container_width=True, type=s2_type):
            st.session_state.process_step = 2
            st.rerun()

    # Step 3 Button - Unlocked for direct access anytime
    with t_col3:
        s3_badge = "✓" if step3_completed else ("●" if current_step == 3 else "🤖")
        s3_label = f"{s3_badge} 3. RECOMMENDATIONS"
        s3_type = "primary" if current_step == 3 else "secondary"
        if st.button(s3_label, key="step_tab_3", use_container_width=True, type=s3_type):
            st.session_state.process_step = 3
            st.rerun()

    # Step 4 Button - Unlocked for direct access anytime
    with t_col4:
        s4_badge = "●" if current_step == 4 else "📍"
        s4_label = f"{s4_badge} 4. NEARBY LOCATIONS"
        s4_type = "primary" if current_step == 4 else "secondary"
        if st.button(s4_label, key="step_tab_4", use_container_width=True, type=s4_type):
            st.session_state.process_step = 4
            st.rerun()

    st.markdown("<div style='margin-bottom: 1.25rem;'></div>", unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # RENDER CURRENT STEP PAGE
    # -------------------------------------------------------------------------
    if current_step == 1:
        render_patient_info()
    elif current_step == 2:
        render_risk_prediction()
    elif current_step == 3:
        render_ai_analysis()
    elif current_step == 4:
        render_nearby_hospitals()
    else:
        render_patient_info()
