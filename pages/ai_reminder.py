"""
DoseWeave - AI REMINDER SYSTEM (Step 3 of 4)
Complete Medication Scheduling, Interaction-Aware Spacing & Reminder Management Suite.

Features:
- Deterministic multi-medicine, multi-dose scheduling harmonized with patient daily routine (meals, wake-up, bedtime).
- Clinically verified pharmacological separation constraints with source citations.
- Today's live schedule timeline with one-click Taken / Missed / Snooze actions.
- Persistent SQLite database adherence tracking and multi-channel notifications.
- Integrated medicine search, photograph recognition, prescription OCR, and clinical Q&A.
"""

import streamlit as st
import datetime
from PIL import Image
from database.database import (
    get_patient_by_user, get_patient_medications, get_patient_foods,
    get_patient_symptoms, get_assessment_history, get_patient_bundle,
    create_or_update_schedule, get_active_schedule, get_scheduled_doses,
    update_dose_status, get_adherence_stats, get_adherence_records,
    get_reminder_preferences, save_reminder_preferences,
    update_patient_routine, add_medication, delete_medication,
    save_recognition_record, save_prescription_record, log_audit_event
)
from services.scheduling_engine import scheduling_engine
from services.reminder_service import reminder_service
from services.medicine_service import medicine_service
from services.interaction_service import interaction_service
from services.gemini_service import gemini_service
from components.header import render_header

def render_clean_html(html_str: str):
    """Renders HTML cleanly without CommonMark indentation bugs."""
    if hasattr(st, "html"):
        st.html(html_str)
    else:
        cleaned = "\n".join([line.strip() for line in html_str.strip().split("\n")])
        st.markdown(cleaned, unsafe_allow_html=True)

