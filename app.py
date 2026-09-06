"""
MEDISAFE AI
AI-Powered Medication Safety, Risk Prediction, Food Interaction and Emergency Support System
Main Application Router and Layout Controller
"""

import os
import streamlit as st
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Streamlit Page Configuration
# Streamlit Page Configuration - collapsed sidebar
st.set_page_config(
    page_title="MediSafe AI — Medication Safety & Healthcare Support",
    page_icon="✚",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Load and inject custom CSS styling
CSS_PATH = os.path.join(os.path.dirname(__file__), "styles", "main.css")
if os.path.exists(CSS_PATH):
    with open(CSS_PATH, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Initialize Database on boot
from database.database import init_db
init_db()

# Import Navigation Component (Top Navigation Bar)
from components.top_nav import render_top_nav

# Import Clinical Flow Page Renderers
from pages.landing_page import render_landing_page
from pages.auth import render_auth_page
from pages.process_flow import render_process_flow
from pages.user_profile import render_user_profile
from pages.patient_info import render_patient_info
from pages.risk_prediction import render_risk_prediction
from pages.ai_analysis import render_ai_analysis
from pages.nearby_hospitals import render_nearby_hospitals
from pages.dashboard import render_dashboard

def main():
    # Session state initialization
    if "user" not in st.session_state:
        st.session_state.user = None

    if "current_page" not in st.session_state:
        st.session_state.current_page = "home"

    # Strict authorization rules:
    # Before login: only 'home' and 'login' allowed.
    # If visitor tries to access protected features, redirect to login.
    PROTECTED_PAGES = {"process", "dashboard", "patient_info", "risk_prediction", "ai_analysis", "nearby_hospitals", "profile"}
    if st.session_state.current_page in PROTECTED_PAGES and not st.session_state.user:
        st.session_state.current_page = "login"
        st.info("🔒 Please log in to access the clinical process and patient safety records.")

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
        "ai_analysis": render_ai_analysis,
        "nearby_hospitals": render_nearby_hospitals,
    }

    current_page = st.session_state.get("current_page", "home")
    renderer = PAGE_ROUTING.get(current_page, render_landing_page)

    try:
        renderer()
    except Exception as e:
        st.error(f"An unexpected error occurred while loading this view: {str(e)}")
        st.info("You can return to the Home page using the navigation bar.")

if __name__ == "__main__":
    main()
