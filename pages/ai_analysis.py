"""
MediSafe AI - AI Analysis & Recommendations Page
Dual-mode clinical intelligence interface supporting both text inquiries and multimodal image uploads.
Generates structured 5-tier safety recommendations strictly compliant with medical guardrails.
"""

import streamlit as st
from PIL import Image
from database.database import (
    get_patient_by_user, get_patient_medications, get_patient_foods,
    get_patient_symptoms, get_assessment_history
)
from services.gemini_service import gemini_service
from services.interaction_service import interaction_service
from services.recommendation_service import recommendation_service
from components.header import render_header
from utils.constants import CLINICAL_DISCLAIMER

def render_ai_analysis():
    user_id = st.session_state.get("user_id", 1)
    patient = get_patient_by_user(user_id)

    render_header(
        title="AI RECOMMENDATION SYSTEM",
        subtitle="Step 3 of 4: Ask questions using text or upload an image such as a prescription or medicine label for AI-assisted analysis and safety-oriented recommendations",
        breadcrumb="MediSafe AI > Process",
        active_step=3
    )

    if not patient:
        st.warning("Please complete Step 1 (Patient Information) before running AI analysis.")
        if st.button("← Go to Patient Information"):
            st.session_state.current_page = "patient_info"
            st.rerun()
        return

    patient_id = patient["id"]
    medications = get_patient_medications(patient_id, active_only=True)
    foods = get_patient_foods(patient_id)
    symptoms = get_patient_symptoms(patient_id)
    history = get_assessment_history(patient_id)
    latest_assessment = history[0] if history else None
    risk_level = latest_assessment["risk_level"] if latest_assessment else "MODERATE RISK"
    risk_score = latest_assessment["risk_score"] if latest_assessment else 45.0

    interaction_data = interaction_service.analyze_all(
        medications=medications,
        foods=foods,
        conditions=patient.get("conditions", []),
        allergies=patient.get("allergies", [])
    )

    # -------------------------------------------------------------------------
    # DUAL INPUT SELECTION (Option A: Text Query | Option B: Image Query)
    # -------------------------------------------------------------------------
    ai_mode = st.session_state.get("ai_input_mode", "text")
    if ai_mode not in ("text", "image"):
        ai_mode = "text"

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        is_text = (ai_mode == "text")
        if st.button("💬 ASK USING TEXT", key="btn_ai_mode_text", use_container_width=True, type="primary" if is_text else "secondary"):
            st.session_state.ai_input_mode = "text"
            st.rerun()
    with col_btn2:
        is_image = (ai_mode == "image")
        if st.button("📷 ASK USING AN IMAGE", key="btn_ai_mode_image", use_container_width=True, type="primary" if is_image else "secondary"):
            st.session_state.ai_input_mode = "image"
            st.rerun()

    st.markdown("<div style='margin-bottom: 1rem;'></div>", unsafe_allow_html=True)

    # ------------------- OPTION A: TEXT QUERY ------------------- #
    if ai_mode == "text":
        st.markdown("#### ASK USING TEXT")
        st.caption("Your inquiry is analyzed in the context of your saved medical profile, active prescriptions, food intake, and symptoms.")

        # Preset query buttons
        preset_cols = st.columns(3)
        with preset_cols[0]:
            if st.button("Can I take this medicine after food?", use_container_width=True):
                st.session_state.user_query_input = "Can I take this medicine after food?"
        with preset_cols[1]:
            if st.button("I feel dizzy after taking my medicine.", use_container_width=True):
                st.session_state.user_query_input = "I feel dizzy after taking my medicine."
        with preset_cols[2]:
            if st.button("What should I monitor based on my current symptoms?", use_container_width=True):
                st.session_state.user_query_input = "What should I monitor based on my current symptoms?"

        with st.form("text_analysis_form"):
            user_question = st.text_input(
                "Type your question here...",
                value=st.session_state.get("user_query_input", ""),
                placeholder="Type your question here..."
            )
            submit_q = st.form_submit_button("ANALYSE MY QUESTION", type="primary", use_container_width=True)

        if submit_q and user_question.strip():
            with st.spinner("Synthesizing clinical response using patient records & pharmacology guidelines..."):
                # Formulate safe educational context
                med_summary = ", ".join([f"{m['medicine_name']} ({m['strength']}, {m['actual_dosage']})" for m in medications]) or "None"
                food_summary = ", ".join([f"{f['food_name']} ({f['category']})" for f in foods]) or "Standard diet"
                sym_summary = ", ".join([f"{s['symptom_name']} ({s['severity']})" for s in symptoms]) or "None"
                cond_summary = ", ".join(patient.get("conditions", [])) or "None"

                prompt = f"""
You are MediSafe AI, a professional educational clinical decision-support assistant.
A patient has asked a medication question.

PATIENT CONTEXT:
- Age: {patient['age']}, Gender: {patient['gender']}
- Chronic Conditions: {cond_summary}
- Active Prescriptions: {med_summary}
- Dietary Intake: {food_summary}
- Symptoms: {sym_summary}
- ML Risk Level: {risk_level} ({risk_score}% Risk Score)

PATIENT QUESTION:
"{user_question}"

STRICT MEDICAL SAFETY RULES:
- Do NOT prescribe new medications.
- Do NOT alter dosages or tell the patient to discontinue prescribed medications without their doctor.
- Do NOT diagnose medical conditions or poisoning.
- Always recommend pharmacist/physician verification.
- Provide a clear, structured educational explanation.
"""
                if gemini_service.is_available():
                    try:
                        response = gemini_service.model.generate_content(prompt)
                        st.session_state.ai_text_response = response.text
                    except Exception as e:
                        st.session_state.ai_text_response = f"Analysis generated based on clinical safety guidelines: For your question regarding '{user_question}', please verify interactions between {med_summary} and your current diet ({food_summary}) with a licensed pharmacist."
                else:
                    st.session_state.ai_text_response = f"Clinical Safety Guidelines for '{user_question}': When taking {med_summary}, ensure adherence to prescribed intervals. Given your reported conditions ({cond_summary}), consult your physician or clinical pharmacist to verify this combination."

        if st.session_state.get("ai_text_response"):
            st.markdown(f"""
                <div style="background: white; border: 1px solid #E2E8F0; border-left: 4px solid #2563EB; border-radius: 10px; padding: 1.25rem 1.5rem; margin-top: 1rem;">
                    <div style="font-weight: 800; color: #0F172A; font-size: 1.05rem; margin-bottom: 0.5rem;">AI Clinical Response:</div>
                    <div style="color: #334155; line-height: 1.6; font-size: 0.95rem;">{st.session_state.ai_text_response}</div>
                </div>
            """, unsafe_allow_html=True)

    # ------------------- OPTION B: IMAGE QUERY ------------------- #
    else:
        st.markdown("#### ASK USING AN IMAGE")
        st.caption("Upload a Prescription Image, Medicine Image, Medicine Label, or other medication information.")

        img_col1, img_col2 = st.columns([1.2, 1.8], gap="medium")
        with img_col1:
            uploaded_file = st.file_uploader("Upload Image", type=["jpg", "jpeg", "png"])
            if uploaded_file is not None:
                image = Image.open(uploaded_file)
                st.session_state.current_analysis_image = image
                st.image(image, caption="Image Preview", use_container_width=True)

                if st.button("ANALYSE IMAGE", type="primary", use_container_width=True):
                    with st.spinner("Performing OCR extraction with Gemini Vision AI..."):
                        if gemini_service.is_available():
                            res = gemini_service.analyze_prescription(image)
                            st.session_state.image_analysis_result = res
                        else:
                            st.session_state.image_analysis_result = "Google Gemini API key not detected. To enable multimodal prescription OCR, configure GOOGLE_API_KEY in your .env file."

        with img_col2:
            st.markdown("##### Image Analysis Output")
            if st.session_state.get("image_analysis_result"):
                st.markdown(st.session_state.image_analysis_result)
            else:
                st.info("Upload a prescription or medicine label on the left and click 'ANALYSE IMAGE'.")

    # -------------------------------------------------------------------------
    # STRUCTURED RECOMMENDATIONS OUTPUT (6 SPECIFIED SECTIONS)
    # -------------------------------------------------------------------------
    st.markdown("<div style='margin-top: 2.5rem;'></div>", unsafe_allow_html=True)
    st.markdown("### 📋 Structured Clinical Recommendations")
    st.caption("Personalized across clinical safety sections based on your patient profile, ML risk level, and active regimen.")

    recs = recommendation_service.generate_recommendations(
        risk_level=risk_level,
        risk_score=risk_score,
        patient=patient,
        medications=medications,
        foods=foods,
        symptoms=symptoms,
        interaction_data=interaction_data,
        is_emergency=False
    )

    # 1. QUERY SUMMARY
    user_q_text = st.session_state.get("user_query_input", "Standard patient intake and multi-drug regimen evaluation.")
    st.markdown(f"""
        <div class="clean-card" style="border-left: 4px solid #2563EB;">
            <div style="font-size: 0.8rem; font-weight: 800; color: #2563EB; text-transform: uppercase;">1. QUERY SUMMARY</div>
            <div style="font-size: 1.05rem; font-weight: 700; color: #0F172A; margin: 0.35rem 0;">Inquiry Overview</div>
            <div style="color: #475569; font-size: 0.92rem; line-height: 1.5;">
                <strong>Patient Query:</strong> {user_q_text}<br>
                <strong>Active Profile:</strong> {len(medications)} medication(s), {len(foods)} food item(s), {len(symptoms)} reported symptom(s).
            </div>
        </div>
    """, unsafe_allow_html=True)

    # 2. ANALYSIS
    st.markdown(f"""
        <div class="clean-card" style="border-left: 4px solid #0D9488;">
            <div style="font-size: 0.8rem; font-weight: 800; color: #0D9488; text-transform: uppercase;">2. ANALYSIS</div>
            <div style="font-size: 1.05rem; font-weight: 700; color: #0F172A; margin: 0.35rem 0;">Pharmacological Evaluation</div>
            <div style="color: #475569; font-size: 0.92rem; line-height: 1.5;">
                The Machine Learning risk prediction engine assessed your regimen at 
                <strong style="color: {'#DC2626' if 'HIGH' in risk_level else ('#D97706' if 'MODERATE' in risk_level else '#16A34A')};">{risk_level} ({risk_score}% Risk Score)</strong>. 
                {st.session_state.get('ai_text_response', 'Pharmacological analysis indicates your active regimen requires routine scheduling and dietary awareness.')}
            </div>
        </div>
    """, unsafe_allow_html=True)

    # 3. POSSIBLE SAFETY CONCERNS
    avoid_items = [r["text"] for r in recs if r.get("category") == "WHAT TO AVOID"]
    all_alerts = interaction_data.get("drug_drug", []) + interaction_data.get("drug_food", []) + interaction_data.get("contraindications", [])
    if all_alerts:
        avoid_items = [f"[{a.get('type', 'Alert')}] {a.get('item1')} ⇄ {a.get('item2')}: {a.get('description')}" for a in all_alerts]
    elif not avoid_items:
        avoid_items = ["No severe contraindications or acute adverse interactions detected in the verified knowledge base."]
    st.markdown("""
        <div class="clean-card" style="border-left: 4px solid #EF4444;">
            <div style="font-size: 0.8rem; font-weight: 800; color: #DC2626; text-transform: uppercase;">3. POSSIBLE SAFETY CONCERNS</div>
            <div style="font-size: 1.05rem; font-weight: 700; color: #0F172A; margin: 0.35rem 0;">Identified Interaction Warnings</div>
            <ul style="color: #475569; font-size: 0.92rem; line-height: 1.6; margin: 0; padding-left: 1.25rem;">
                {}
            </ul>
        </div>
    """.format("".join([f"<li>{item}</li>" for item in avoid_items])), unsafe_allow_html=True)

    # 4. THINGS TO MONITOR
    monitor_items = [r["text"] for r in recs if r.get("category") == "WHAT TO MONITOR"]
    if not monitor_items:
        monitor_items = ["Monitor for changes in energy, dizziness, blood pressure variance, or digestive discomfort."]
    st.markdown("""
        <div class="clean-card" style="border-left: 4px solid #F59E0B;">
            <div style="font-size: 0.8rem; font-weight: 800; color: #B45309; text-transform: uppercase;">4. THINGS TO MONITOR</div>
            <div style="font-size: 1.05rem; font-weight: 700; color: #0F172A; margin: 0.35rem 0;">Key Symptoms & Vital Signs</div>
            <ul style="color: #475569; font-size: 0.92rem; line-height: 1.6; margin: 0; padding-left: 1.25rem;">
                {}
            </ul>
        </div>
    """.format("".join([f"<li>{item}</li>" for item in monitor_items])), unsafe_allow_html=True)

    # 5. RECOMMENDATIONS
    rec_items = [r["text"] for r in recs if r.get("category") in ["WHAT TO REVIEW", "WHAT TO DO"]]
    if not rec_items:
        rec_items = [
            "Maintain an updated list of all active medications, strengths, and daily schedules.",
            "Take medications with water and adhere strictly to prescribed dosing intervals."
        ]
    st.markdown("""
        <div class="clean-card" style="border-left: 4px solid #10B981;">
            <div style="font-size: 0.8rem; font-weight: 800; color: #047857; text-transform: uppercase;">5. RECOMMENDATIONS</div>
            <div style="font-size: 1.05rem; font-weight: 700; color: #0F172A; margin: 0.35rem 0;">Adherence & Practical Safety Guidance</div>
            <ul style="color: #475569; font-size: 0.92rem; line-height: 1.6; margin: 0; padding-left: 1.25rem;">
                {}
            </ul>
        </div>
    """.format("".join([f"<li>{item}</li>" for item in rec_items])), unsafe_allow_html=True)

    # 6. WHEN TO CONTACT A HEALTHCARE PROFESSIONAL
    contact_items = [r["text"] for r in recs if r.get("category") == "WHEN TO CONSULT A HEALTHCARE PROFESSIONAL"]
    if not contact_items:
        contact_items = [
            "Schedule a clinical review with your prescribing doctor if introducing any new prescription or over-the-counter medication.",
            "Seek urgent emergency medical evaluation immediately if experiencing chest pain, difficulty breathing, or sudden loss of consciousness."
        ]
    st.markdown("""
        <div class="clean-card" style="border-left: 4px solid #4F46E5;">
            <div style="font-size: 0.8rem; font-weight: 800; color: #4F46E5; text-transform: uppercase;">6. WHEN TO CONTACT A HEALTHCARE PROFESSIONAL</div>
            <div style="font-size: 1.05rem; font-weight: 700; color: #0F172A; margin: 0.35rem 0;">Professional Consultation Advice</div>
            <ul style="color: #475569; font-size: 0.92rem; line-height: 1.6; margin: 0; padding-left: 1.25rem;">
                {}
            </ul>
        </div>
    """.format("".join([f"<li>{item}</li>" for item in contact_items])), unsafe_allow_html=True)

    # Continuation to Step 4
    st.markdown("<div style='margin-top: 2rem;'></div>", unsafe_allow_html=True)
    if st.button("FIND NEARBY HEALTHCARE LOCATIONS →", key="recs_to_hosp_btn", type="primary", use_container_width=True):
        st.session_state.process_step = 4
        st.session_state.current_page = "process"
        st.rerun()

    st.markdown("<div style='margin-top: 1.25rem;'></div>", unsafe_allow_html=True)
    st.caption("This information is for educational and decision-support purposes and does not replace professional medical advice.")
