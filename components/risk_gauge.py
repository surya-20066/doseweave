"""
MediSafe AI - Risk Gauge Visualization Component
Renders an interactive Plotly clinical speedometer gauge.
"""

import plotly.graph_objects as go
import streamlit as st

def render_risk_gauge(score: float, risk_level: str, confidence: float = None, suffix: str = "%"):
    """
    Renders a Plotly Indicator Gauge showing normalized risk score (0-100).
    """
    bar_color = "#16A34A" if score <= 33 else ("#D97706" if score <= 66 else "#DC2626")

    title_text = f"<b>{risk_level}</b>"
    if confidence is not None:
        try:
            c_val = float(confidence)
            title_text += f"<br><span style='font-size:0.75em;color:#64748B;'>Model Confidence: {c_val:.1f}%</span>"
        except (ValueError, TypeError):
            title_text += f"<br><span style='font-size:0.75em;color:#64748B;'>Model Confidence: {confidence}%</span>"

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        number={"suffix": suffix, "font": {"size": 40, "color": "#0F172A", "family": "Arial, sans-serif"}},
        title={"text": title_text, "font": {"size": 19, "color": "#0F2C59", "family": "Arial, sans-serif"}},
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "#94A3B8", "tickvals": [0, 33, 66, 100]},
            "bar": {"color": bar_color, "thickness": 0.28},
            "bgcolor": "white",
            "borderwidth": 1,
            "bordercolor": "#E2E8F0",
            "steps": [
                {"range": [0, 33], "color": "#DCFCE7"},    # Low
                {"range": [33, 66], "color": "#FEF3C7"},   # Moderate
                {"range": [66, 100], "color": "#FEE2E2"}   # High
            ],
            "threshold": {
                "line": {"color": "#B91C1C", "width": 3.5},
                "thickness": 0.85,
                "value": score
            }
        }
    ))

    fig.update_layout(
        height=270,
        margin=dict(l=25, r=25, t=45, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        font={"color": "#0F172A"}
    )

    st.plotly_chart(fig, use_container_width=True)
