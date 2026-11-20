"""
DoseWeave - Machine Learning Risk Prediction Page (Step 2 of 4)
Automatically loads saved patient data from SQLite and performs real-time
clinical risk analysis using the trained machine learning pipeline.
Features compact data summary cards, centered trigger button, verified ML results,
dynamic Explainable AI factor attribution, and collapsed detail accordions.
"""

import streamlit as st
from database.database import (
    get_patient_by_user, get_patient_medications, get_patient_foods,
    get_patient_symptoms, save_risk_assessment, get_patient_bundle,
    get_assessment_history
)
from services.interaction_service import interaction_service
from services.recommendation_service import recommendation_service
from services.emergency_service import emergency_service
from models.predict import risk_predictor
from components.header import render_header
from components.risk_gauge import render_risk_gauge
from components.emergency_alert import render_emergency_alert

def render_risk_prediction():
    user_id = st.session_state.get("user_id", 1)
    
    # Fast reliable bundle retrieval ensuring all lists are non-None
    bundle = st.session_state.get("patient_bundle")
    if (
        not bundle 
        or not bundle.get("patient") 
        or bundle.get("patient", {}).get("user_id") != user_id
        or st.session_state.get("patient_dirty", False)
    ):
        bundle = get_patient_bundle(user_id)
        st.session_state.patient_bundle = bundle
        st.session_state.patient_dirty = False

    patient = bundle.get("patient")
    st.session_state.current_patient = patient

    # 1. Page Header & Workflow Status
    render_header(
        title="ANALYSE THE RISK",
        subtitle="Step 2 of 4: Use the trained machine learning model to analyse medication-related risk",
        breadcrumb="DoseWeave > Process",
        active_step=2
    )

    if not patient:
        st.warning("⚠️ No patient profile found. Please complete Step 1 (Patient Information) first.")
        if st.button("← Go to Patient Information", type="primary"):
            st.session_state.current_page = "patient_info"
            st.session_state.process_step = 1
            st.rerun()
        return

    patient_id = patient["id"]
    medications = [m for m in (bundle.get("medications") or []) if m]
    foods = [f for f in (bundle.get("foods") or []) if f]
    symptoms = [s for s in (bundle.get("symptoms") or []) if s]

    # 2. Compact Automatically Retrieved Patient Data Summary
    st.markdown("### 📋 Automatically Retrieved Patient Data")
    st.caption("Loaded directly from your encrypted SQLite database record.")

    sc1, sc2, sc3, sc4 = st.columns(4)

    # Card 1: Patient
    with sc1:
        st.markdown(f"""
            <div class="clean-card" style="padding: 1.1rem !important; min-height: 110px;">
                <div style="font-size: 0.72rem; font-weight: 800; color: #64748B; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.25rem;">PATIENT</div>
                <div style="font-size: 1.05rem; font-weight: 700; color: #0F172A; line-height: 1.3;">{patient['name']}</div>
                <div style="font-size: 0.8rem; color: #64748B; margin-top: 0.25rem;">{patient['age']}y • {patient['gender']} • {patient.get('blood_group') or 'N/A'}</div>
            </div>
        """, unsafe_allow_html=True)

    # Card 2: Medications (Empty-state aware)
    with sc2:
        if len(medications) == 0:
            med_count_display = "0 Medications"
            med_detail_display = "No medications added"
            med_detail_color = "#94A3B8"
        else:
            med_count_display = f"{len(medications)} Active {'Medication' if len(medications) == 1 else 'Medications'}"
            med_names = [m.get("medicine_name", "") for m in medications[:2]]
            med_detail_display = ", ".join(med_names) + ("..." if len(medications) > 2 else "")
            med_detail_color = "#475569"

        st.markdown(f"""
            <div class="clean-card" style="padding: 1.1rem !important; min-height: 110px;">
                <div style="font-size: 0.72rem; font-weight: 800; color: #64748B; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.25rem;">MEDICATIONS</div>
                <div style="font-size: 1.05rem; font-weight: 700; color: #0F172A; line-height: 1.3;">{med_count_display}</div>
                <div style="font-size: 0.8rem; color: {med_detail_color}; margin-top: 0.25rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{med_detail_display}</div>
            </div>
        """, unsafe_allow_html=True)

    # Card 3: Food & Diet (Empty-state aware)
    with sc3:
        if len(foods) == 0:
            food_count_display = "0 Food Entries"
            food_detail_display = "No food information available"
            food_detail_color = "#94A3B8"
        else:
            food_count_display = f"{len(foods)} Logged {'Item' if len(foods) == 1 else 'Items'}"
            food_names = [f.get("food_name", "") for f in foods[:2]]
            food_detail_display = ", ".join(food_names) + ("..." if len(foods) > 2 else "")
            food_detail_color = "#475569"

        st.markdown(f"""
            <div class="clean-card" style="padding: 1.1rem !important; min-height: 110px;">
                <div style="font-size: 0.72rem; font-weight: 800; color: #64748B; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.25rem;">FOOD & DIET</div>
                <div style="font-size: 1.05rem; font-weight: 700; color: #0F172A; line-height: 1.3;">{food_count_display}</div>
                <div style="font-size: 0.8rem; color: {food_detail_color}; margin-top: 0.25rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{food_detail_display}</div>
            </div>
        """, unsafe_allow_html=True)

    # Card 4: Symptoms (Empty-state aware)
    with sc4:
        if len(symptoms) == 0:
            sym_count_display = "0 Symptoms"
            sym_detail_display = "No symptoms reported"
            sym_detail_color = "#94A3B8"
        else:
            sym_count_display = f"{len(symptoms)} Reported {'Symptom' if len(symptoms) == 1 else 'Symptoms'}"
            sym_names = [s.get("symptom_name", "") for s in symptoms[:2]]
            sym_detail_display = ", ".join(sym_names) + ("..." if len(symptoms) > 2 else "")
            sym_detail_color = "#475569"

        st.markdown(f"""
            <div class="clean-card" style="padding: 1.1rem !important; min-height: 110px;">
                <div style="font-size: 0.72rem; font-weight: 800; color: #64748B; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.25rem;">SYMPTOMS</div>
                <div style="font-size: 1.05rem; font-weight: 700; color: #0F172A; line-height: 1.3;">{sym_count_display}</div>
                <div style="font-size: 0.8rem; color: {sym_detail_color}; margin-top: 0.25rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{sym_detail_display}</div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='margin-top: 1.75rem;'></div>", unsafe_allow_html=True)

    # 3. Trigger Actions: Run ML Analysis OR Proceed to Recommendations Directly
    b_col1, b_col2, b_col3 = st.columns([1, 1.8, 1])
    with b_col2:
        btn_c1, btn_c2 = st.columns([1.25, 1])
        with btn_c1:
            run_pred_btn = st.button("⚡ ANALYSE MY RISK", key="run_ml_btn", type="primary", use_container_width=True)
        with btn_c2:
            if st.button("AI REMINDERS →", key="skip_to_recs_btn", type="secondary", use_container_width=True):
                st.session_state.process_step = 3
                st.session_state.current_page = "process"
                st.rerun()

        st.markdown(
            "<div style='text-align: center; font-size: 0.82rem; color: #64748B; margin-top: 0.45rem; line-height: 1.35;'>"
            "Analyse with the trained machine learning model, or proceed directly to AI Reminder System."
            "</div>",
            unsafe_allow_html=True
        )

    # 4. Results Gating: Execute Prediction ONLY on Button Click or Preserve Active Session
    if run_pred_btn:
        interaction_data = interaction_service.analyze_all(
            medications=medications,
            foods=foods,
            conditions=patient.get("conditions", []),
            allergies=patient.get("allergies", [])
        )
        emergency_data = emergency_service.evaluate_emergency(symptoms)

        with st.spinner("Analyzing patient pharmacological markers and calculating model probabilities..."):
            pred = risk_predictor.predict_risk(
                patient=patient,
                medications=medications,
                foods=foods,
                symptoms=symptoms,
                interaction_data=interaction_data
            )
            recs = recommendation_service.generate_recommendations(
                risk_level=pred["risk_level"],
                risk_score=pred["risk_score"],
                patient=patient,
                medications=medications,
                foods=foods,
                symptoms=symptoms,
                interaction_data=interaction_data,
                is_emergency=pred["is_emergency"]
            )
            st.session_state.last_prediction = pred
            st.session_state.last_recommendations = recs
            st.session_state.last_interaction_data = interaction_data
            st.session_state.risk_analyzed = True

            # Save risk assessment record into SQLite database
            all_alerts = interaction_data.get("drug_drug", []) + interaction_data.get("drug_food", [])
            save_risk_assessment(
                patient_id=patient_id,
                risk_level=pred["risk_level"],
                risk_score=pred["risk_score"],
                model_confidence=pred["model_confidence"],
                top_factors=pred["top_contributing_factors"],
                raw_features=pred["raw_features"],
                emergency_flag=1 if pred["is_emergency"] else 0,
                interactions=all_alerts,
                recommendations=recs
            )
            st.session_state.assessment_dirty = True
            if "patient_bundle" in st.session_state and st.session_state["patient_bundle"]:
                st.session_state["patient_bundle"]["history"] = get_assessment_history(patient_id) or []

    # If the user has not analyzed yet in this session, provide a helpful prompt and direct link to Step 3
    if not st.session_state.get("risk_analyzed", False) or "last_prediction" not in st.session_state:
        st.markdown("""
            <div style="background: #F8FAFC; border: 1px dashed #CBD5E1; border-radius: 12px; padding: 1.5rem; text-align: center; margin-top: 1.5rem;">
                <div style="font-size: 1rem; font-weight: 700; color: #334155; margin-bottom: 0.35rem;">
                    Ready for Clinical Decision Support
                </div>
                <div style="font-size: 0.86rem; color: #64748B; max-width: 540px; margin: 0 auto 1.25rem auto; line-height: 1.5;">
                    Click <strong>'⚡ ANALYSE MY RISK'</strong> above to calculate ML probabilities, or continue directly to the AI Recommendation System.
                </div>
            </div>
        """, unsafe_allow_html=True)
        st.markdown("<div style='margin-top: 1rem;'></div>", unsafe_allow_html=True)
        c_nav1, c_nav2, c_nav3 = st.columns([1, 1.8, 1])
        with c_nav2:
            if st.button("CONTINUE TO AI REMINDER SYSTEM →", key="unassessed_continue_btn", type="primary", use_container_width=True):
                st.session_state.process_step = 3
                st.session_state.current_page = "process"
                st.rerun()
        return

    pred = st.session_state.get("last_prediction")

    # 5. Analysis Complete Banner
    st.markdown("""
        <div style="background: #ECFDF5; border: 1px solid #A7F3D0; border-radius: 12px; padding: 0.85rem 1.25rem; margin: 1.75rem 0 1.25rem 0; display: flex; align-items: center; justify-content: center; gap: 8px;">
            <span style="color: #059669; font-weight: 800; font-size: 1.02rem;">✓ ANALYSIS COMPLETE</span>
            <span style="color: #065F46; font-size: 0.85rem;">— Machine learning inference finished successfully using trained risk model</span>
        </div>
    """, unsafe_allow_html=True)

    # Emergency safety check
    if pred.get("is_emergency"):
        render_emergency_alert(pred.get("emergency_symptoms", []))

    # 6. Clinical Safety Score & Model Inference Results
    st.markdown("""
        <div style="margin-top: 1.5rem; margin-bottom: 0.85rem;">
            <h3 style="margin: 0; font-size: 1.4rem; font-weight: 800; color: #0F2C59; display: flex; align-items: center; gap: 0.5rem;">
                🎯 Clinical Safety Score
            </h3>
        </div>
    """, unsafe_allow_html=True)

    # Main Clinical Safety Score Card with Speedometer Gauge
    st.markdown("""
        <div class="clean-card" style="padding: 1.25rem 1.5rem 0.75rem 1.5rem !important; margin-bottom: 1.25rem;">
    """, unsafe_allow_html=True)

    render_risk_gauge(
        score=pred["risk_score"],
        risk_level=pred["risk_level"],
        confidence=pred["model_confidence"],
        suffix="%"
    )

    st.markdown("</div>", unsafe_allow_html=True)

    # Three Clear Model Output Summary Indicator Cards
    col_res1, col_res2, col_res3 = st.columns(3)

    with col_res1:
        r_level = pred["risk_level"]
        badge_type = "badge-high" if "HIGH" in r_level else ("badge-moderate" if "MODERATE" in r_level else "badge-low")
        st.markdown(f"""
            <div class="clean-card" style="text-align: center; padding: 1.25rem 1rem !important;">
                <div style="font-size: 0.76rem; font-weight: 800; color: #64748B; text-transform: uppercase; letter-spacing: 0.06em;">PREDICTED RISK LEVEL</div>
                <div style="margin: 0.7rem 0;">
                    <span class="{badge_type}" style="font-size: 1.12rem; padding: 0.45rem 1.35rem; border-radius: 9999px;">{r_level}</span>
                </div>
                <div style="font-size: 0.8rem; color: #64748B;">Classification via Trained ML Pipeline</div>
            </div>
        """, unsafe_allow_html=True)

    with col_res2:
        st.markdown(f"""
            <div class="clean-card" style="text-align: center; padding: 1.25rem 1rem !important;">
                <div style="font-size: 0.76rem; font-weight: 800; color: #64748B; text-transform: uppercase; letter-spacing: 0.06em;">PREDICTION CONFIDENCE</div>
                <div style="font-size: 2.25rem; font-weight: 800; color: #2563EB; margin: 0.3rem 0;">{pred['model_confidence']}%</div>
                <div style="font-size: 0.8rem; color: #64748B;">Confidence in predicted classification</div>
            </div>
        """, unsafe_allow_html=True)

    with col_res3:
        st.markdown(f"""
            <div class="clean-card" style="text-align: center; padding: 1.25rem 1rem !important;">
                <div style="font-size: 0.76rem; font-weight: 800; color: #64748B; text-transform: uppercase; letter-spacing: 0.06em;">ESTIMATED RISK SCORE</div>
                <div style="font-size: 2.25rem; font-weight: 800; color: #0F172A; margin: 0.3rem 0;">{pred['risk_score']}%</div>
                <div style="font-size: 0.8rem; color: #64748B;">Overall calculated clinical risk burden</div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='margin-top: 1rem;'></div>", unsafe_allow_html=True)

    # 7. What Does This Result Mean? Section
    st.markdown("### 💡 WHAT DOES THIS RESULT MEAN?")

    # Dynamic explanation based on real prediction and actual patient parameters
    risk_lvl = pred["risk_level"]
    score_val = pred["risk_score"]
    med_cnt = len(medications)
    sym_cnt = len(symptoms)

    if "HIGH" in risk_lvl:
        explanation_body = (
            f"Based on the available patient profile ({patient['age']}y, {med_cnt} active medication{'s' if med_cnt != 1 else ''}, "
            f"{sym_cnt} reported symptom{'s' if sym_cnt != 1 else ''}), the trained machine learning model classified the current case as "
            f"<strong>High Risk</strong> ({score_val}%). Elevated clinical indicators or significant pharmacological interactions "
            f"were identified in the evaluated record. Immediate clinical consultation with a healthcare provider is strongly advised."
        )
        box_border = "#FCA5A5"
        box_bg = "#FEF2F2"
    elif "MODERATE" in risk_lvl:
        explanation_body = (
            f"Based on the available patient profile ({patient['age']}y, {med_cnt} active medication{'s' if med_cnt != 1 else ''}, "
            f"{sym_cnt} reported symptom{'s' if sym_cnt != 1 else ''}), the trained machine learning model classified the current case as "
            f"<strong>Moderate Risk</strong> ({score_val}%). Moderate risk indicators such as medication interactions, dosage parameters, "
            f"or underlying conditions warrant targeted observation and scheduled review with a licensed healthcare professional."
        )
        box_border = "#FDE68A"
        box_bg = "#FFFBEB"
    else:
        explanation_body = (
            f"Based on the available patient information ({patient['age']}y, {med_cnt} active medication{'s' if med_cnt != 1 else ''}, "
            f"{sym_cnt} reported symptom{'s' if sym_cnt != 1 else ''}), the trained machine learning model classified the current case as "
            f"<strong>Low Risk</strong> ({score_val}%). This result reflects the information currently available in the system, "
            f"with minimal detected pharmacological conflicts or severe risk factors."
        )
        box_border = "#BFDBFE"
        box_bg = "#EFF6FF"

    st.markdown(f"""
        <div style="background: {box_bg}; border: 1px solid {box_border}; border-radius: 12px; padding: 1.15rem 1.4rem; margin-bottom: 1.5rem;">
            <div style="font-size: 0.92rem; color: #1E293B; line-height: 1.55; margin-bottom: 0.65rem;">
                {explanation_body}
            </div>
            <div style="font-size: 0.78rem; color: #64748B; font-weight: 500; border-top: 1px dashed #CBD5E1; padding-top: 0.5rem;">
                ⚠️ <em>This system is intended for decision-support and educational purposes and does not replace professional medical advice.</em>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # 8. Collapsible Detailed Analysis Sections (Collapsed Initially to Reduce Page Length)
    st.markdown("### 🔬 Detailed Clinical Analysis")
    st.caption("Expand the sections below to review in-depth model visualizations, probability distributions, and Explainable AI factors.")

    # Accordion 1: Risk Class Probabilities
    with st.expander("▶ RISK CLASS PROBABILITIES", expanded=False):
        st.markdown("""
            <div style="font-size: 0.85rem; color: #64748B; margin-bottom: 0.75rem;">
                Actual calibrated probability distribution across clinical risk classes generated directly via <code>model.predict_proba()</code>.
            </div>
        """, unsafe_allow_html=True)

        probs = pred.get("probabilities", {})
        prob_classes = [
            ("LOW RISK", probs.get("LOW RISK", 0.0), "#10B981"),
            ("MODERATE RISK", probs.get("MODERATE RISK", 0.0), "#F59E0B"),
            ("HIGH RISK", probs.get("HIGH RISK", 0.0), "#EF4444")
        ]

        p_c1, p_c2, p_c3 = st.columns(3)
        for idx, (cls_name, prob_val, color) in enumerate(prob_classes):
            col_target = [p_c1, p_c2, p_c3][idx]
            pct = round(float(prob_val) * 100.0, 1)
            with col_target:
                st.markdown(f"""
                    <div style="background: white; border: 1px solid #E2E8F0; border-top: 4px solid {color}; border-radius: 10px; padding: 0.9rem; text-align: center;">
                        <div style="font-size: 0.76rem; font-weight: 700; color: #64748B;">{cls_name}</div>
                        <div style="font-size: 1.6rem; font-weight: 800; color: #0F172A; margin: 0.3rem 0;">{pct}%</div>
                    </div>
                """, unsafe_allow_html=True)
                st.progress(float(min(1.0, max(0.0, prob_val))))

    # Accordion 3: Top Contributing Risk Factors (Explainable AI)
    with st.expander("▶ TOP CONTRIBUTING RISK FACTORS", expanded=False):
        st.markdown("""
            <div style="font-size: 0.85rem; color: #64748B; margin-bottom: 0.85rem;">
                Explainable AI feature attribution derived dynamically from actual patient data, active medications, symptoms, and trained model weights.
            </div>
        """, unsafe_allow_html=True)

        raw_factors = pred.get("top_contributing_factors", [])

        # Normalize factors to structured dicts
        structured_factors = []
        for f in raw_factors:
            if isinstance(f, dict):
                structured_factors.append(f)
            elif isinstance(f, str):
                structured_factors.append({
                    "factor": f,
                    "impact": "High" if "High" in f or "Critical" in f else ("Moderate" if "Moderate" in f else "Low"),
                    "description": f
                })

        # Separate significant elevated factors (Moderate / High) from baseline
        significant_factors = [
            f for f in structured_factors
            if f.get("impact") in ["High", "Moderate"]
        ]

        if not significant_factors:
            st.markdown("""
                <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 10px; padding: 1.25rem; text-align: center; color: #475569; margin-bottom: 1rem;">
                    <div style="font-size: 1.25rem; margin-bottom: 0.35rem;">🛡️</div>
                    <div style="font-weight: 700; font-size: 0.98rem; color: #1E293B;">
                        No major risk factors were identified from the available patient information.
                    </div>
                    <div style="font-size: 0.82rem; color: #64748B; margin-top: 0.35rem;">
                        Current inputs indicate absence of acute clinical symptoms, severe drug-drug interactions, or high-risk polypharmacy.
                    </div>
                </div>
            """, unsafe_allow_html=True)

        # Render each factor dynamically with factor name, impact badge, and short explanation
        for item in structured_factors:
            factor_name = item.get("factor", "Clinical Risk Indicator")
            impact = item.get("impact", "Low")
            desc = item.get("description", "")

            if impact == "High":
                badge_class = "badge-high"
                border_color = "#EF4444"
            elif impact == "Moderate":
                badge_class = "badge-moderate"
                border_color = "#F59E0B"
            else:
                badge_class = "badge-low"
                border_color = "#10B981"

            st.markdown(f"""
                <div style="background: white; border: 1px solid #E2E8F0; border-left: 4px solid {border_color}; border-radius: 10px; padding: 0.95rem 1.25rem; margin-bottom: 0.65rem; box-shadow: 0 1px 3px rgba(0,0,0,0.03);">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.35rem; flex-wrap: wrap; gap: 8px;">
                        <span style="font-weight: 700; font-size: 0.96rem; color: #0F172A;">{factor_name}</span>
                        <span class="{badge_class}" style="font-size: 0.76rem; font-weight: 700; padding: 0.2rem 0.65rem;">Impact: {impact}</span>
                    </div>
                    <div style="font-size: 0.86rem; color: #475569; line-height: 1.45;">
                        {desc}
                    </div>
                </div>
            """, unsafe_allow_html=True)

    # 9. Next Step Action Call Button
    st.markdown("<div style='margin-top: 2.25rem;'></div>", unsafe_allow_html=True)
    c_col1, c_col2, c_col3 = st.columns([1, 1.8, 1])
    with c_col2:
        if st.button("CONTINUE TO AI REMINDER SYSTEM →", key="pred_to_ai_btn", type="primary", use_container_width=True):
            st.session_state.process_step = 3
            st.session_state.current_page = "process"
            st.rerun()

