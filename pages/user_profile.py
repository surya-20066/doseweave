"""
MediSafe AI - Professional Healthcare User Profile Page
Displays authenticated user account details, linked clinical patient record,
medical summary, profile completion status, real recent activity, and quick workflow actions.
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from database.database import (
    get_user_by_id,
    get_patient_by_user,
    get_patient_medications,
    get_patient_conditions,
    get_patient_allergies,
    get_patient_assessments,
    update_user_profile,
    change_user_password,
    DB_PATH
)

def format_member_date(created_at_val) -> str:
    """Formats database created_at timestamp into Month Year."""
    if not created_at_val:
        return "September 2026"
    try:
        dt = datetime.fromisoformat(str(created_at_val).replace("Z", ""))
        return dt.strftime("%B %Y")
    except Exception:
        return str(created_at_val)[:10]

def render_clean_html(html_str: str):
    """Renders HTML cleanly without CommonMark indentation or code block parsing."""
    if hasattr(st, "html"):
        st.html(html_str)
    else:
        cleaned = "\n".join([line.strip() for line in html_str.strip().split("\n")])
        st.markdown(cleaned, unsafe_allow_html=True)

def render_user_profile():
    user = st.session_state.get("user")
    if not user:
        st.warning("Please sign in to view your profile.")
        if st.button("Go to Sign In", type="primary"):
            st.session_state.auth_tab = "Login"
            st.session_state.current_page = "login"
            st.rerun()
        return

    user_id = user.get("user_id")
    fresh_user = get_user_by_id(user_id) or user
    patient = get_patient_by_user(user_id)

    # -------------------------------------------------------------------------
    # 1. PAGE HEADER
    # -------------------------------------------------------------------------
    render_clean_html("""
<div style="margin-bottom: 0.5rem;">
    <h1 style="font-size: 2rem; font-weight: 800; color: #0F172A; margin: 0 0 0.25rem 0;">PROFILE</h1>
    <p style="font-size: 0.95rem; color: #64748B; margin: 0;">Manage your account and view your linked patient information.</p>
</div>
""")
    st.divider()

    # -------------------------------------------------------------------------
    # 2. TWO-COLUMN RESPONSIVE LAYOUT
    # -------------------------------------------------------------------------
    col_left, col_right = st.columns([1, 1.25], gap="large")

    # =========================================================================
    # LEFT COLUMN: ACCOUNT INFORMATION & PROFILE STATUS
    # =========================================================================
    with col_left:
        render_clean_html("""
<div style="font-size: 0.82rem; font-weight: 800; color: #2563EB; letter-spacing: 0.06em; text-transform: uppercase; margin-bottom: 0.65rem;">
    ACCOUNT INFORMATION
</div>
""")

        user_name = fresh_user.get("full_name", "Clinical User")
        user_email = fresh_user.get("email", "user@medisafe.ai")
        user_initial = user_name[0].upper() if user_name else "U"
        member_since = format_member_date(fresh_user.get("created_at"))
        display_user_id = fresh_user.get("user_id", user_id or 1)

        # Account Card with Avatar
        render_clean_html(f"""
<div class="profile-card-box">
    <div class="profile-avatar-wrapper">
        <div class="profile-avatar-circle">{user_initial}</div>
        <div>
            <div style="font-size: 1.15rem; font-weight: 800; color: #0F172A; line-height: 1.2;">{user_name}</div>
            <div style="font-size: 0.85rem; color: #64748B; margin-top: 2px;">{user_email}</div>
        </div>
    </div>
    <div class="profile-row">
        <span class="profile-row-label">Full Name</span>
        <span class="profile-row-value">{user_name}</span>
    </div>
    <div class="profile-row">
        <span class="profile-row-label">Email Address</span>
        <span class="profile-row-value">{user_email}</span>
    </div>
    <div class="profile-row">
        <span class="profile-row-label">Account Status</span>
        <span class="profile-row-value" style="color: #059669;">● Active</span>
    </div>
    <div class="profile-row">
        <span class="profile-row-label">Member Since</span>
        <span class="profile-row-value">{member_since}</span>
    </div>
    <div class="profile-row">
        <span class="profile-row-label">Account ID</span>
        <span class="profile-row-value">#{display_user_id}</span>
    </div>
