"""
MediSafe AI - Professional Home / Landing Page
Introduces the platform, its key capabilities, architecture,
and displays the 4-Step Clinical Process with accessible, high-contrast buttons.
"""

import streamlit as st

def render_landing_page():
    user = st.session_state.get("user")

    # -------------------------------------------------------------------------
    # 1. HERO & INTRODUCTORY SECTION
    # -------------------------------------------------------------------------
    st.markdown("""
        <div style="text-align: center; max-width: 900px; margin: 0 auto; padding: 1.5rem 1rem 1rem 1rem;">
            <div class="hero-tag">
                <span class="pulse-dot"></span>
                CLINICAL MEDICATION SAFETY & HEALTHCARE SUPPORT SYSTEM
            </div>
            <h1 class="hero-title">
                MEDISAFE AI
            </h1>
            <div class="hero-subtitle">
                "Your Smart Medication Safety and Healthcare Support Assistant"
            </div>
            <p class="hero-desc">
                MediSafe AI helps users organize health information, analyze medication-related risk, ask healthcare-related questions using text or images, receive safety-oriented recommendations, and find nearby healthcare facilities.
            </p>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # 2. WHAT IS MEDISAFE AI & CORE CAPABILITIES
    # -------------------------------------------------------------------------
    st.markdown("""
        <div class="clean-card section-reveal" style="padding: 2rem 2.25rem; margin-bottom: 2.5rem;">
            <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 24px;">
                <div>
                    <div style="font-size: 0.72rem; font-weight: 800; color: #2563EB; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.4rem;">
                        ABOUT THE PLATFORM
                    </div>
                    <div style="font-size: 1.25rem; font-weight: 800; color: #0F172A; margin-bottom: 0.6rem;">
                        What is MediSafe AI?
                    </div>
                    <div style="font-size: 0.88rem; color: #64748B; line-height: 1.6;">
                        MediSafe AI is a specialized clinical decision-support and medication safety platform. It pairs calibrated Machine Learning models with medical safety knowledge bases to evaluate multi-drug regimens and detect potential adverse drug events before they happen.
                    </div>
                </div>
                <div>
                    <div style="font-size: 0.72rem; font-weight: 800; color: #0D9488; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.4rem;">
                        CLINICAL CAPABILITIES
                    </div>
                    <div style="font-size: 1.25rem; font-weight: 800; color: #0F172A; margin-bottom: 0.6rem;">
                        What does MediSafe AI do?
                    </div>
                    <div style="font-size: 0.88rem; color: #64748B; line-height: 1.6;">
                        It audits active prescriptions against food and beverage intake, cross-references chronic health conditions and allergies, calculates personalized risk scores, answers clinical questions via multimodal OCR and AI, and locates nearby emergency facilities.
                    </div>
                </div>
                <div>
                    <div style="font-size: 0.72rem; font-weight: 800; color: #4F46E5; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.4rem;">
                        SYSTEM ARCHITECTURE
                    </div>
                    <div style="font-size: 1.25rem; font-weight: 800; color: #0F172A; margin-bottom: 0.6rem;">
                        How does the system work?
                    </div>
                    <div style="font-size: 0.88rem; color: #64748B; line-height: 1.6;">
                        Operating on a 4-step clinical flow, user inputs are stored in an encrypted SQLite database, fed into an offline-trained Machine Learning risk engine, enriched through Gemini AI safety guidelines, and mapped via real-time geospatial emergency dispatch.
                    </div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # 3. COMPLETE PROCESS OVERVIEW (4 STEPS VISUAL)
    # -------------------------------------------------------------------------
    st.markdown("""
        <div class="section-reveal" style="text-align: center; margin-bottom: 1.85rem;">
            <div style="font-size: 0.74rem; font-weight: 800; color: #2563EB; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.35rem;">
                CLINICAL DECISION SUPPORT
            </div>
            <h2 style="font-size: 2.1rem; font-weight: 800; color: #0F172A !important; letter-spacing: -0.025em;">
                How the 4-Step Process Works
            </h2>
            <p style="color: #64748B; font-size: 0.95rem; max-width: 600px; margin: 0 auto;">
                A continuous, guided workflow designed for patients, clinical caregivers, and healthcare evaluators.
            </p>
        </div>
    """, unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.markdown("""
            <div class="clean-card step-card step-card-1" style="height: 100%; border-top: 4px solid #2563EB; padding: 1.25rem;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem;">
                    <span class="floating-icon" style="font-size: 1.8rem;">👤</span>
                    <span style="background: #EFF6FF; color: #2563EB; font-weight: 800; font-size: 0.75rem; padding: 3px 8px; border-radius: 9999px; border: 1px solid #DBEAFE;">STEP 1</span>
                </div>
                <div style="font-size: 1.05rem; font-weight: 800; color: #0F172A; margin-bottom: 0.45rem;">COLLECT USER DATA</div>
                <div style="font-size: 0.85rem; color: #64748B; line-height: 1.55;">
                    Enter and securely store patient information, medication details, food information, allergies and symptoms.
                </div>
            </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown("""
            <div class="clean-card step-card step-card-2" style="height: 100%; border-top: 4px solid #4F46E5; padding: 1.25rem;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem;">
                    <span class="floating-icon-delayed" style="font-size: 1.8rem;">⚡</span>
                    <span style="background: #EEF2FF; color: #4F46E5; font-weight: 800; font-size: 0.75rem; padding: 3px 8px; border-radius: 9999px; border: 1px solid #C7D2FE;">STEP 2</span>
                </div>
                <div style="font-size: 1.05rem; font-weight: 800; color: #0F172A; margin-bottom: 0.45rem;">ANALYSE THE RISK</div>
                <div style="font-size: 0.85rem; color: #64748B; line-height: 1.55;">
                    Use the trained machine learning model to analyse medication-related risk.
                </div>
            </div>
        """, unsafe_allow_html=True)

    with c3:
        st.markdown("""
            <div class="clean-card step-card step-card-3" style="height: 100%; border-top: 4px solid #0D9488; padding: 1.25rem;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem;">
                    <span class="floating-icon" style="font-size: 1.8rem;">🤖</span>
                    <span style="background: #CCFBF1; color: #0F766E; font-weight: 800; font-size: 0.75rem; padding: 3px 8px; border-radius: 9999px; border: 1px solid #99F6E4;">STEP 3</span>
                </div>
                <div style="font-size: 1.05rem; font-weight: 800; color: #0F172A; margin-bottom: 0.45rem;">AI RECOMMENDATION SYSTEM</div>
                <div style="font-size: 0.85rem; color: #64748B; line-height: 1.55;">
                    Ask questions using text or upload an image such as a prescription or medicine label for AI-assisted analysis and safety-oriented recommendations.
                </div>
            </div>
        """, unsafe_allow_html=True)

    with c4:
        st.markdown("""
            <div class="clean-card step-card step-card-4" style="height: 100%; border-top: 4px solid #10B981; padding: 1.25rem;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem;">
                    <span class="floating-icon-delayed" style="font-size: 1.8rem;">🏥</span>
                    <span style="background: #ECFDF5; color: #047857; font-weight: 800; font-size: 0.75rem; padding: 3px 8px; border-radius: 9999px; border: 1px solid #A7F3D0;">STEP 4</span>
                </div>
                <div style="font-size: 1.05rem; font-weight: 800; color: #0F172A; margin-bottom: 0.45rem;">NEARBY HEALTHCARE LOCATIONS</div>
                <div style="font-size: 0.85rem; color: #64748B; line-height: 1.55;">
                    Search for nearby hospitals and healthcare facilities using your current or manually entered location.
                </div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='margin-top: 2.5rem;'></div>", unsafe_allow_html=True)
    st.markdown("""
        <div class="clean-card section-reveal" style="padding: 1.25rem 1.75rem; text-align: center;">
            <div style="font-size: 0.85rem; color: #64748B; line-height: 1.5;">
                <strong>Clinical Decision Support Notice:</strong> MediSafe AI provides automated risk screening, pharmacological knowledge retrieval, and emergency locator guidance for educational and research evaluation. Always verify findings with qualified healthcare professionals.
            </div>
        </div>
    """, unsafe_allow_html=True)
