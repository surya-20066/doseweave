"""
DOSEWEAVE
AI-Powered Medication Safety, Risk Prediction, Food Interaction and Emergency Support System
Main Application Router and Layout Controller
"""

import os
import streamlit as st
from dotenv import load_dotenv

# Load environment variables once
load_dotenv()

# Streamlit Page Configuration - collapsed sidebar
st.set_page_config(
    page_title="DoseWeave — Medication Safety & Healthcare Support",
    page_icon="✚",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# High-Performance Cached CSS Loading
@st.cache_data(show_spinner=False)
def load_cached_css() -> str:
    css_path = os.path.join(os.path.dirname(__file__), "styles", "main.css")
    if os.path.exists(css_path):
        with open(css_path, "r", encoding="utf-8") as f:
            return f.read()
    return ""

css_content = load_cached_css()
if css_content:
    st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)

# High-Performance Cached Database & Reminder Worker Initialization (runs once per process)
from database.database import init_db
from services.reminder_service import reminder_service

@st.cache_resource(show_spinner=False)
def ensure_core_services_ready():
    init_db()
    reminder_service.start_background_worker()
    return True

ensure_core_services_ready()

# Import Navigation Component (Top Navigation Bar)
from components.top_nav import render_top_nav

# Import Clinical Flow Page Renderers
from pages.landing_page import render_landing_page
from pages.auth import render_auth_page
from pages.process_flow import render_process_flow
from pages.user_profile import render_user_profile
from pages.patient_info import render_patient_info
from pages.risk_prediction import render_risk_prediction
from pages.ai_reminder import render_ai_reminder
from pages.ai_analysis import render_ai_analysis
from pages.nearby_hospitals import render_nearby_hospitals
from pages.dashboard import render_dashboard
from pages.admin_dashboard import render_admin_dashboard

def main():
    # Session state initialization
    if "user" not in st.session_state:
        st.session_state.user = None

    if "current_page" not in st.session_state:
        st.session_state.current_page = "home"

    # Strict authorization rules:
    # Before login: only 'home' and 'login' allowed.
    # If visitor tries to access protected features, redirect to login.
    PROTECTED_PAGES = {"process", "dashboard", "patient_info", "risk_prediction", "ai_reminder", "ai_analysis", "nearby_hospitals", "profile", "admin"}
    if st.session_state.current_page in PROTECTED_PAGES and not st.session_state.user:
        st.session_state.current_page = "login"
        st.info("🔒 Please log in to access the clinical process and patient safety records.")

    # Strict role-based guard for admin portal
    if st.session_state.current_page == "admin":
        user = st.session_state.get("user")
        if not user or user.get("role") != "admin":
            st.session_state.current_page = "home"
            st.error("⛔ Unauthorized: Administrator privileges required.")

    # Render Professional Top Navigation Bar
    render_top_nav()

    # Route mapping
    PAGE_ROUTING = {
        "home": render_landing_page,
        "login": render_auth_page,
        "process": render_process_flow,
        "dashboard": render_dashboard,
        "profile": render_user_profile,
        "patient_info": render_patient_info,
        "risk_prediction": render_risk_prediction,
        "ai_reminder": render_ai_reminder,
        "ai_analysis": render_ai_reminder,  # Seamless backward compatibility
        "nearby_hospitals": render_nearby_hospitals,
        "admin": render_admin_dashboard,
    }

    current_page = st.session_state.get("current_page", "home")
    renderer = PAGE_ROUTING.get(current_page, render_landing_page)

    try:
        renderer()
    except Exception as e:
        import traceback
        traceback.print_exc()
        st.error(f"An unexpected error occurred while loading this view: {str(e)}")
        st.info("You can return to the Home page using the navigation bar.")

if __name__ == "__main__":
    main()