</div>
""")

        # Account Actions (Edit Profile & Change Password)
        if "profile_action_mode" not in st.session_state:
            st.session_state.profile_action_mode = None

        c_act1, c_act2 = st.columns(2)
        with c_act1:
            is_editing = (st.session_state.profile_action_mode == "edit")
            if st.button("✏️ EDIT PROFILE", key="btn_edit_prof", use_container_width=True, type="primary" if is_editing else "secondary"):
                st.session_state.profile_action_mode = None if is_editing else "edit"
                st.rerun()
        with c_act2:
            is_pwd = (st.session_state.profile_action_mode == "password")
            if st.button("🔑 CHANGE PASSWORD", key="btn_change_pwd", use_container_width=True, type="primary" if is_pwd else "secondary"):
                st.session_state.profile_action_mode = None if is_pwd else "password"
                st.rerun()

        # ==================== EDIT PROFILE FORM ==================== #
        if st.session_state.profile_action_mode == "edit":
            st.markdown("<div style='margin-top: 0.75rem;'></div>", unsafe_allow_html=True)
            with st.form("edit_profile_form"):
                st.markdown("<div style='font-size: 0.95rem; font-weight: 800; color: #0F172A; margin-bottom: 0.5rem;'>Edit Account Details</div>", unsafe_allow_html=True)
                new_name = st.text_input("Full Name", value=user_name)
                new_email = st.text_input("Email Address", value=user_email)
                
                c_save, c_cancel = st.columns([1.2, 1])
                with c_save:
                    save_prof_submit = st.form_submit_button("SAVE CHANGES", type="primary", use_container_width=True)
                with c_cancel:
                    cancel_prof = st.form_submit_button("CANCEL", type="secondary", use_container_width=True)

            if cancel_prof:
                st.session_state.profile_action_mode = None
                st.rerun()

            if save_prof_submit:
                success, msg = update_user_profile(user_id, new_name, new_email)
                if success:
                    st.session_state.user["full_name"] = new_name.strip()
                    st.session_state.user["email"] = new_email.strip().lower()
                    st.session_state.profile_action_mode = None
                    st.success("Profile updated successfully!")
                    st.rerun()
                else:
                    st.error(msg)

        # ==================== CHANGE PASSWORD FORM ==================== #
        elif st.session_state.profile_action_mode == "password":
            st.markdown("<div style='margin-top: 0.75rem;'></div>", unsafe_allow_html=True)
            with st.form("change_password_form"):
                st.markdown("<div style='font-size: 0.95rem; font-weight: 800; color: #0F172A; margin-bottom: 0.5rem;'>Change Account Password</div>", unsafe_allow_html=True)
                curr_pwd = st.text_input("Current Password", type="password", placeholder="Enter current password")
                new_pwd = st.text_input("New Password", type="password", placeholder="At least 6 characters")
                confirm_new_pwd = st.text_input("Confirm New Password", type="password", placeholder="Repeat new password")
                
                c_save_pwd, c_cancel_pwd = st.columns([1.2, 1])
                with c_save_pwd:
                    save_pwd_submit = st.form_submit_button("UPDATE PASSWORD", type="primary", use_container_width=True)
                with c_cancel_pwd:
                    cancel_pwd = st.form_submit_button("CANCEL", type="secondary", use_container_width=True)

            if cancel_pwd:
                st.session_state.profile_action_mode = None
                st.rerun()

            if save_pwd_submit:
                if not curr_pwd:
                    st.error("Please enter your current password.")
                elif len(new_pwd) < 6:
                    st.error("New password must be at least 6 characters long.")
                elif new_pwd != confirm_new_pwd:
                    st.error("New passwords do not match.")
                else:
                    success, msg = change_user_password(user_id, curr_pwd, new_pwd)
                    if success:
                        st.session_state.profile_action_mode = None
                        st.success("Password changed successfully!")
                        st.rerun()
                    else:
                        st.error(msg)

        st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)

        # ---------------------------------------------------------------------
        # PROFILE STATUS (Based on Real SQLite Data)
        # ---------------------------------------------------------------------
        render_clean_html("""
