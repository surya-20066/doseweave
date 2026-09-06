"""
MediSafe AI - Professional Top Navigation Bar
Replaces the left sidebar navigation with a clean, responsive, stateful, and executive top navbar.

States:
1. Visitor (Unauthenticated):
   [ ✚ MEDISAFE AI ] --------- [ HOME ] [ LOGIN ] [ SIGN UP ]
2. Authenticated:
   [ ✚ MEDISAFE AI ] --------- [ HOME ] [ PROCESS ] [ PROFILE ] [ LOGOUT ]
   + Active Clinical User Avatar & Session Pill
"""

import streamlit as st
from utils.constants import APP_NAME

def render_top_nav():
    user = st.session_state.get("user")
    current_page = st.session_state.get("current_page", "home")

    # Map current_page to active top navbar button
    process_pages = {"process", "patient_info", "risk_prediction", "ai_analysis", "nearby_hospitals", "dashboard"}

    if not user:
        # VISITOR TOP NAVBAR
        c_logo, c_nav = st.columns([2.1, 1.15])
        with c_logo:
            st.markdown(f"""
                <div style="display: flex; align-items: center; gap: 12px; padding: 0.35rem 0;">
                    <div class="brand-logo-icon" style="background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%); color: white; width: 42px; height: 42px; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 1.45rem; box-shadow: 0 4px 12px rgba(37, 99, 235, 0.28);">
                        ✚
                    </div>
                    <div>
                        <div style="font-weight: 800; font-size: 1.35rem; color: #0F172A; letter-spacing: -0.025em; line-height: 1.1;">{APP_NAME}</div>
                        <div style="font-size: 0.70rem; color: #2563EB; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em;">Clinical Safety Intelligence</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

        with c_nav:
            if current_page == "home":
                btn_col1, btn_col2 = st.columns([1, 1.15])
                with btn_col1:
                    if st.button("LOGIN", key="topnav_login_btn", use_container_width=True):
                        st.session_state.auth_tab = "Login"
                        st.session_state.current_page = "login"
                        st.rerun()
                with btn_col2:
                    if st.button("SIGN UP →", key="topnav_signup_btn", use_container_width=True, type="primary"):
                        st.session_state.auth_tab = "Sign Up"
                        st.session_state.current_page = "login"
                        st.rerun()
            else:
                btn_col1, btn_col2, btn_col3 = st.columns([1.1, 1, 1])
                with btn_col1:
                    if st.button("← HOME", key="topnav_home_btn", use_container_width=True):
                        st.session_state.current_page = "home"
                        st.rerun()
                with btn_col2:
                    is_login = (st.session_state.get("auth_tab") != "Sign Up")
                    if st.button("LOGIN", key="topnav_login_btn", use_container_width=True, type="primary" if is_login else "secondary"):
                        st.session_state.auth_tab = "Login"
                        st.session_state.current_page = "login"
                        st.rerun()
                with btn_col3:
                    is_signup = (st.session_state.get("auth_tab") == "Sign Up")
                    if st.button("SIGN UP", key="topnav_signup_btn", use_container_width=True, type="primary" if is_signup else "secondary"):
                        st.session_state.auth_tab = "Sign Up"
                        st.session_state.current_page = "login"
                        st.rerun()

    else:
        # AUTHENTICATED TOP NAVBAR - ELEVATED EXECUTIVE CLINICAL SUITE
        user_name = user.get("full_name", "Clinical User")
        initial = user_name[0].upper() if user_name else "U"

        c_brand, c_user, c_nav = st.columns([1.2, 1.1, 2.1])

        with c_brand:
            st.markdown(f"""
                <div style="display: flex; align-items: center; gap: 12px; padding: 0.2rem 0;">
                    <div class="brand-logo-icon" style="background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%); color: white; width: 42px; height: 42px; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 1.45rem; box-shadow: 0 4px 12px rgba(37, 99, 235, 0.28);">
                        ✚
                    </div>
                    <div>
                        <div style="font-weight: 800; font-size: 1.35rem; color: #0F172A; letter-spacing: -0.025em; line-height: 1.1;">{APP_NAME}</div>
                        <div style="font-size: 0.70rem; color: #059669; font-weight: 800; text-transform: uppercase; letter-spacing: 0.05em; display: flex; align-items: center; gap: 4px;">
                            <span class="pulse-dot"></span> Active Session
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

        with c_user:
            st.markdown(f"""
                <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 12px; padding: 0.4rem 0.85rem; display: flex; align-items: center; gap: 10px;">
                    <div style="background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%); color: white; width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 0.90rem; flex-shrink: 0;">
                        {initial}
                    </div>
                    <div style="overflow: hidden; flex: 1;">
                        <div style="font-weight: 800; color: #0F172A; font-size: 0.84rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{user_name}</div>
                        <div style="font-size: 0.70rem; color: #64748B;">Clinical Account</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

        with c_nav:
            btn_col1, btn_col2, btn_col3, btn_col4 = st.columns([1, 1.1, 1, 0.9])
            with btn_col1:
                is_home = (current_page == "home")
                if st.button("HOME", key="topnav_home_auth", use_container_width=True, type="primary" if is_home else "secondary"):
                    st.session_state.current_page = "home"
                    st.rerun()
            with btn_col2:
                is_process = (current_page in process_pages)
                if st.button("PROCESS", key="topnav_process_auth", use_container_width=True, type="primary" if is_process else "secondary"):
                    st.session_state.current_page = "process"
                    st.rerun()
            with btn_col3:
                is_profile = (current_page == "profile")
                if st.button("PROFILE", key="topnav_profile_auth", use_container_width=True, type="primary" if is_profile else "secondary"):
                    st.session_state.current_page = "profile"
                    st.rerun()
            with btn_col4:
                if st.button("LOGOUT", key="topnav_logout_auth", use_container_width=True):
                    st.session_state.clear()
                    st.session_state.current_page = "home"
                    st.rerun()

    st.markdown("<div style='margin-bottom: 0.75rem;'></div>", unsafe_allow_html=True)