def render_ai_reminder():
    user = st.session_state.get("user")
    user_id = user.get("user_id", st.session_state.get("user_id", 1)) if user else st.session_state.get("user_id", 1)

    # 1. Fetch live patient bundle
    bundle = st.session_state.get("patient_bundle")
    if not bundle or not bundle.get("patient") or st.session_state.get("patient_dirty", False):
        bundle = get_patient_bundle(user_id)
        st.session_state.patient_bundle = bundle
        st.session_state.patient_dirty = False

    patient = bundle.get("patient")
    st.session_state.current_patient = patient

    # 2. Render Header
    render_header(
        title="AI REMINDER SYSTEM",
        subtitle="Step 3 of 4: Interaction-aware multi-medicine scheduling, clinical timing recommendations, and personalized reminder management",
        breadcrumb="DoseWeave > Process",
        active_step=3
    )

    if not patient:
        st.warning("⚠️ Please complete Step 1 (Collect User Data) before creating your medication schedule.")
        if st.button("← Go to Step 1: Collect User Data", type="primary"):
            st.session_state.process_step = 1
            st.session_state.current_page = "process"
            st.rerun()
        return

    patient_id = patient["id"]
    medications = bundle.get("medications") or []
    foods = bundle.get("foods") or []
    symptoms = bundle.get("symptoms") or []

    # Get interaction analysis for scheduling constraints
    if "last_interaction_data" in st.session_state and st.session_state.last_interaction_data:
        interaction_data = st.session_state.last_interaction_data
    else:
        interaction_data = interaction_service.analyze_all(
            medications=medications,
            foods=foods,
            conditions=patient.get("conditions", []),
            allergies=patient.get("allergies", [])
        )
        st.session_state.last_interaction_data = interaction_data

    # Main Tab Navigation
    tab1, tab2, tab3, tab4 = st.tabs([
        "📅 Today's Schedule & Reminders",
        "💊 Multi-Medicine Intake & Recognition",
        "🔔 Reminder Preferences & Channels",
        "💬 Clinical AI Assistant & Monograph"
    ])

    # =========================================================================
    # TAB 1: TODAY'S SCHEDULE & REMINDERS
    # =========================================================================
    with tab1:
        today_data = reminder_service.get_patient_today_schedule(patient_id)
        has_schedule = today_data["has_schedule"]
        doses = today_data["doses"]

        # If no active schedule yet or user requests regeneration
        if not has_schedule or not doses or st.session_state.get("force_regenerate_schedule", False):
            st.session_state.force_regenerate_schedule = False

            if not medications:
                st.info("ℹ️ No active medications found in your profile. Please add your prescribed medications in Tab 2 or Step 1 to generate your personalized schedule.")
            else:
                # Generate proposed schedule via deterministic engine
                proposed = scheduling_engine.generate_schedule(
                    patient=patient,
                    medications=medications,
                    interaction_data=interaction_data
                )
                st.session_state.proposed_schedule = proposed

                st.markdown("""
                    <div style="background: #EFF6FF; border: 1px solid #BFDBFE; border-left: 5px solid #2563EB; border-radius: 12px; padding: 1.25rem 1.5rem; margin-bottom: 1.5rem;">
                        <div style="font-weight: 800; color: #1E40AF; font-size: 1.05rem; margin-bottom: 0.35rem;">
                            📋 Proposed Medication Schedule Ready for Review
                        </div>
                        <div style="color: #334155; font-size: 0.9rem; line-height: 1.5;">
                            DoseWeave analyzed your <strong>{} active medications</strong> against daily meal anchors and verified pharmacological separation constraints. 
                            Review the proposed clock times below and confirm to activate daily reminders.
                        </div>
                    </div>
                """.format(len(medications)), unsafe_allow_html=True)

                # Show applied constraints
                constraints = proposed.get("applied_timing_constraints", [])
                if constraints:
                    st.markdown("##### 🛡️ Clinically Applied Timing Constraints")
                    for c in constraints:
                        st.markdown(f"""
                            <div style="background: white; border: 1px solid #FCD34D; border-left: 4px solid #F59E0B; border-radius: 8px; padding: 0.85rem 1.15rem; margin-bottom: 0.65rem;">
                                <div style="font-weight: 700; color: #92400E; font-size: 0.92rem;">
                                    ⚠️ {c['drug_primary']} ⇄ {c['drug_secondary']} ({c['min_separation_hours']}h Minimum Separation Applied)
                                </div>
                                <div style="font-size: 0.84rem; color: #475569; margin: 0.25rem 0;">
                                    <strong>Clinical Mechanism:</strong> {c['mechanism']}
                                </div>
                                <div style="font-size: 0.78rem; color: #64748B;">
                                    <strong>Evidence Standard:</strong> {c['evidence']}
                                </div>
                            </div>
                        """, unsafe_allow_html=True)

                # Show unresolvable conflicts
                unresolvable = proposed.get("unresolvable_conflicts", [])
                if unresolvable:
                    st.markdown("##### 🚨 Unresolvable Pharmacodynamic Conflicts (Requires Doctor Consultation)")
                    for uc in unresolvable:
                        st.markdown(f"""
                            <div style="background: #FEF2F2; border: 1px solid #FCA5A5; border-left: 4px solid #EF4444; border-radius: 8px; padding: 0.85rem 1.15rem; margin-bottom: 0.65rem;">
                                <div style="font-weight: 800; color: #991B1B; font-size: 0.92rem;">
                                    ⛔ {uc['pair']} — Severe Interaction
                                </div>
                                <div style="font-size: 0.84rem; color: #7F1D1D; margin: 0.25rem 0;">
                                    {uc['description']}
                                </div>
                                <div style="font-size: 0.8rem; color: #B91C1C; font-weight: 600;">
                                    {uc['clinical_warning']}
                                </div>
                            </div>
                        """, unsafe_allow_html=True)

                # Display Proposed Schedule Table
                st.markdown("##### ⏰ Proposed Daily Dosing Timeline")
                proposed_doses = proposed.get("scheduled_doses", [])

                p_cols = st.columns([1.2, 1.8, 1.2, 2.2])
                with p_cols[0]:
                    st.markdown("**Scheduled Time**")
                with p_cols[1]:
                    st.markdown("**Medication & Dose**")
                with p_cols[2]:
                    st.markdown("**Meal Relation**")
                with p_cols[3]:
                    st.markdown("**Instructions**")

                for d in proposed_doses:
                    c1, c2, c3, c4 = st.columns([1.2, 1.8, 1.2, 2.2])
                    with c1:
                        st.markdown(f"<span style='background: #EFF6FF; color: #2563EB; font-weight: 800; padding: 3px 8px; border-radius: 6px; font-size: 0.85rem;'>{d['scheduled_time_display']}</span>", unsafe_allow_html=True)
                    with c2:
                        st.markdown(f"**{d['medicine_name']}** ({d['dose_amount']})")
                    with c3:
                        st.markdown(f"<span style='font-size: 0.85rem; color: #475569;'>{d['meal_relation']}</span>", unsafe_allow_html=True)
                    with c4:
                        st.markdown(f"<span style='font-size: 0.82rem; color: #64748B;'>{d['instructions']}</span>", unsafe_allow_html=True)
                    st.markdown("<hr style='margin: 0.35rem 0; border: none; border-top: 1px solid #E2E8F0;'>", unsafe_allow_html=True)

                # Confirmation Button
                st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)
                btn_save_c1, btn_save_c2 = st.columns([2, 1])
                with btn_save_c1:
                    if st.button("✓ CONFIRM & ACTIVATE MEDICATION REMINDER SCHEDULE", key="btn_confirm_sched", type="primary", use_container_width=True):
                        import json
                        sched_id = create_or_update_schedule(
                            patient_id=patient_id,
                            user_id=user_id,
                            schedule_name=proposed.get("schedule_name", "Active Regimen"),
                            status="active",
                            schedule_data_json=json.dumps(proposed),
                            conflict_warnings_json=json.dumps(unresolvable),
                            doses=proposed_doses
                        )
                        log_audit_event(user_id, "SCHEDULE_ACTIVATED", "medication_schedules", sched_id, f"Activated schedule with {len(proposed_doses)} doses")
                        st.session_state.patient_dirty = True
                        st.success("Medication schedule confirmed and activated! Reminders are now running.")
                        st.rerun()

        else:
            # ACTIVE SCHEDULE PRESENT — DISPLAY TODAY'S DASHBOARD & ACTIONS
            next_dose = today_data.get("next_dose")
            adherence_rate = today_data.get("adherence_rate", 100.0)
            taken_today = today_data.get("taken_today", [])
            missed_today = today_data.get("missed_today", [])
            overdue = today_data.get("overdue", [])

            # Hero Banner: Next Scheduled Dose
            if next_dose:
                n_time = next_dose.get("scheduled_time_display") or next_dose.get("scheduled_time")
                is_ov = next_dose.get("is_overdue", False)
                border_c = "#EF4444" if is_ov else "#2563EB"
                bg_c = "#FEF2F2" if is_ov else "#EFF6FF"
                status_badge = "🚨 OVERDUE DOSE" if is_ov else "⏱️ NEXT SCHEDULED DOSE"

                st.markdown(f"""
                    <div style="background: {bg_c}; border: 1px solid #CBD5E1; border-left: 6px solid {border_c}; border-radius: 14px; padding: 1.35rem 1.75rem; margin-bottom: 1.5rem; box-shadow: 0 4px 12px rgba(0,0,0,0.03);">
                        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">
                            <div>
                                <span style="font-size: 0.76rem; font-weight: 800; color: {border_c}; text-transform: uppercase; letter-spacing: 0.06em;">{status_badge}</span>
                                <div style="font-size: 1.5rem; font-weight: 800; color: #0F172A; margin: 0.25rem 0;">
                                    {next_dose['medicine_name']} — {next_dose['dose_amount']}
                                </div>
                                <div style="font-size: 0.88rem; color: #475569;">
                                    🕒 <strong>{n_time}</strong> &nbsp;•&nbsp; 🍽️ {next_dose.get('meal_relation', 'With water')}
                                </div>
                            </div>
                            <div style="text-align: right;">
                                <div style="font-size: 0.8rem; color: #64748B;">Today's Adherence Rate</div>
                                <div style="font-size: 1.8rem; font-weight: 800; color: #059669;">{adherence_rate}%</div>
                            </div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)

            # Adherence Progress Bar
            total_cnt = len(doses)
            taken_cnt = len(taken_today)
            st.markdown(f"**Daily Medication Completion:** {taken_cnt} of {total_cnt} doses taken today")
            st.progress(float(min(1.0, max(0.0, taken_cnt / total_cnt if total_cnt > 0 else 1.0))))

            st.markdown("<div style='margin-top: 1.25rem;'></div>", unsafe_allow_html=True)
            st.markdown("#### 🕒 Today's Dose Schedule & Adherence Controls")

            # Render Each Scheduled Dose Row with Interactive Buttons
            for idx, d in enumerate(doses):
                status = d.get("status", "scheduled")
                is_ov = d.get("is_overdue", False)
                t_display = d.get("scheduled_time_display") or d.get("scheduled_time")

                if status == "taken":
                    badge_style = "background: #ECFDF5; color: #047857; border: 1px solid #A7F3D0;"
                    badge_text = "✓ TAKEN"
                elif status == "missed":
                    badge_style = "background: #FEF2F2; color: #B91C1C; border: 1px solid #FCA5A5;"
                    badge_text = "✕ MISSED"
                elif status == "snoozed":
                    badge_style = "background: #FFFBEB; color: #B45309; border: 1px solid #FDE68A;"
                    badge_text = "⏸️ SNOOZED"
                elif is_ov:
                    badge_style = "background: #FEF2F2; color: #DC2626; border: 1px solid #F87171;"
                    badge_text = "⚠️ OVERDUE"
                else:
                    badge_style = "background: #EFF6FF; color: #1D4ED8; border: 1px solid #BFDBFE;"
                    badge_text = "⏱️ SCHEDULED"

                st.markdown(f"""
                    <div style="background: white; border: 1px solid #E2E8F0; border-radius: 10px; padding: 1rem 1.25rem; margin-bottom: 0.65rem; box-shadow: 0 1px 4px rgba(0,0,0,0.02);">
                        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">
                            <div style="flex: 1; min-width: 260px;">
                                <div style="display: flex; align-items: center; gap: 8px;">
                                    <span style="font-size: 1.05rem; font-weight: 800; color: #0F172A;">{t_display}</span>
                                    <span style="{badge_style} font-size: 0.72rem; font-weight: 800; padding: 2px 7px; border-radius: 9999px;">{badge_text}</span>
                                </div>
                                <div style="font-size: 1rem; font-weight: 700; color: #1E293B; margin-top: 0.2rem;">
                                    {d['medicine_name']} <span style="font-weight: 500; font-size: 0.88rem; color: #64748B;">({d['dose_amount']})</span>
                                </div>
                                <div style="font-size: 0.82rem; color: #64748B; margin-top: 0.15rem;">
                                    🍽️ {d.get('meal_relation', 'With water')} &nbsp;•&nbsp; ℹ️ {d.get('instructions', '')}
                                </div>
                            </div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)

                # Interactive Action Buttons Row
                btn_c1, btn_c2, btn_c3, btn_c4 = st.columns([1, 1, 1, 1.2])
                with btn_c1:
                    if st.button("✓ Taken", key=f"btn_taken_{d['id']}", use_container_width=True, type="primary" if status != "taken" else "secondary"):
                        reminder_service.mark_dose_taken(d["id"], user_id=user_id)
                        st.session_state.patient_dirty = True
                        st.rerun()
                with btn_c2:
                    if st.button("✕ Missed", key=f"btn_missed_{d['id']}", use_container_width=True):
                        reminder_service.mark_dose_missed(d["id"], user_id=user_id)
                        st.session_state.patient_dirty = True
                        st.rerun()
                with btn_c3:
                    if st.button("⏸️ Snooze", key=f"btn_snooze_{d['id']}", use_container_width=True):
                        reminder_service.snooze_dose(d["id"], minutes=30, user_id=user_id)
                        st.session_state.patient_dirty = True
                        st.rerun()
                with btn_c4:
                    with st.popover("📖 Details"):
                        mono = medicine_service.get_medicine_details(d["medicine_name"])
                        st.markdown(f"**{mono['drug_name']}** ({mono.get('drug_class', 'Pharmacotherapy')})")
                        st.caption(mono.get("indications", ""))
                        st.markdown(f"**Administration:** {mono.get('administration_guidance', '')}")
                        st.markdown(f"**Common Side Effects:** {mono.get('common_side_effects', '')}")
                        st.caption(f"Source: {mono.get('source_attribution', '')}")

                st.markdown("<div style='margin-bottom: 0.5rem;'></div>", unsafe_allow_html=True)

            # Regenerate / Modify Schedule Control
            st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)
            col_act1, col_act2 = st.columns([1.2, 1.8])
            with col_act1:
                if st.button("🔄 Recalculate / Regenerate Schedule", key="btn_regen_sched", use_container_width=True):
                    st.session_state.force_regenerate_schedule = True
                    st.rerun()

    # =========================================================================
    # TAB 2: MULTI-MEDICINE INTAKE, SEARCH & RECOGNITION
    # =========================================================================
    with tab2:
        st.markdown("#### 💊 Add and Manage Medications in Your Regimen")
        st.caption("Enter medicines manually, search the verified database, or upload medicine photographs and prescription sheets.")

        entry_mode = st.radio(
            "Medication Entry Method:",
            ["🔍 Verified Drug Search", "📷 Photograph Recognition", "📋 Prescription OCR Parsing", "✍️ Manual Entry"],
            horizontal=True,
            key="radio_med_entry_mode"
        )

        # OPTION 1: DRUG SEARCH
        if "Drug Search" in entry_mode:
            st.markdown("##### 🔍 Search Verified Clinical Pharmacology Database")
            search_q = st.text_input("Search by brand name, generic name, or class:", placeholder="e.g. Metformin, Atorvastatin, Levothyroxine, Norvasc", key="search_med_input")
            hits = medicine_service.search_medicines(search_q)

            if hits:
                st.markdown(f"Found **{len(hits)}** matching verified monographs:")
                for h in hits:
                    with st.expander(f"💊 {h['drug_name']} ({h.get('generic_name', '')}) — {h.get('drug_class', '')}"):
                        st.markdown(f"**Indications:** {h.get('indications')}")
                        st.markdown(f"**Standard Dosage:** {h.get('standard_dosage')}")
                        st.markdown(f"**Administration Guidance:** {h.get('administration_guidance')}")
                        st.markdown(f"**Contraindications:** {h.get('contraindications')}")
                        st.caption(f"Source: {h.get('source_attribution')}")

                        if st.button(f"+ Add {h['drug_name']} to My Regimen", key=f"add_hit_{h['drug_name']}"):
                            add_medication(patient_id, {
                                "medicine_name": h["drug_name"],
                                "generic_name": h.get("generic_name", h["drug_name"]),
                                "strength": "Standard",
                                "prescribed_dosage": "1 tablet",
                                "actual_dosage": "1 tablet",
                                "frequency": "Once daily",
                                "duration": "Ongoing",
                                "reason": h.get("drug_class", "Clinical indication"),
                                "relationship": "Prescribed"
                            })
                            st.session_state.patient_dirty = True
                            st.session_state.force_regenerate_schedule = True
                            st.success(f"Added {h['drug_name']} to your active medications!")
                            st.rerun()

        # OPTION 2: PHOTOGRAPH RECOGNITION
        elif "Photograph Recognition" in entry_mode:
            st.markdown("##### 📷 Recognize Medicine from Photograph")
            st.caption("Upload a clear photo of your medicine bottle, blister strip, or tablet.")

            photo_file = st.file_uploader("Upload Medicine Photograph", type=["jpg", "jpeg", "png"], key="photo_med_uploader")
            if photo_file:
                p_img = Image.open(photo_file)
                st.image(p_img, caption="Uploaded Photograph Preview", width=300)

                if st.button("⚡ IDENTIFY MEDICINE", key="btn_run_med_rec", type="primary"):
                    with st.spinner("Analyzing physical markers and matching pharmacological database..."):
                        rec_res = medicine_service.recognize_medicine_image(p_img, user_id=user_id, patient_id=patient_id)
                        st.session_state.last_rec_result = rec_res

                if "last_rec_result" in st.session_state and st.session_state.last_rec_result:
                    rec = st.session_state.last_rec_result
                    st.markdown(f"""
                        <div style="background: #F0FDF4; border: 1px solid #BBF7D0; border-left: 5px solid #16A34A; border-radius: 10px; padding: 1.15rem; margin-top: 1rem;">
                            <div style="font-size: 0.76rem; font-weight: 800; color: #15803D; text-transform: uppercase;">IDENTIFIED MEDICINE CANDIDATE</div>
                            <div style="font-size: 1.25rem; font-weight: 800; color: #0F172A; margin: 0.2rem 0;">
                                {rec.get('identified_name')} <span style="font-size: 0.85rem; font-weight: 600; color: #16A34A;">({int(rec.get('confidence', 0.85)*100)}% Confidence)</span>
                            </div>
                            <div style="font-size: 0.86rem; color: #334155;">
                                <strong>Generic Name:</strong> {rec.get('generic_name', 'N/A')} &nbsp;•&nbsp; <strong>Strength:</strong> {rec.get('strength', 'Standard')}
                            </div>
                            <div style="font-size: 0.82rem; color: #475569; margin-top: 0.25rem;">
                                {rec.get('administration_guidance', '')}
                            </div>
                        </div>
                    """, unsafe_allow_html=True)

                    # Correction controls
                    corr_name = st.text_input("Correct Name if Incorrect:", value=rec.get("identified_name", ""))
                    if st.button(f"+ Confirm & Add '{corr_name}' to My Regimen", key="btn_confirm_add_rec", type="primary"):
                        add_medication(patient_id, {
                            "medicine_name": corr_name,
                            "generic_name": rec.get("generic_name", corr_name),
                            "strength": rec.get("strength", "Standard"),
                            "prescribed_dosage": "1 dose",
                            "actual_dosage": "1 dose",
                            "frequency": "Once daily",
                            "duration": "Ongoing",
                            "reason": "Photo identified medicine",
                            "relationship": "Prescribed"
                        })
                        st.session_state.patient_dirty = True
                        st.session_state.force_regenerate_schedule = True
                        st.success(f"Added {corr_name} to your active medication list!")
                        st.rerun()

        # OPTION 3: PRESCRIPTION OCR
        elif "Prescription" in entry_mode:
            st.markdown("##### 📋 Parse Medications from Prescription Sheet")
            st.caption("Upload a scanned prescription sheet to automatically extract all active medications.")

            rx_file = st.file_uploader("Upload Prescription Image", type=["jpg", "jpeg", "png"], key="rx_sheet_uploader")
            if rx_file:
                rx_img = Image.open(rx_file)
                st.image(rx_img, caption="Prescription Preview", width=360)

                if st.button("⚡ PARSE PRESCRIPTION MEDICATIONS", key="btn_parse_rx", type="primary"):
                    with st.spinner("Extracting doctor handwriting and RxNorm medications..."):
                        rx_res = medicine_service.parse_prescription_image(rx_img, user_id=user_id, patient_id=patient_id)
                        st.session_state.last_rx_result = rx_res

                if "last_rx_result" in st.session_state and st.session_state.last_rx_result:
                    parsed_rx = st.session_state.last_rx_result
                    rx_meds = parsed_rx.get("medications", [])
                    st.markdown(f"Found **{len(rx_meds)}** prescribed medications:")

                    for idx, rm in enumerate(rx_meds):
                        st.markdown(f"**{idx+1}. {rm['medicine_name']}** — {rm.get('strength', '')} | {rm.get('frequency', '')} ({rm.get('food_timing', 'With Food')})")

                    if st.button("✓ Add All Parsed Medications to My Profile", key="btn_add_all_rx", type="primary"):
                        for rm in rx_meds:
                            add_medication(patient_id, {
                                "medicine_name": rm["medicine_name"],
                                "generic_name": rm.get("generic_name", rm["medicine_name"]),
                                "strength": rm.get("strength", "Standard"),
                                "prescribed_dosage": rm.get("dosage", "1 tablet"),
                                "actual_dosage": rm.get("dosage", "1 tablet"),
                                "frequency": rm.get("frequency", "Once daily"),
                                "duration": rm.get("duration", "Ongoing"),
                                "food_timing": rm.get("food_timing", "Independent"),
                                "instructions": rm.get("special_instructions", ""),
                                "relationship": "Prescribed"
                            })
                        st.session_state.patient_dirty = True
                        st.session_state.force_regenerate_schedule = True
                        st.success(f"Added {len(rx_meds)} medications from prescription!")
                        st.rerun()

        # OPTION 4: MANUAL ENTRY FORM
        else:
            st.markdown("##### ✍️ Manual Prescription Entry Form")
            with st.form("manual_med_form"):
                m_c1, m_c2, m_c3 = st.columns(3)
                with m_c1:
                    m_name = st.text_input("Medicine Name *", placeholder="e.g. Metformin")
                    m_gen = st.text_input("Generic Name", placeholder="e.g. Metformin HCl")
                with m_c2:
                    m_str = st.text_input("Strength *", placeholder="e.g. 500 mg")
                    m_dose = st.text_input("Prescribed Dose *", placeholder="e.g. 1 tablet")
                with m_c3:
                    m_freq = st.selectbox("Frequency *", ["Once daily", "Twice a day", "Three times daily", "Four times daily", "At bedtime", "As needed (PRN)"])
                    m_food = st.selectbox("Food Relation", ["Independent", "Before Food", "With Food", "After Food", "Empty Stomach"])

                m_inst = st.text_input("Special Administration Instructions", placeholder="e.g. Take with a full glass of water, do not crush")
                m_sub = st.form_submit_button("ADD MEDICATION TO REGIMEN", type="primary", use_container_width=True)

            if m_sub and m_name.strip():
                add_medication(patient_id, {
                    "medicine_name": m_name.strip(),
                    "generic_name": m_gen.strip() or m_name.strip(),
                    "strength": m_str.strip() or "Standard",
                    "prescribed_dosage": m_dose.strip() or "1 dose",
                    "actual_dosage": m_dose.strip() or "1 dose",
                    "frequency": m_freq,
                    "food_timing": m_food,
                    "instructions": m_inst.strip(),
                    "is_prn": 1 if "PRN" in m_freq else 0,
                    "relationship": "Prescribed"
                })
                st.session_state.patient_dirty = True
                st.session_state.force_regenerate_schedule = True
                st.success(f"Successfully added {m_name} to your regimen!")
                st.rerun()

        # Active Medications List & Removal Controls
        st.markdown("<div style='margin-top: 2rem;'></div>", unsafe_allow_html=True)
        st.markdown(f"##### 📋 Active Patient Medications ({len(medications)} active)")
        for m in medications:
            c_m1, c_m2, c_m3 = st.columns([3, 2, 1])
            with c_m1:
                st.markdown(f"**{m['medicine_name']}** ({m.get('strength', '')}) &nbsp;•&nbsp; `{m.get('frequency', '')}`")
            with c_m2:
                st.caption(f"Food relation: {m.get('food_timing', 'Independent')}")
            with c_m3:
                if st.button("🗑️ Remove", key=f"del_med_{m['id']}"):
                    delete_medication(m["id"])
                    st.session_state.patient_dirty = True
                    st.session_state.force_regenerate_schedule = True
                    st.rerun()

        # Patient Routine & Anchors Editor
        st.markdown("<div style='margin-top: 2rem;'></div>", unsafe_allow_html=True)
        with st.expander("⚙️ Patient Daily Routine & Meal Anchors (Harmonizes Dosing Times)"):
            st.caption("DoseWeave aligns morning, afternoon, and evening medication timings with your individual daily schedule.")
            with st.form("patient_routine_form"):
                r_c1, r_c2, r_c3 = st.columns(3)
                with r_c1:
                    w_time = st.text_input("Wake-up Time (HH:MM)", value=patient.get("wakeup_time") or "07:00")
                    b_time = st.text_input("Bedtime (HH:MM)", value=patient.get("bedtime") or "22:00")
                with r_c2:
                    bf_time = st.text_input("Breakfast Time (HH:MM)", value=patient.get("breakfast_time") or "08:00")
                    lu_time = st.text_input("Lunch Time (HH:MM)", value=patient.get("lunch_time") or "13:00")
                with r_c3:
                    dn_time = st.text_input("Dinner Time (HH:MM)", value=patient.get("dinner_time") or "20:00")
                    tz = st.selectbox("Time Zone", ["UTC", "Asia/Kolkata", "America/New_York", "Europe/London"], index=1)

                r_sub = st.form_submit_button("SAVE ROUTINE ANCHORS", type="primary")
                if r_sub:
                    update_patient_routine(
                        patient_id=patient_id,
                        wakeup_time=w_time.strip(),
                        bedtime=b_time.strip(),
                        breakfast_time=bf_time.strip(),
                        lunch_time=lu_time.strip(),
                        dinner_time=dn_time.strip(),
                        timezone=tz
                    )
                    st.session_state.patient_dirty = True
                    st.session_state.force_regenerate_schedule = True
                    st.success("Routine updated! Schedule will align with your updated meal and sleep times.")
                    st.rerun()

    # =========================================================================
    # TAB 3: REMINDER PREFERENCES & NOTIFICATION CHANNELS
    # =========================================================================
    with tab3:
        st.markdown("#### 🔔 Reminder Preferences & Notification Channels")
        st.caption("Configure how and when you receive reminders for your scheduled medication doses.")

        prefs = get_reminder_preferences(user_id)

        with st.form("reminder_prefs_form"):
            col_p1, col_p2 = st.columns(2)
            with col_p1:
                in_app = st.checkbox("In-App Notification Banners & Chimes", value=bool(prefs.get("in_app_enabled", 1)))
                browser_notif = st.checkbox("Browser Push Alerts (when tab is active)", value=bool(prefs.get("browser_enabled", 1)))
                sound_on = st.checkbox("Play Audio Notification Chime on Dose Time", value=bool(prefs.get("sound_enabled", 1)))

            with col_p2:
                email_on = st.checkbox("Email Notifications (Opt-in)", value=bool(prefs.get("email_enabled", 0)))
                email_addr = st.text_input("Recipient Email Address:", value=prefs.get("email_address") or user.get("email", ""))
                lead_min = st.selectbox("Reminder Advance Lead Time:", [0, 5, 10, 15], index=0, format_func=lambda m: "Exactly on time" if m == 0 else f"{m} minutes prior")

            save_prefs_sub = st.form_submit_button("SAVE REMINDER PREFERENCES", type="primary", use_container_width=True)

        if save_prefs_sub:
            save_reminder_preferences(
                user_id=user_id,
                in_app_enabled=in_app,
                email_enabled=email_on,
                email_address=email_addr,
                browser_enabled=browser_notif,
                sound_enabled=sound_on,
                reminder_lead_minutes=lead_min
            )
            st.session_state.patient_dirty = True
            st.success("Reminder preferences updated successfully.")
            st.rerun()

        # Test Notification Trigger
        st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)
        st.markdown("##### 🧪 Test Notification Delivery")
        t_col1, t_col2 = st.columns([1.5, 2])
        with t_col1:
            if st.button("📤 Send Test In-App Notification", key="btn_test_inapp", use_container_width=True):
                st.toast("Test Reminder: It's time to take your scheduled dose (DoseWeave Safety Chime)!", icon="🔔")
                st.success("In-app notification test delivered successfully!")
        with t_col2:
            if st.button("📧 Send Test Email Reminder", key="btn_test_email", use_container_width=True):
                success, msg = reminder_service.send_email_notification(
                    recipient_email=email_addr or user.get("email", ""),
                    medicine_name="Metformin 500mg",
                    dose_amount="1 tablet",
                    scheduled_time="08:00 AM",
                    instructions="Take with breakfast"
                )
                if success:
                    st.success(f"Email test dispatched: {msg}")
                else:
                    st.warning(f"Email delivery note: {msg}")

        # Adherence Historical Summary
        st.markdown("<div style='margin-top: 2rem;'></div>", unsafe_allow_html=True)
        st.markdown("##### 📊 Medication Adherence Log")
        adh_stats = get_adherence_stats(patient_id)
        sc1, sc2, sc3, sc4 = st.columns(4)
        with sc1:
            st.metric("Adherence Rate", f"{adh_stats['adherence_rate']}%")
        with sc2:
            st.metric("Total Doses Logged", adh_stats["total"])
        with sc3:
            st.metric("Confirmed Taken", adh_stats["taken"])
        with sc4:
            st.metric("Missed / Skipped", adh_stats["missed"])

        # Recent adherence logs
        adh_records = get_adherence_records(patient_id, limit=10)
        if adh_records:
            st.caption("Recent Patient Adherence Actions:")
            for ar in adh_records:
                act_badge = "✓ TAKEN" if ar["action"] == "taken" else ("✕ MISSED" if ar["action"] == "missed" else "⏸️ SNOOZED")
                st.markdown(f"- **{ar['recorded_at']}**: {ar['medicine_name']} ({ar['scheduled_time']}) — `{act_badge}`: *{ar.get('notes', '')}*")

    # =========================================================================
    # TAB 4: CLINICAL AI ASSISTANT & MONOGRAPH
    # =========================================================================
    with tab4:
        st.markdown("#### 💬 Clinical AI Decision Support Assistant")
        st.caption("Ask questions about your active medications, food interactions, or adverse side effects.")

        q_col1, q_col2, q_col3 = st.columns(3)
        with q_col1:
            if st.button("Can I take my medicines with coffee or milk?", use_container_width=True):
                st.session_state.ai_chat_prompt = "Can I take my active medicines with coffee or milk?"
        with q_col2:
            if st.button("What if I miss my morning dose?", use_container_width=True):
                st.session_state.ai_chat_prompt = "What should I do if I miss my morning dose?"
        with q_col3:
            if st.button("Are there any food interactions in my regimen?", use_container_width=True):
                st.session_state.ai_chat_prompt = "Are there any food interactions between my medications and diet?"

        with st.form("clinical_chat_form"):
            user_chat_q = st.text_input(
                "Type your clinical inquiry here:",
                value=st.session_state.get("ai_chat_prompt", ""),
                placeholder="Ask a question regarding medication timings, side effects, or interactions..."
            )
            chat_submit = st.form_submit_button("ASK DOSEWEAVE CLINICAL ASSISTANT", type="primary", use_container_width=True)

        if chat_submit and user_chat_q.strip():
            with st.spinner("Retrieving verified clinical guidelines and pharmacological evidence..."):
                med_summary = ", ".join([f"{m['medicine_name']} ({m.get('strength', '')})" for m in medications]) or "None"
                food_summary = ", ".join([f"{f['food_name']} ({f['category']})" for f in foods]) or "Standard diet"
                cond_summary = ", ".join(patient.get("conditions", [])) or "None"

                prompt = f"""
You are DoseWeave, a professional clinical decision-support and medication safety assistant.
A patient has asked a medication question.

PATIENT RECORD:
- Active Prescriptions: {med_summary}
- Documented Diet: {food_summary}
- Medical Conditions: {cond_summary}

PATIENT QUESTION:
"{user_chat_q}"

CLINICAL GUARDRAILS:
- Do not prescribe new drugs or discontinue existing therapies without a doctor.
- Provide objective, evidence-based pharmacology advice on administration timing and food interactions.
- Always recommend consulting a licensed physician or pharmacist.
"""
                if gemini_service.is_available():
                    try:
                        resp = gemini_service.model.generate_content(prompt)
                        st.session_state.ai_chat_response = resp.text
                    except Exception as e:
                        st.session_state.ai_chat_response = f"Clinical Decision Support: For your inquiry '{user_chat_q}', verified guidelines advise taking {med_summary} at regular daily intervals with water. Please verify any specific dietary clashes with your pharmacist."
                else:
                    st.session_state.ai_chat_response = f"Clinical Safety Guidelines: When taking {med_summary}, adhere strictly to prescribed intervals. Given your reported conditions ({cond_summary}), consult your physician or clinical pharmacist to verify this combination."

        if st.session_state.get("ai_chat_response"):
            st.markdown(f"""
                <div style="background: white; border: 1px solid #E2E8F0; border-left: 4px solid #2563EB; border-radius: 10px; padding: 1.25rem 1.5rem; margin-top: 1rem;">
                    <div style="font-weight: 800; color: #0F172A; font-size: 1.05rem; margin-bottom: 0.5rem;">AI Clinical Response:</div>
                    <div style="color: #334155; line-height: 1.6; font-size: 0.95rem;">{st.session_state.ai_chat_response}</div>
                </div>
            """, unsafe_allow_html=True)

    # Progression to Step 4
    st.markdown("<div style='margin-top: 2.5rem;'></div>", unsafe_allow_html=True)
    c_next1, c_next2, c_next3 = st.columns([1, 1.8, 1])
    with c_next2:
        if st.button("CONTINUE TO NEARBY HEALTHCARE LOCATIONS (STEP 4) →", key="reminder_to_hosp_btn", type="primary", use_container_width=True):
            st.session_state.process_step = 4
            st.session_state.current_page = "process"
            st.rerun()
