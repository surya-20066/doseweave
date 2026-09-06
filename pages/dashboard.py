"""
MediSafe AI - User Dashboard & Workflow Progress
Guides the authenticated user through the clinical safety journey with live progress status.
"""

import streamlit as st
from database.database import (
    get_patient_by_user, get_patient_medications, get_patient_foods,
    get_patient_symptoms, get_assessment_history
)
from services.interaction_service import interaction_service
from services.emergency_service import emergency_service
from components.metric_cards import render_metrics_row
from components.risk_gauge import render_risk_gauge
from components.emergency_alert import render_emergency_alert

def render_dashboard():
    user = st.session_state.get("user")
    user_id = st.session_state.get("user_id", 1)
    user_name = user.get("full_name", "User") if user else "User"

    # Fetch patient profile scoped to this user
    patient = get_patient_by_user(user_id)
    has_patient_profile = (patient is not None)

    patient_id = patient["id"] if has_patient_profile else None
    medications = get_patient_medications(patient_id, active_only=True) if has_patient_profile else []
    foods = get_patient_foods(patient_id) if has_patient_profile else []
    symptoms = get_patient_symptoms(patient_id) if has_patient_profile else []
    history = get_assessment_history(patient_id) if has_patient_profile else []

    has_prediction = len(history) > 0
    latest_assessment = history[0] if has_prediction else None

    # Interactions & Emergency Triage
    interaction_data = interaction_service.analyze_all(
        medications=medications,
        foods=foods,
        conditions=patient.get("conditions", []) if patient else [],
        allergies=patient.get("allergies", []) if patient else []
    )
    emergency_data = emergency_service.evaluate_emergency(symptoms)

    # Top Welcome Bar
    st.markdown(f"""
        <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-left: 5px solid #2563EB; border-radius: 16px; padding: 1.6rem 2rem; margin-bottom: 1.85rem; box-shadow: 0 4px 16px -2px rgba(0,0,0,0.04); display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 16px;">
            <div>
                <div style="font-size: 0.74rem; font-weight: 800; color: #2563EB; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.25rem;">
                    PERSONALIZED CLINICAL DASHBOARD
                </div>
                <h2 style="font-size: 2rem; font-weight: 800; color: #0F172A; margin: 0; letter-spacing: -0.025em;">
                    Welcome back, {user_name}
                </h2>
                <div style="color: #64748B; font-size: 0.95rem; margin-top: 0.35rem; font-weight: 500;">
                    Active Patient Record: <strong style="color: #0F172A;">{patient['name'] if patient else 'No profile created yet'}</strong>
                </div>
            </div>
            <div style="display: flex; gap: 10px; align-items: center;">
                <span style="background: #ECFDF5; color: #047857; font-weight: 800; font-size: 0.8rem; padding: 0.45rem 1rem; border-radius: 9999px; border: 1px solid #A7F3D0; display: inline-flex; align-items: center; gap: 6px;">
                    <span class="pulse-dot"></span> Session Active
                </span>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Emergency Alert Banner if acute symptoms exist
    if emergency_data["is_emergency"]:
        render_emergency_alert(emergency_data["flagged_symptoms"])

    # -------------------------------------------------------------------------
    # 1. WORKFLOW PROGRESS CHECKLIST
    # -------------------------------------------------------------------------
    st.markdown("### 📋 Your Safety Journey & Progress")
    st.caption("Follow these 4 sequential steps to evaluate medication safety and receive decision support.")

    c1, c2, c3, c4 = st.columns(4)

    # Step 1 Card: Patient Information
    with c1:
        status_bg = "#ECFDF5" if has_patient_profile else "#FEF3C7"
        status_color = "#047857" if has_patient_profile else "#B45309"
        status_txt = "PROFILE COMPLETE ✓" if has_patient_profile else "PROFILE PENDING"
        st.markdown(f"""
            <div class="clean-card" style="height: 100%; border-top: 4px solid #2563EB;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.4rem;">
                    <span style="font-size: 0.72rem; font-weight: 800; color: #64748B; text-transform: uppercase;">STEP 1</span>
                    <span style="font-size: 1.4rem;">👤</span>
                </div>
                <div style="font-weight: 800; font-size: 1.1rem; color: #0F172A; margin: 0.25rem 0 0.4rem 0;">Patient Information</div>
                <div style="font-size: 0.82rem; color: #64748B; margin-bottom: 0.85rem; line-height: 1.45;">Demographics, conditions, active medications & food.</div>
                <div style="background: {status_bg}; color: {status_color}; font-size: 0.75rem; font-weight: 800; padding: 3px 8px; border-radius: 9999px; display: inline-block; margin-bottom: 0.85rem;">
                    {status_txt}
                </div>
            </div>
        """, unsafe_allow_html=True)
        if st.button("Edit Patient Data →", key="dash_btn_step1", use_container_width=True):
            st.session_state.current_page = "patient_info"
            st.rerun()

    # Step 2 Card: Risk Prediction
    with c2:
        status_bg = "#ECFDF5" if has_prediction else "#F1F5F9"
        status_color = "#047857" if has_prediction else "#64748B"
        status_txt = "PREDICTION COMPLETE ✓" if has_prediction else "NOT COMPLETED"
        st.markdown(f"""
            <div class="clean-card" style="height: 100%; border-top: 4px solid #4F46E5;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.4rem;">
                    <span style="font-size: 0.72rem; font-weight: 800; color: #64748B; text-transform: uppercase;">STEP 2</span>
                    <span style="font-size: 1.4rem;">⚡</span>
                </div>
                <div style="font-weight: 800; font-size: 1.1rem; color: #0F172A; margin: 0.25rem 0 0.4rem 0;">Run Risk Prediction</div>
                <div style="font-size: 0.82rem; color: #64748B; margin-bottom: 0.85rem; line-height: 1.45;">Real Machine Learning risk classification model.</div>
                <div style="background: {status_bg}; color: {status_color}; font-size: 0.75rem; font-weight: 800; padding: 3px 8px; border-radius: 9999px; display: inline-block; margin-bottom: 0.85rem;">
                    {status_txt}
                </div>
            </div>
        """, unsafe_allow_html=True)
        btn_type = "primary" if (has_patient_profile and not has_prediction) else "secondary"
        if st.button("Predict Risk Now →", key="dash_btn_step2", type=btn_type, use_container_width=True):
            st.session_state.current_page = "risk_prediction"
            st.rerun()

    # Step 3 Card: AI Analysis
    with c3:
        st.markdown(f"""
            <div class="clean-card" style="height: 100%; border-top: 4px solid #0D9488;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.4rem;">
                    <span style="font-size: 0.72rem; font-weight: 800; color: #64748B; text-transform: uppercase;">STEP 3</span>
                    <span style="font-size: 1.4rem;">🤖</span>
                </div>
                <div style="font-weight: 800; font-size: 1.1rem; color: #0F172A; margin: 0.25rem 0 0.4rem 0;">Ask AI for Analysis</div>
                <div style="font-size: 0.82rem; color: #64748B; margin-bottom: 0.85rem; line-height: 1.45;">Ask text questions or scan prescription images.</div>
                <div style="background: #EFF6FF; color: #1D4ED8; font-size: 0.75rem; font-weight: 800; padding: 3px 8px; border-radius: 9999px; display: inline-block; margin-bottom: 0.85rem;">
                    AI ANALYSIS READY
                </div>
            </div>
        """, unsafe_allow_html=True)
        if st.button("Open AI Analysis →", key="dash_btn_step3", use_container_width=True):
            st.session_state.current_page = "ai_analysis"
            st.rerun()

    # Step 4 Card: Nearby Hospitals
    with c4:
        st.markdown(f"""
            <div class="clean-card" style="height: 100%; border-top: 4px solid #10B981;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.4rem;">
                    <span style="font-size: 0.72rem; font-weight: 800; color: #64748B; text-transform: uppercase;">STEP 4</span>
                    <span style="font-size: 1.4rem;">🏥</span>
                </div>
                <div style="font-weight: 800; font-size: 1.1rem; color: #0F172A; margin: 0.25rem 0 0.4rem 0;">Find Nearby Hospitals</div>
                <div style="font-size: 0.82rem; color: #64748B; margin-bottom: 0.85rem; line-height: 1.45;">Geospatial interactive map & emergency centers.</div>
                <div style="background: #ECFDF5; color: #047857; font-size: 0.75rem; font-weight: 800; padding: 3px 8px; border-radius: 9999px; display: inline-block; margin-bottom: 0.85rem;">
                    HOSPITALS READY
                </div>
            </div>
        """, unsafe_allow_html=True)
        if st.button("Locate Hospitals →", key="dash_btn_step4", use_container_width=True):
            st.session_state.current_page = "nearby_hospitals"
            st.rerun()

    st.markdown("<div style='margin-top: 2rem;'></div>", unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # 2. METRIC OVERVIEW ROW
    # -------------------------------------------------------------------------
    current_risk_level = latest_assessment["risk_level"] if latest_assessment else "PENDING EVAL"
    emergency_status_str = "ACTIVE ALERT" if emergency_data["is_emergency"] else "NO ACTIVE ALERT"

    render_metrics_row(
        num_medicines=len(medications),
        num_interactions=len(interaction_data["drug_drug"]) + len(interaction_data["contraindications"]),
        num_food_alerts=len(interaction_data["drug_food"]),
        risk_level=current_risk_level,
        emergency_status=emergency_status_str
    )

    st.markdown("<div style='margin-top: 1.75rem;'></div>", unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # 3. CLINICAL SUMMARY & SPEEDOMETER GAUGE
    # -------------------------------------------------------------------------
    col_left, col_right = st.columns([1.2, 1.8], gap="medium")

    with col_left:
        st.markdown("#### 🎯 Clinical Safety Score")
        if latest_assessment:
            render_risk_gauge(
                score=float(latest_assessment["risk_score"]),
                risk_level=latest_assessment["risk_level"],
                confidence=float(latest_assessment["model_confidence"]),
                suffix="%"
            )
            st.caption(f"Last assessed: {latest_assessment['created_at']}")
        else:
            st.markdown("""
                <div class="clean-card" style="text-align: center; padding: 2.5rem 1rem;">
                    <div style="font-size: 2rem; margin-bottom: 0.5rem;">⚡</div>
                    <div style="font-weight: 700; color: #0F172A; margin-bottom: 0.35rem;">No Assessment Run Yet</div>
                    <div style="font-size: 0.85rem; color: #64748B; margin-bottom: 1rem;">Run your first risk prediction to generate your clinical safety score.</div>
                </div>
            """, unsafe_allow_html=True)
            if st.button("Run First Prediction →", type="primary", use_container_width=True):
                st.session_state.current_page = "risk_prediction"
                st.rerun()

    with col_right:
        st.markdown("#### 💊 Active Regimen Overview")
        if not medications:
            st.info("No medications logged yet. Click 'Edit Patient Data' above to add your prescriptions.")
        else:
            for med in medications[:4]:
                st.markdown(f"""
                    <div style="background: white; border: 1px solid #E2E8F0; border-radius: 10px; padding: 0.85rem 1.15rem; margin-bottom: 0.5rem; display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <strong style="color: #0F172A; font-size: 0.95rem;">{med['medicine_name']}</strong>
                            <span style="color: #2563EB; font-size: 0.8rem; font-weight: 600; margin-left: 6px;">({med['strength']})</span>
                            <div style="font-size: 0.78rem; color: #64748B;">Dosage: {med['actual_dosage']} • {med['frequency']}</div>
                        </div>
                        <span style="font-size: 0.75rem; background: #F8FAFC; border: 1px solid #E2E8F0; padding: 3px 8px; border-radius: 6px; color: #334155;">
                            {med.get('relationship', 'Prescribed')}
                        </span>
                    </div>
                """, unsafe_allow_html=True)

            if len(medications) > 4:
                st.caption(f"+ {len(medications) - 4} more medicines in regimen.")
