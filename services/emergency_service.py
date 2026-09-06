"""
MediSafe AI - Emergency Symptom Triage Service
Detects high-acuity clinical red-flag indicators (e.g. respiratory distress,
chest pain, neurological compromise) and provides rapid escalation protocols.
"""

from typing import List, Dict, Any
from utils.constants import EMERGENCY_SYMPTOMS

class EmergencyService:
    def evaluate_emergency(
        self,
        symptoms: List[Dict[str, Any]],
        risk_level: str = ""
    ) -> Dict[str, Any]:
        """
        Evaluates symptom acuity and returns emergency state with protocols.
        """
        flagged_symptoms = []
        for s in symptoms:
            name = s.get("symptom_name", "")
            severity = s.get("severity", "Mild")
            if name in EMERGENCY_SYMPTOMS or severity == "Severe":
                flagged_symptoms.append(f"{name} ({severity})")

        is_emergency = len(flagged_symptoms) > 0

        emergency_contacts = [
            {"label": "National Emergency Services", "number": "112 (Universal) / 911 / 999"},
            {"label": "Ambulance Direct Hotline", "number": "102 / 911"},
            {"label": "Poison Control Center Hotline", "number": "1-800-222-1222 (US) / National Helpline"}
        ]

        immediate_actions = [
            "Call local emergency medical services immediately or have a bystander call.",
            "Do NOT attempt to operate a vehicle or drive yourself to the emergency department.",
            "Keep all active medication packaging, strips, and prescription sheets ready for emergency paramedics.",
            "Rest in a comfortable, seated or recovery position while waiting for emergency responders.",
            "If experiencing difficulty breathing or chest pain, avoid physical exertion."
        ]

        return {
            "is_emergency": is_emergency,
            "flagged_symptoms": flagged_symptoms,
            "emergency_title": "URGENT MEDICAL ATTENTION RECOMMENDED" if is_emergency else "Standard Clinical Status",
            "immediate_actions": immediate_actions if is_emergency else [],
            "emergency_contacts": emergency_contacts,
            "disclaimer": "Emergency triage indicators are based on acute symptom flags and do not constitute a medical diagnosis."
        }

# Singleton instance
emergency_service = EmergencyService()
