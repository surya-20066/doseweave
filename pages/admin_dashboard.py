"""
DoseWeave - Protected Administrative & Faculty Evaluation Dashboard
Accessible strictly by authenticated administrative accounts (role == 'admin').
Provides system health monitoring, live database inspection, reminder daemon status,
and aggregated clinical intelligence metrics.
"""

import streamlit as st
import pandas as pd
import sqlite3
import os
from database.database import (
    get_admin_system_stats, get_table_data_paginated,
    get_table_schema_info, get_audit_logs, DB_PATH
)
from models.predict import risk_predictor
from services.gemini_service import gemini_service
from services.reminder_service import reminder_service
from components.header import render_header

def render_admin_dashboard():
    user = st.session_state.get("user")
    
    # Strict role-based access control
    if not user or user.get("role") != "admin":
        st.error("⛔ ACCESS DENIED: Administrator privileges required.")
        st.info("Please log in with an administrator account (e.g. `admin@doseweave.ai`).")
        if st.button("← Return to Home", type="primary"):
            st.session_state.current_page = "home"
            st.rerun()
        return

    render_header(
        title="SYSTEM ADMINISTRATION & EVALUATION DASHBOARD",
        subtitle="Restricted clinical oversight portal: system health diagnostics, live SQLite inspection, and reminder telemetry",
        breadcrumb="DoseWeave > Admin"
    )

    stats = get_admin_system_stats()

    # 1. System Telemetry Metric Cards
    st.markdown("### 📊 System Health & Registry Metrics")
    m_c1, m_c2, m_c3, m_c4 = st.columns(4)
    with m_c1:
        st.metric("Total User Accounts", stats.get("total_users", 0))
        st.metric("Patient Records", stats.get("total_patients", 0))
    with m_c2:
        st.metric("Active Medications", stats.get("total_medications", 0))
        st.metric("Generated Schedules", stats.get("total_schedules", 0))
    with m_c3:
        st.metric("Scheduled Doses", stats.get("total_scheduled_doses", 0))
        st.metric("Adherence Records", stats.get("total_adherence_records", 0))
    with m_c4:
        st.metric("Clinical Risk Evals", stats.get("total_assessments", 0))
        st.metric("Dispatched Alerts", stats.get("notifications_sent", 0))

    st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)

    # 2. Subsystem Diagnostics & Service Health
    st.markdown("### 🩺 Subsystem Operational Diagnostics")
    diag_c1, diag_c2, diag_c3, diag_c4 = st.columns(4)

    # Machine Learning Pipeline
    ml_ready = risk_predictor.is_ready()
    with diag_c1:
        ml_badge = "background: #ECFDF5; color: #047857; border: 1px solid #A7F3D0;" if ml_ready else "background: #FEF2F2; color: #DC2626; border: 1px solid #F87171;"
        st.markdown(f"""
            <div style="background: white; border: 1px solid #E2E8F0; border-radius: 10px; padding: 1.1rem; text-align: center;">
                <div style="font-size: 0.74rem; font-weight: 800; color: #64748B; text-transform: uppercase;">ML MODEL ARTIFACTS</div>
                <div style="margin: 0.5rem 0;">
                    <span style="{ml_badge} font-weight: 800; font-size: 0.82rem; padding: 4px 10px; border-radius: 9999px;">
                        {'ONLINE (96.6% Acc)' if ml_ready else 'OFFLINE'}
                    </span>
                </div>
                <div style="font-size: 0.78rem; color: #64748B;">RandomForest / CalibratedProb</div>
            </div>
        """, unsafe_allow_html=True)

    # Reminder Worker Daemon
    worker_on = reminder_service._worker_running
    with diag_c2:
        w_badge = "background: #ECFDF5; color: #047857; border: 1px solid #A7F3D0;" if worker_on else "background: #FFFBEB; color: #B45309; border: 1px solid #FDE68A;"
        st.markdown(f"""
            <div style="background: white; border: 1px solid #E2E8F0; border-radius: 10px; padding: 1.1rem; text-align: center;">
                <div style="font-size: 0.74rem; font-weight: 800; color: #64748B; text-transform: uppercase;">REMINDER DAEMON</div>
                <div style="margin: 0.5rem 0;">
                    <span style="{w_badge} font-weight: 800; font-size: 0.82rem; padding: 4px 10px; border-radius: 9999px;">
                        {'ACTIVE (30s Tick)' if worker_on else 'STANDBY'}
                    </span>
                </div>
                <div style="font-size: 0.78rem; color: #64748B;">Background Thread Worker</div>
            </div>
        """, unsafe_allow_html=True)

    # SQLite Database WAL Engine
    with diag_c3:
        st.markdown(f"""
            <div style="background: white; border: 1px solid #E2E8F0; border-radius: 10px; padding: 1.1rem; text-align: center;">
                <div style="font-size: 0.74rem; font-weight: 800; color: #64748B; text-transform: uppercase;">DATABASE ENGINE</div>
                <div style="margin: 0.5rem 0;">
                    <span style="background: #EFF6FF; color: #1D4ED8; border: 1px solid #BFDBFE; font-weight: 800; font-size: 0.82rem; padding: 4px 10px; border-radius: 9999px;">
                        SQLITE 3 (WAL MODE)
                    </span>
                </div>
                <div style="font-size: 0.78rem; color: #64748B;">Synchronous: NORMAL</div>
            </div>
        """, unsafe_allow_html=True)

    # Gemini Multimodal OCR
    gemini_on = gemini_service.is_available()
    with diag_c4:
        g_badge = "background: #ECFDF5; color: #047857; border: 1px solid #A7F3D0;" if gemini_on else "background: #FFFBEB; color: #B45309; border: 1px solid #FDE68A;"
        st.markdown(f"""
            <div style="background: white; border: 1px solid #E2E8F0; border-radius: 10px; padding: 1.1rem; text-align: center;">
                <div style="font-size: 0.74rem; font-weight: 800; color: #64748B; text-transform: uppercase;">MULTIMODAL VISION</div>
                <div style="margin: 0.5rem 0;">
                    <span style="{g_badge} font-weight: 800; font-size: 0.82rem; padding: 4px 10px; border-radius: 9999px;">
                        {'CONFIGURED' if gemini_on else 'LOCAL FALLBACK'}
                    </span>
                </div>
                <div style="font-size: 0.78rem; color: #64748B;">Gemini 3.6 Flash / Local OCR</div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='margin-top: 2rem;'></div>", unsafe_allow_html=True)

    # 3. Live SQLite Database Inspector (Paginated, Masked, Searchable)
    st.markdown("### 🗄️ Faculty & Evaluator Database Inspector")
    st.caption("Inspect live tables, schemas, and records from `data/doseweave.db`. Sensitive fields (such as password hashes) are securely masked.")

    AVAILABLE_TABLES = [
        ("👤 Users", "users"),
        ("📋 Patients", "patients"),
        ("💊 Medications", "medications"),
        ("📅 Medication Schedules", "medication_schedules"),
        ("⏰ Scheduled Doses", "scheduled_doses"),
        ("📊 Adherence Records", "medication_adherence"),
        ("🔔 Reminder Preferences", "reminder_preferences"),
        ("📤 Reminder Notifications", "reminder_notifications"),
        ("📷 Medicine Recognition History", "medicine_recognition_history"),
        ("📋 Prescription Records", "prescription_records"),
        ("⚡ Risk Assessments", "risk_assessments"),
        ("⚠️ Allergies", "allergies"),
        ("🩺 Medical Conditions", "medical_conditions"),
        ("🥗 Food Entries", "food_entries"),
        ("🛡️ Audit Logs", "audit_logs"),
        ("📖 Drug Info Cache", "drug_information_cache")
    ]

    tbl_dict = {lbl: tbl for lbl, tbl in AVAILABLE_TABLES}
    sel_label = st.selectbox("Select Database Table to Inspect:", options=[lbl for lbl, _ in AVAILABLE_TABLES], key="admin_db_select")
    target_table = tbl_dict[sel_label]

    # Show Table Schema Details
    schema_info = get_table_schema_info(target_table)
    with st.expander(f"📐 View Schema Definition for `{target_table}` ({len(schema_info)} columns)"):
        schema_df = pd.DataFrame(schema_info)[["cid", "name", "type", "notnull", "dflt_value", "pk"]]
        st.dataframe(schema_df, use_container_width=True, hide_index=True)

    # Fetch Table Records
    rows, total_records = get_table_data_paginated(target_table, limit=50, offset=0)
    st.markdown(f"**Records in `{target_table}`:** Showing {len(rows)} of {total_records} total entries")

    if rows:
        df_display = pd.DataFrame(rows)
        # Mask sensitive columns
        if "password_hash" in df_display.columns:
            df_display["password_hash"] = df_display["password_hash"].apply(
                lambda h: f"{str(h)[:8]}... [SHA-256 MASKED]" if h else ""
            )
        st.dataframe(df_display, use_container_width=True, hide_index=True)
    else:
        st.info(f"Table `{target_table}` is currently empty.")

    # 4. Recent System Audit Trail
    st.markdown("<div style='margin-top: 2rem;'></div>", unsafe_allow_html=True)
    st.markdown("### 🛡️ System Audit Trail")
    audit_logs = get_audit_logs(limit=25)
    if audit_logs:
        df_audit = pd.DataFrame(audit_logs)[["id", "created_at", "user_id", "action", "entity_type", "entity_id", "details"]]
        st.dataframe(df_audit, use_container_width=True, hide_index=True)
    else:
        st.info("No security or adherence audit events logged yet.")