<div style="font-size: 0.82rem; font-weight: 800; color: #2563EB; letter-spacing: 0.06em; text-transform: uppercase; margin-bottom: 0.65rem;">
    PROFILE STATUS
</div>
""")

        patient_exists = patient is not None
        meds = get_patient_medications(patient["id"]) if patient_exists else []
        conds = get_patient_conditions(patient["id"]) if patient_exists else []
        allergies = get_patient_allergies(patient["id"]) if patient_exists else []
        assessments = get_patient_assessments(patient["id"]) if patient_exists else []

        med_info_complete = bool(meds or conds or allergies)
        risk_available = len(assessments) > 0

        render_clean_html(f"""
<div class="profile-card-box">
    <div class="profile-status-item">
        <span style="color: #334155; font-weight: 600;">Account</span>
        <span style="color: #059669; font-weight: 700;">✓ Complete</span>
    </div>
    <div class="profile-status-item">
        <span style="color: #334155; font-weight: 600;">Patient Information</span>
        <span style="color: {'#059669' if patient_exists else '#D97706'}; font-weight: 700;">
            {'✓ Complete' if patient_exists else '⚠️ Incomplete'}
        </span>
    </div>
    <div class="profile-status-item">
        <span style="color: #334155; font-weight: 600;">Medical Information</span>
        <span style="color: {'#059669' if med_info_complete else '#D97706'}; font-weight: 700;">
            {'✓ Complete' if med_info_complete else '⚠️ Incomplete'}
        </span>
    </div>
    <div class="profile-status-item">
        <span style="color: #334155; font-weight: 600;">Risk Assessment</span>
        <span style="color: {'#059669' if risk_available else '#64748B'}; font-weight: 700;">
            {'✓ Available' if risk_available else 'Not Available'}
        </span>
    </div>
</div>
""")

        # Logout Action
        if st.button("LOGOUT", key="btn_profile_logout", use_container_width=True):
            st.session_state.clear()
            st.session_state.current_page = "home"
            st.rerun()

    # =========================================================================
    # RIGHT COLUMN: LINKED PATIENT RECORD & MEDICAL SUMMARY
    # =========================================================================
    with col_right:
        render_clean_html("""
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.65rem;">
    <div style="font-size: 0.82rem; font-weight: 800; color: #2563EB; letter-spacing: 0.06em; text-transform: uppercase;">
        LINKED PATIENT RECORD
    </div>
    <span style="background: #EFF6FF; color: #2563EB; font-weight: 700; font-size: 0.72rem; padding: 3px 10px; border-radius: 9999px; border: 1px solid #DBEAFE;">
        PRIMARY PROFILE
    </span>
</div>
""")

        if patient_exists:
            # 2-Column Responsive Grid for Patient Demographics
            p_name = patient.get("name", "Unknown Patient")
            p_age = f"{patient.get('age', 0)} Years"
            p_gender = patient.get("gender", "Not Specified")
            p_blood = patient.get("blood_group", "Not Specified")
            p_weight = f"{patient.get('weight', 0)} kg"
            p_height = f"{patient.get('height', 0)} cm"

            render_clean_html(f"""
<div class="profile-card-box">
    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 0.5rem;">
        <div class="patient-info-box">
            <div class="patient-info-label">PATIENT NAME</div>
            <div class="patient-info-value">{p_name}</div>
        </div>
        <div class="patient-info-box">
            <div class="patient-info-label">AGE</div>
            <div class="patient-info-value">{p_age}</div>
        </div>
        <div class="patient-info-box">
            <div class="patient-info-label">GENDER</div>
            <div class="patient-info-value">{p_gender}</div>
        </div>
        <div class="patient-info-box">
            <div class="patient-info-label">BLOOD GROUP</div>
            <div class="patient-info-value">{p_blood}</div>
        </div>
        <div class="patient-info-box">
            <div class="patient-info-label">WEIGHT</div>
            <div class="patient-info-value">{p_weight}</div>
        </div>
        <div class="patient-info-box">
            <div class="patient-info-label">HEIGHT</div>
            <div class="patient-info-value">{p_height}</div>
        </div>
    </div>
