"""
DoseWeave - Authentication Interface (Login & Sign-Up)
Secure registration and authentication system with password hashing and session management.
Shows ONLY ONE view at a time (Login OR Sign-Up), toggleable via modern segmented pill buttons.
Redirects to PROCESS upon successful authentication.
"""

import streamlit as st
from database.database import create_user, verify_user

def render_auth_page():
    st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)

    auth_col1, auth_col2, auth_col3 = st.columns([1.2, 1.6, 1.2])

    with auth_col2:
        with st.container(border=True):
            # Portal Header
            st.markdown("""
                <div style="text-align: center; margin-bottom: 1.35rem;">
                    <div class="brand-logo-icon" style="background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%); color: white; width: 48px; height: 48px; border-radius: 14px; display: inline-flex; align-items: center; justify-content: center; font-weight: 800; font-size: 1.6rem; margin-bottom: 0.85rem; box-shadow: 0 4px 14px rgba(37, 99, 235, 0.32);">
                        ✚
                    </div>
                    <h2 style="font-size: 1.95rem; font-weight: 800; color: #0F172A; margin: 0; letter-spacing: -0.03em;">DoseWeave Portal</h2>
                    <p style="color: #64748B; font-size: 0.88rem; margin-top: 0.35rem; margin-bottom: 0.75rem;">Secure Access to Medication Risk & Clinical Safety Intelligence</p>
                    <div style="display: inline-flex; align-items: center; gap: 6px; background: #EFF6FF; border: 1px solid #DBEAFE; color: #2563EB; font-size: 0.72rem; font-weight: 700; padding: 0.25rem 0.75rem; border-radius: 9999px;">
                        <span class="pulse-dot"></span> Clinical Decision Support
                    </div>
                </div>
            """, unsafe_allow_html=True)

            # Segmented Pill Switcher (Single Active Tab)
            active_tab = st.session_state.get("auth_tab", "Login")
            if active_tab not in ("Login", "Sign Up"):
                active_tab = "Login"

            col_t1, col_t2 = st.columns(2)
            with col_t1:
                is_login = (active_tab == "Login")
                if st.button("LOG IN", key="auth_tab_login", use_container_width=True, type="primary" if is_login else "secondary"):
                    st.session_state.auth_tab = "Login"
                    st.rerun()
            with col_t2:
                is_signup = (active_tab == "Sign Up")
                if st.button("CREATE ACCOUNT", key="auth_tab_signup", use_container_width=True, type="primary" if is_signup else "secondary"):
                    st.session_state.auth_tab = "Sign Up"
                    st.rerun()

            st.markdown("<div style='margin-top: 1rem;'></div>", unsafe_allow_html=True)

            # =========================================================================
            # VIEW 1: LOGIN (Shown ONLY when active_tab == "Login")
            # =========================================================================
            if active_tab == "Login":
                st.markdown("""
                    <div style="margin-bottom: 0.85rem;">
                        <div style="font-size: 1.12rem; font-weight: 800; color: #0F172A;">Log in to your account</div>
                        <div style="font-size: 0.84rem; color: #64748B;">Access your medication safety and patient workspace.</div>
                    </div>
                """, unsafe_allow_html=True)

                with st.form("login_form"):
                    email = st.text_input("Email address", placeholder="name@example.com", value="demo@doseweave.ai")
                    password = st.text_input("Password", type="password", placeholder="Enter your password", value="password123")
                    st.markdown("<div style='margin-top: 0.5rem;'></div>", unsafe_allow_html=True)
                    submit_login = st.form_submit_button("LOG IN", use_container_width=True, type="primary")

                if submit_login:
                    if not email.strip() or not password.strip():
                        st.error("Please provide both email and password.")
                    else:
                        user = verify_user(email.strip(), password)
                        if user:
                            st.session_state.user = user
                            st.session_state.user_id = user["user_id"]
                            st.session_state.current_page = "process"
                            st.session_state.process_step = 1
                            st.success(f"Welcome back, {user['full_name']}!")
                            st.rerun()
                        else:
                            st.error("Invalid email or password. Please check credentials or create an account.")

                # Quick demo credentials
                st.markdown("""
                    <div style="background: linear-gradient(135deg, #F0F7FF 0%, #EEF2FF 100%); border: 1px solid #BFDBFE; border-radius: 12px; padding: 0.85rem 1rem; margin-top: 1.25rem;">
                        <div style="font-size: 0.74rem; font-weight: 800; color: #2563EB; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 0.35rem; display: flex; align-items: center; justify-content: center; gap: 6px;">
                            <span>🔑</span> Quick Demo Access Credentials
                        </div>
                        <div style="font-size: 0.82rem; color: #334155; margin-bottom: 0.35rem; text-align: center;">
                            <strong>Patient Portal:</strong> <code style="background: #FFFFFF; border: 1px solid #CBD5E1; padding: 2px 7px; border-radius: 6px; font-weight: 700; color: #1E40AF;">demo@doseweave.ai</code> / <code style="background: #FFFFFF; border: 1px solid #CBD5E1; padding: 2px 7px; border-radius: 6px; font-weight: 700; color: #1E40AF;">password123</code>
                        </div>
                        <div style="font-size: 0.82rem; color: #334155; text-align: center;">
                            <strong>Admin Portal:</strong> <code style="background: #FFFFFF; border: 1px solid #CBD5E1; padding: 2px 7px; border-radius: 6px; font-weight: 700; color: #047857;">admin@doseweave.ai</code> / <code style="background: #FFFFFF; border: 1px solid #CBD5E1; padding: 2px 7px; border-radius: 6px; font-weight: 700; color: #047857;">admin123</code>
                        </div>
                    </div>
                """, unsafe_allow_html=True)

                st.markdown("<div style='margin-top: 1rem;'></div>", unsafe_allow_html=True)
                c_sw1, c_sw2 = st.columns([1.3, 1])
                with c_sw1:
                    st.markdown("<div style='font-size: 0.84rem; color: #64748B; padding-top: 0.5rem;'>Need a new account?</div>", unsafe_allow_html=True)
                with c_sw2:
                    if st.button("Create Account →", key="switch_to_signup", use_container_width=True):
                        st.session_state.auth_tab = "Sign Up"
                        st.rerun()

            # =========================================================================
            # VIEW 2: SIGN UP (Shown ONLY when active_tab == "Sign Up")
            # =========================================================================
            else:
                st.markdown("""
                    <div style="margin-bottom: 0.85rem;">
                        <div style="font-size: 1.12rem; font-weight: 800; color: #0F172A;">Create a new account</div>
                        <div style="font-size: 0.84rem; color: #64748B;">Set up a secure account for your clinical care team.</div>
                    </div>
                """, unsafe_allow_html=True)

                with st.form("signup_form"):
                    full_name = st.text_input("Full name", placeholder="e.g. Sarah Jenkins")
                    reg_email = st.text_input("Email address", placeholder="name@example.com")
                    reg_password = st.text_input("Password", type="password", placeholder="At least 6 characters")
                    confirm_password = st.text_input("Confirm password", type="password", placeholder="Repeat password")
                    st.markdown("<div style='margin-top: 0.5rem;'></div>", unsafe_allow_html=True)
                    submit_signup = st.form_submit_button("CREATE ACCOUNT", use_container_width=True, type="primary")

                if submit_signup:
                    if not full_name.strip() or not reg_email.strip() or not reg_password:
                        st.error("All fields are required.")
                    elif len(reg_password) < 6:
                        st.error("Password must be at least 6 characters long.")
                    elif reg_password != confirm_password:
                        st.error("Passwords do not match.")
                    else:
                        success, msg, user_id = create_user(full_name, reg_email, reg_password)
                        if success:
                            user = verify_user(reg_email, reg_password)
                            st.session_state.user = user
                            st.session_state.user_id = user_id
                            st.session_state.current_page = "process"
                            st.session_state.process_step = 1
                            st.success("Account created successfully!")
                            st.rerun()
                        else:
                            st.error(msg)

                st.markdown("<div style='margin-top: 1rem;'></div>", unsafe_allow_html=True)
                c_sw1, c_sw2 = st.columns([1.3, 1])
                with c_sw1:
                    st.markdown("<div style='font-size: 0.84rem; color: #64748B; padding-top: 0.5rem;'>Already have an account?</div>", unsafe_allow_html=True)
                with c_sw2:
                    if st.button("Log In →", key="switch_to_login", use_container_width=True):
                        st.session_state.auth_tab = "Login"
                        st.rerun()

        # Bottom Trust & Security Badges
        st.markdown("""
            <div style="text-align: center; margin-top: 1.25rem; color: #94A3B8; font-size: 0.74rem; display: flex; align-items: center; justify-content: center; gap: 12px;">
                <span>🔒 256-Bit SSL Encrypted</span>
                <span>•</span>
                <span>🛡️ HIPAA-Conformant</span>
                <span>•</span>
                <span>⚕️ Decision Support Only</span>
            </div>
        """, unsafe_allow_html=True)
