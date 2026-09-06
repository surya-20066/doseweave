"""
MediSafe AI - Metric Cards Component
Renders clean healthcare metric cards with clinical values, accent borders, and status badges.
"""

import streamlit as st

def render_metric_card(label: str, value: str, subtext: str = "", badge_type: str = "default", accent_color: str = "#2563EB", icon: str = "📊"):
    badge_html = ""
    if badge_type == "low":
        badge_html = f'<span class="badge-low">● {value}</span>'
    elif badge_type == "moderate":
        badge_html = f'<span class="badge-moderate">⚠️ {value}</span>'
    elif badge_type == "high":
        badge_html = f'<span class="badge-high">🚨 {value}</span>'
    else:
        badge_html = f'<div class="metric-card-value" style="color: #0F172A;">{value}</div>'

    html = f"""
        <div class="metric-card" style="border-top: 3.5px solid {accent_color};">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.35rem;">
                <span class="metric-card-label">{label}</span>
                <span style="font-size: 1.15rem;">{icon}</span>
            </div>
            <div style="margin: 0.4rem 0;">
                {badge_html}
            </div>
            <div class="metric-card-subtext">{subtext}</div>
        </div>
    """
    st.markdown(html, unsafe_allow_html=True)

def render_metrics_row(
    num_medicines: int,
    num_interactions: int,
    num_food_alerts: int,
    risk_level: str,
    emergency_status: str
):
    c1, c2, c3, c4, c5 = st.columns(5)

    with c1:
        render_metric_card(
            label="Medicines",
            value=str(num_medicines),
            subtext="Active in regimen",
            accent_color="#2563EB",
            icon="💊"
        )

    with c2:
        acc_col = "#EF4444" if num_interactions > 0 else "#10B981"
        render_metric_card(
            label="Interactions",
            value=str(num_interactions),
            subtext="Drug & Condition conflicts",
            accent_color=acc_col,
            icon="⚠️"
        )

    with c3:
        acc_col2 = "#F59E0B" if num_food_alerts > 0 else "#10B981"
        render_metric_card(
            label="Food Alerts",
            value=str(num_food_alerts),
            subtext="Diet & Beverage clashes",
            accent_color=acc_col2,
            icon="🥗"
        )

    with c4:
        badge_map = {
            "LOW RISK": "low",
            "MODERATE RISK": "moderate",
            "HIGH RISK": "high"
        }
        acc_col3 = "#10B981" if risk_level == "LOW RISK" else ("#F59E0B" if risk_level == "MODERATE RISK" else "#EF4444")
        render_metric_card(
            label="ML Risk Level",
            value=risk_level,
            subtext="Probability prediction",
            badge_type=badge_map.get(risk_level, "low"),
            accent_color=acc_col3,
            icon="⚡"
        )

    with c5:
        is_emerg = "ACTIVE ALERT" in emergency_status or "URGENT" in emergency_status
        badge_type = "high" if is_emerg else "low"
        acc_col4 = "#DC2626" if is_emerg else "#10B981"
        render_metric_card(
            label="Emergency Triage",
            value=emergency_status,
            subtext="Acute symptom status",
            badge_type=badge_type,
            accent_color=acc_col4,
            icon="🚨" if is_emerg else "✅"
        )