</div>
""")

            # -----------------------------------------------------------------
            # MEDICAL SUMMARY (Conditions, Allergies, Medications)
            # -----------------------------------------------------------------
            render_clean_html("""
<div style="font-size: 0.82rem; font-weight: 800; color: #0F172A; letter-spacing: 0.04em; text-transform: uppercase; margin: 1.25rem 0 0.65rem 0;">
    MEDICAL SUMMARY
</div>
""")

            with st.container():
                # Medical Conditions
                render_clean_html("<div style='font-size: 0.78rem; font-weight: 700; color: #64748B; text-transform: uppercase; margin-bottom: 0.35rem;'>Medical Conditions</div>")
                if conds:
                    cond_html = "".join([f'<span class="clinical-tag tag-condition">{c}</span>' for c in conds])
                    render_clean_html(f"<div>{cond_html}</div>")
                else:
                    st.caption("No information available.")

                st.markdown("<div style='margin-top: 0.75rem;'></div>", unsafe_allow_html=True)

                # Allergies
                render_clean_html("<div style='font-size: 0.78rem; font-weight: 700; color: #64748B; text-transform: uppercase; margin-bottom: 0.35rem;'>Allergies</div>")
                if allergies:
                    allergy_tags = []
                    for alg in allergies:
                        a_name = alg.get("allergen_name") if isinstance(alg, dict) else alg
                        allergy_tags.append(f'<span class="clinical-tag tag-allergy">{a_name}</span>')
                    render_clean_html(f"<div>{''.join(allergy_tags)}</div>")
                else:
                    st.caption("No information available.")

                st.markdown("<div style='margin-top: 0.75rem;'></div>", unsafe_allow_html=True)

                # Current Medications
                render_clean_html("<div style='font-size: 0.78rem; font-weight: 700; color: #64748B; text-transform: uppercase; margin-bottom: 0.35rem;'>Current Medications</div>")
                if meds:
                    med_data = []
                    for m in meds:
                        med_data.append({
                            "Medicine Name": m.get("medicine_name", "N/A"),
                            "Dosage": m.get("prescribed_dosage") or m.get("strength") or "As Prescribed",
                            "Frequency": m.get("frequency", "Daily")
                        })
                    med_df = pd.DataFrame(med_data)
                    st.dataframe(med_df, use_container_width=True, hide_index=True)
                else:
                    st.caption("No information available.")

            # -----------------------------------------------------------------
            # RECENT ACTIVITY (Real data from SQLite)
            # -----------------------------------------------------------------
            st.markdown("<div style='margin-top: 1.25rem;'></div>", unsafe_allow_html=True)
            render_clean_html("""
<div style="font-size: 0.82rem; font-weight: 800; color: #0F172A; letter-spacing: 0.04em; text-transform: uppercase; margin-bottom: 0.5rem;">
    RECENT ACTIVITY
</div>
""")

            if assessments:
                latest_ast = assessments[0]
                ast_date = latest_ast.get("created_at", "Recently")[:16]
                ast_level = latest_ast.get("risk_level", "Assessed")
                ast_score = latest_ast.get("risk_score", 0.0)

                level_color = "#10B981" if "LOW" in str(ast_level).upper() else "#F59E0B" if "MED" in str(ast_level).upper() else "#EF4444"

                render_clean_html(f"""
<div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-left: 4px solid {level_color}; border-radius: 10px; padding: 0.75rem 1rem;">
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <span style="font-weight: 700; color: #0F172A; font-size: 0.88rem;">Risk Assessment Completed</span>
        <span style="font-size: 0.75rem; color: #64748B;">{ast_date}</span>
    </div>
    <div style="font-size: 0.82rem; color: #475569; margin-top: 4px;">
        Evaluated as <strong style="color: {level_color};">{ast_level}</strong> (Score: {ast_score:.1f})
    </div>
