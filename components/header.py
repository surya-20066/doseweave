"""
MediSafe AI - Clinical Header Component
Elevated, modern, high-contrast header matching top-tier healthcare SaaS applications.
"""

import streamlit as st
from database.database import get_patient, get_patient_by_user

def render_header(title: str, subtitle: str, breadcrumb: str = "MediSafe AI", active_step: int = None):
    user = st.session_state.get("user")
    user_id = user.get("user_id", st.session_state.get("user_id")) if user else st.session_state.get("user_id")
    patient = get_patient_by_user(user_id) if user_id else get_patient(st.session_state.get("current_patient_id", 1))
    patient_text = f"👤 <strong>{patient['name']}</strong> &nbsp;|&nbsp; {patient['age']}y • {patient['gender']}" if patient else "👤 <strong>Active Record</strong> &nbsp;|&nbsp; Verified"

    st.markdown(f"""
        <div style="background: linear-gradient(135deg, #FFFFFF 0%, #F8FAFC 100%); border: 1px solid #E2E8F0; border-left: 5px solid #2563EB; border-radius: 16px; padding: 1.35rem 1.85rem; margin-bottom: 1.25rem; box-shadow: 0 4px 16px -2px rgba(0, 0, 0, 0.05); display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 15px;">
            <div>
                <div style="font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.08em; color: #2563EB; font-weight: 800; margin-bottom: 0.25rem; display: flex; align-items: center; gap: 6px;">
                    <span>●</span> {breadcrumb} &nbsp;›&nbsp; {title}
                </div>
                <div style="color: #0F172A; font-size: 1.75rem; font-weight: 800; letter-spacing: -0.025em; line-height: 1.2;">
                    {title}
                </div>
                <div style="color: #64748B; font-size: 0.90rem; margin-top: 0.25rem; font-weight: 500;">
                    {subtitle}
                </div>
            </div>
            <div style="background: #EFF6FF; border: 1px solid #DBEAFE; border-radius: 9999px; padding: 0.45rem 1.1rem; font-size: 0.82rem; color: #1E40AF; font-weight: 700; box-shadow: 0 2px 6px rgba(37, 99, 235, 0.08);">
                {patient_text}
            </div>
        </div>
    """, unsafe_allow_html=True)
