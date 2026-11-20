"""
DoseWeave - Patient Information Collection
Unified intake page collecting patient demographics, chronic conditions,
allergies, multi-drug medications, food & beverages, and symptoms.
Stored in SQLite connected to the logged-in user.
"""

import streamlit as st
from database.database import (
    get_patient_by_user, save_complete_patient_data,
    get_patient_medications, get_patient_foods, get_patient_symptoms,
    get_patient_bundle
)
from utils.constants import (
    CHRONIC_CONDITIONS, FOOD_CATEGORIES, SYSTEM_SYMPTOMS
)
from utils.helpers import calculate_bmi
from components.header import render_header

def render_patient_info():
    user_id = st.session_state.get("user_id", 1)
    
    # Fast reliable bundle retrieval ensuring non-None collections
    bundle = st.session_state.get("patient_bundle")
    if not bundle or not bundle.get("patient") or st.session_state.get("patient_dirty", False):
        bundle = get_patient_bundle(user_id)
        st.session_state.patient_bundle = bundle
        st.session_state.patient_dirty = False

    patient = bundle.get("patient")
    st.session_state.current_patient = patient

    existing_meds = bundle.get("medications") or []
    existing_foods = bundle.get("foods") or []
    existing_symptoms = bundle.get("symptoms") or []

    render_header(
        title="COLLECT USER DATA",
        subtitle="Step 1 of 4: Enter and securely store patient information, medication details, food information, allergies and symptoms",
        breadcrumb="DoseWeave > Process",
        active_step=1
    )

    # Maintain medications list in session state for dynamic add/remove
    if "med_list_state" not in st.session_state:
        if patient is not None:
            st.session_state.med_list_state = existing_meds
        else:
            st.session_state.med_list_state = [
                {"medicine_name": "Metformin", "strength": "500 mg", "prescribed_dosage": "500 mg BID", "actual_dosage": "500 mg BID", "frequency": "Twice a day", "time_taken": "Morning", "duration": "Ongoing", "relationship": "Prescribed by Physician"}
            ]

    # Maintain food entries list in session state
    if "food_list_state" not in st.session_state:
        if patient is not None:
            st.session_state.food_list_state = existing_foods
        else:
            st.session_state.food_list_state = [
                {"food_name": "Grapefruit Juice", "category": "Grapefruit & Citrus Juice", "quantity": "1 glass (250ml)", "time_consumed": "Breakfast", "relationship_to_med": "With Medication"}
            ]

    # -------------------------------------------------------------------------
    # 1. PERSONAL INFORMATION
    # -------------------------------------------------------------------------
    st.markdown("### 👤 1. Personal Information")
    with st.container():
        p_c1, p_c2, p_c3 = st.columns(3)
        with p_c1:
            p_name = st.text_input("Patient Full Name *", value=patient["name"] if patient else "Alex Morgan")
            p_age = st.number_input("Age (Years) *", min_value=0, max_value=125, value=int(patient["age"]) if patient else 58)
        with p_c2:
            gender_opts = ["Male", "Female", "Other", "Prefer not to say"]
            g_idx = gender_opts.index(patient["gender"]) if patient and patient["gender"] in gender_opts else 0
            p_gender = st.selectbox("Gender *", options=gender_opts, index=g_idx)
            blood_opts = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-", "Unknown"]
            b_idx = blood_opts.index(patient["blood_group"]) if patient and patient["blood_group"] in blood_opts else 6
            p_blood = st.selectbox("Blood Group", options=blood_opts, index=b_idx)
        with p_c3:
            p_weight = st.number_input("Weight (kg) *", min_value=1.0, max_value=350.0, value=float(patient["weight"]) if patient else 78.5, step=0.5)
            p_height = st.number_input("Height (cm) *", min_value=10.0, max_value=260.0, value=float(patient["height"]) if patient else 175.0, step=0.5)
            bmi, bmi_cat = calculate_bmi(p_weight, p_height)
            st.markdown(f"<div style='font-size: 0.85rem; color: #64748B; margin-top: 0.35rem;'>Calculated BMI: <strong>{bmi or 'N/A'}</strong> ({bmi_cat})</div>", unsafe_allow_html=True)

    st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # 2. MEDICAL HISTORY & ALLERGIES
    # -------------------------------------------------------------------------
    st.markdown("### 🩺 2. Medical History & Chronic Conditions")
    existing_conds = patient.get("conditions", []) if patient else ["Hypertension", "Diabetes Mellitus"]
    selected_conditions = []

    m_cols = st.columns(2)
    for idx, cond in enumerate(CHRONIC_CONDITIONS):
        with m_cols[idx % 2]:
            checked = cond in existing_conds or any(cond.lower() in ec.lower() for ec in existing_conds)
            if st.checkbox(cond, value=checked, key=f"cond_check_{idx}"):
                selected_conditions.append(cond)

    other_conds_txt = st.text_input("Other Medical Conditions (comma-separated)", placeholder="e.g. Thyroid disorder, High cholesterol")
    if other_conds_txt.strip():
        for item in other_conds_txt.split(","):
            if item.strip():
                selected_conditions.append(item.strip())

    st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)

    st.markdown("### ⚠️ 3. Known Allergies & Hypersensitivities")
    existing_allergies = [a.get("allergen_name", "") for a in patient.get("allergies", [])] if patient else ["Penicillin"]
    al_c1, al_c2 = st.columns(2)
    with al_c1:
        med_allergies = st.text_area(
            "Medicine Allergies (e.g. Penicillin, Aspirin, Sulfa drugs)",
            value=", ".join(existing_allergies),
            height=70
        )
    with al_c2:
        food_allergies = st.text_area(
            "Food & Other Allergies (e.g. Peanuts, Shellfish, Dairy)",
            placeholder="e.g. Peanuts, Shellfish, Gluten",
            height=70
        )

    st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # 4. MEDICATION INFORMATION
    # -------------------------------------------------------------------------
    st.markdown(f"### 💊 4. Medication Information ({len(st.session_state.med_list_state)} active)")
    st.caption("Add every prescription or self-medicated drug currently being taken.")

    # Display dynamic medication cards
    for idx, med in enumerate(st.session_state.med_list_state):
        with st.expander(f"Medicine #{idx + 1}: {med.get('medicine_name', 'Unnamed Medicine')} ({med.get('strength', '')})", expanded=True):
            mc1, mc2, mc3 = st.columns(3)
            with mc1:
                med["medicine_name"] = st.text_input("Medicine Name *", value=med.get("medicine_name", ""), key=f"m_name_{idx}")
                med["strength"] = st.text_input("Strength *", value=med.get("strength", "500 mg"), key=f"m_str_{idx}")
                med["relationship"] = st.selectbox("Status", options=["Prescribed by Physician", "Self-Medicated (OTC)", "Unknown"], index=0 if "Prescribed" in med.get("relationship", "") else 1, key=f"m_rel_{idx}")
            with mc2:
                med["prescribed_dosage"] = st.text_input("Prescribed Dosage *", value=med.get("prescribed_dosage", "500 mg once daily"), key=f"m_pdose_{idx}")
                med["actual_dosage"] = st.text_input("Actual Dosage Taken *", value=med.get("actual_dosage", "500 mg once daily"), key=f"m_adose_{idx}")
                med["frequency"] = st.text_input("Frequency *", value=med.get("frequency", "Once a day"), key=f"m_freq_{idx}")
            with mc3:
                med["time_taken"] = st.selectbox("Time Taken", options=["Morning", "Afternoon", "Evening", "Bedtime", "Variable"], key=f"m_time_{idx}")
                med["duration"] = st.text_input("Duration", value=med.get("duration", "Ongoing"), key=f"m_dur_{idx}")
                st.markdown("<div style='margin-top: 1.6rem;'></div>", unsafe_allow_html=True)
                if st.button(f"🗑️ Remove Medicine #{idx + 1}", key=f"del_med_btn_{idx}"):
                    st.session_state.med_list_state.pop(idx)
                    st.rerun()

    if st.button("➕ Add Another Medicine", key="add_med_row_btn"):
        st.session_state.med_list_state.append({
            "medicine_name": "",
            "strength": "",
            "prescribed_dosage": "",
            "actual_dosage": "",
            "frequency": "Once a day",
            "time_taken": "Morning",
            "duration": "Ongoing",
            "relationship": "Prescribed by Physician"
        })
        st.rerun()

    st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # 5. FOOD INFORMATION
    # -------------------------------------------------------------------------
    st.markdown(f"### 🥗 5. Food & Beverage Information ({len(st.session_state.food_list_state)} active)")
    st.caption("Record foods, drinks, and dietary supplements taken around medication hours.")

    for idx, food in enumerate(st.session_state.food_list_state):
        with st.expander(f"Dietary Item #{idx + 1}: {food.get('food_name', 'Item')} ({food.get('category', '')})", expanded=True):
            fc1, fc2, fc3 = st.columns(3)
            with fc1:
                food["food_name"] = st.text_input("Food / Drink Name *", value=food.get("food_name", ""), key=f"f_name_{idx}")
                cat_idx = FOOD_CATEGORIES.index(food.get("category", "General Food")) if food.get("category") in FOOD_CATEGORIES else 0
                food["category"] = st.selectbox("Category", options=FOOD_CATEGORIES, index=cat_idx, key=f"f_cat_{idx}")
            with fc2:
                food["quantity"] = st.text_input("Quantity / Portion", value=food.get("quantity", "1 serving"), key=f"f_qty_{idx}")
                food["time_consumed"] = st.selectbox("Time Consumed", options=["Breakfast", "Lunch", "Dinner", "Evening Snack", "Throughout Day"], key=f"f_time_{idx}")
            with fc3:
                rel_opts = ["Before Medicine", "With Medicine", "After Medicine"]
                r_idx = rel_opts.index(food.get("relationship_to_med", "With Medicine")) if food.get("relationship_to_med") in rel_opts else 1
                food["relationship_to_med"] = st.selectbox("Relationship to Medicine", options=rel_opts, index=r_idx, key=f"f_rel_{idx}")
                st.markdown("<div style='margin-top: 1.6rem;'></div>", unsafe_allow_html=True)
                if st.button(f"🗑️ Remove Item #{idx + 1}", key=f"del_food_btn_{idx}"):
                    st.session_state.food_list_state.pop(idx)
                    st.rerun()

    if st.button("➕ Add Another Food / Drink Item", key="add_food_row_btn"):
        st.session_state.food_list_state.append({
            "food_name": "",
            "category": "General Food",
            "quantity": "1 serving",
            "time_consumed": "Lunch",
            "relationship_to_med": "With Medicine"
        })
        st.rerun()

    st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # 6. SYMPTOMS & SEVERITY
    # -------------------------------------------------------------------------
    st.markdown("### 🩺 6. Symptoms & Severity")
    st.caption("Select any acute symptoms experienced recently.")

    sym_dict = {s["symptom_name"]: s["severity"] for s in existing_symptoms}
    selected_symptoms = []

    s_cols = st.columns(3)
    for idx, sym in enumerate(SYSTEM_SYMPTOMS):
        with s_cols[idx % 3]:
            is_checked = sym in sym_dict
            if st.checkbox(sym, value=is_checked, key=f"sym_chk_{idx}"):
                default_sev = sym_dict.get(sym, "Mild")
                sev_idx = ["Mild", "Moderate", "Severe"].index(default_sev) if default_sev in ["Mild", "Moderate", "Severe"] else 0
                sev = st.selectbox(f"Severity: {sym}", options=["Mild", "Moderate", "Severe"], index=sev_idx, key=f"sym_sev_{idx}")
                selected_symptoms.append({"symptom_name": sym, "severity": sev, "time_started": "Recent"})

    st.markdown("<div style='margin-top: 2.5rem;'></div>", unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # 7. SAVE BUTTON & DATABASE PERSISTENCE
    # -------------------------------------------------------------------------
    if st.button("SAVE AND CONTINUE TO RISK ANALYSIS →", key="save_patient_data_btn", type="primary", use_container_width=True):
        if not p_name.strip():
            st.error("Patient Name is required.")
        else:
            allergies_payload = []
            if med_allergies.strip():
                for a in med_allergies.split(","):
                    if a.strip():
                        allergies_payload.append({"name": a.strip(), "type": "Medicine", "severity": "Major"})
            if food_allergies.strip():
                for fa in food_allergies.split(","):
                    if fa.strip():
                        allergies_payload.append({"name": fa.strip(), "type": "Food", "severity": "Moderate"})

            cleaned_meds = [m for m in st.session_state.med_list_state if m.get("medicine_name", "").strip()]
            cleaned_foods = [f for f in st.session_state.food_list_state if f.get("food_name", "").strip()]

            patient_info = {
                "name": p_name.strip(),
                "age": int(p_age),
                "gender": p_gender,
                "weight": float(p_weight),
                "height": float(p_height),
                "blood_group": p_blood
            }

            save_complete_patient_data(
                user_id=user_id,
                patient_info=patient_info,
                conditions=selected_conditions,
                allergies=allergies_payload,
                medications=cleaned_meds,
                foods=cleaned_foods,
                symptoms=selected_symptoms
            )

            # Immediately refresh cached bundle with newly saved data
            st.session_state.patient_bundle = get_patient_bundle(user_id)
            st.session_state.current_patient = st.session_state.patient_bundle.get("patient")
            st.session_state.patient_dirty = False
            st.session_state.last_interaction_data = None

            st.success("Information saved into SQLite database successfully.")
            # Automatically activate Step 2 and transition
            st.session_state.process_step = 2
            st.session_state.current_page = "process"
            st.rerun()