</div>
""")
            else:
                st.caption("No recent activity available.")

        else:
            # Empty State for User with No Linked Patient Record
            render_clean_html("""
<div class="profile-card-box" style="text-align: center; padding: 2.25rem 1.5rem;">
    <div style="font-size: 2.2rem; margin-bottom: 0.5rem;">📋</div>
    <div style="font-size: 1.1rem; font-weight: 800; color: #0F172A; margin-bottom: 0.35rem;">
        No Patient Profile Created Yet
    </div>
    <p style="color: #64748B; font-size: 0.88rem; max-width: 380px; margin: 0 auto 1.25rem auto;">
        No patient information has been added yet. Add your clinical profile to enable automated risk prediction and AI safety intelligence.
    </p>
</div>
""")
            if st.button("ADD PATIENT INFORMATION", type="primary", use_container_width=True):
                st.session_state.current_page = "patient_info"
                st.session_state.process_step = 1
                st.rerun()

    # -------------------------------------------------------------------------
    # 3. QUICK ACTIONS
    # -------------------------------------------------------------------------
    st.divider()
    render_clean_html("""
<div style="font-size: 0.82rem; font-weight: 800; color: #2563EB; letter-spacing: 0.06em; text-transform: uppercase; margin-bottom: 0.75rem;">
    QUICK ACTIONS
</div>
""")

    qa1, qa2, qa3, qa4 = st.columns(4)
    with qa1:
        if st.button("UPDATE PATIENT DATA", key="qa_update_patient", use_container_width=True):
            st.session_state.current_page = "patient_info"
            st.session_state.process_step = 1
            st.rerun()
    with qa2:
        if st.button("VIEW RISK ANALYSIS", key="qa_view_risk", use_container_width=True):
            st.session_state.current_page = "risk_prediction"
            st.session_state.process_step = 2
            st.rerun()
    with qa3:
        if st.button("AI RECOMMENDATIONS", key="qa_ai_recs", use_container_width=True):
            st.session_state.current_page = "ai_analysis"
            st.session_state.process_step = 3
            st.rerun()
    with qa4:
        if st.button("FIND NEARBY HOSPITALS", key="qa_nearby_hosp", use_container_width=True):
            st.session_state.current_page = "nearby_hospitals"
            st.session_state.process_step = 4
            st.rerun()

    # -------------------------------------------------------------------------
    # 4. OPTIONAL FACULTY / EVALUATOR DATABASE INSPECTOR (Clean & Collapsed)
    # -------------------------------------------------------------------------
    st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)
    with st.expander("🗄️ Faculty & Evaluator Database Inspector (Optional)", expanded=False):
        st.caption("Inspect live SQLite database tables (`data/medisafe.db`) for evaluation verification.")
        import sqlite3

        AVAILABLE_TABLES = [
            ("👤 Users", "users"),
            ("📋 Patients", "patients"),
            ("💊 Medications", "medications"),
            ("🩺 Medical Conditions", "medical_conditions"),
            ("⚠️ Allergies", "allergies"),
            ("⚡ Risk Assessments", "risk_assessments"),
            ("💡 Recommendations", "recommendations")
        ]

        table_dict = {lbl: tbl for lbl, tbl in AVAILABLE_TABLES}
        sel_lbl = st.selectbox("Select Table:", options=[lbl for lbl, _ in AVAILABLE_TABLES], key="prof_db_inspect")
        sel_tbl = table_dict[sel_lbl]

        try:
            conn = sqlite3.connect(DB_PATH)
            df = pd.read_sql_query(f"SELECT * FROM {sel_tbl} ORDER BY 1 DESC LIMIT 50", conn)
            conn.close()

            if "password_hash" in df.columns:
                df["password_hash"] = df["password_hash"].apply(lambda h: f"{h[:8]}... (Hashed)" if h else "")

            st.dataframe(df, use_container_width=True, hide_index=True)
            st.caption(f"Showing up to 50 records from table `{sel_tbl}`")
        except Exception as err:
            st.error(f"Unable to read table: {err}")


