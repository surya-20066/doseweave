"""
MediSafe AI - Explainable Clinical Recommendation Engine
Generates deterministic, rule-based clinical safety alerts and recommendations
across four structured healthcare decision-support tiers:
1. WHAT TO REVIEW
2. WHAT TO AVOID
3. WHAT TO MONITOR
4. WHEN TO CONSULT A HEALTHCARE PROFESSIONAL

STRICT SAFETY POLICY:
- Never prescribes new medicines
- Never alters dosages
- Never advises discontinuation of doctor-prescribed therapy without medical supervision
"""

from typing import List, Dict, Any
from utils.constants import (
    RISK_LEVEL_LOW, RISK_LEVEL_MODERATE, RISK_LEVEL_HIGH
)

class RecommendationService:
    def generate_recommendations(
        self,
        risk_level: str,
        risk_score: float,
        patient: Dict[str, Any],
        medications: List[Dict[str, Any]],
        foods: List[Dict[str, Any]],
        symptoms: List[Dict[str, Any]],
        interaction_data: Dict[str, Any],
        is_emergency: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Synthesizes patient context and outputs prioritized clinical recommendations.
        """
        recommendations = []

        # -------------------------------------------------------------
        # TIER 1: URGENT / WHEN TO CONSULT A HEALTHCARE PROFESSIONAL
        # -------------------------------------------------------------
        if is_emergency:
            recommendations.append({
                "category": "WHEN TO CONSULT A HEALTHCARE PROFESSIONAL",
                "text": "CRITICAL: Severe symptoms detected. Seek emergency medical evaluation or visit the nearest emergency department immediately.",
                "priority": "Critical"
            })
        elif risk_level == RISK_LEVEL_HIGH:
            recommendations.append({
                "category": "WHEN TO CONSULT A HEALTHCARE PROFESSIONAL",
                "text": "High Risk Profile: Schedule a prompt review with your prescribing physician or clinical pharmacist to audit your current regimen.",
                "priority": "High"
            })
        elif risk_level == RISK_LEVEL_MODERATE:
            recommendations.append({
                "category": "WHEN TO CONSULT A HEALTHCARE PROFESSIONAL",
                "text": "Moderate Risk Profile: Mention all identified interactions and symptoms to your doctor or pharmacist during your next consultation.",
                "priority": "Medium"
            })
        else:
            recommendations.append({
                "category": "WHEN TO CONSULT A HEALTHCARE PROFESSIONAL",
                "text": "Low Risk Baseline: Maintain standard annual medication reviews and notify your healthcare team if new symptoms emerge.",
                "priority": "Standard"
            })

        # -------------------------------------------------------------
        # TIER 2: WHAT TO REVIEW (Medications & Dosage Adherence)
        # -------------------------------------------------------------
        if len(medications) >= 4:
            recommendations.append({
                "category": "WHAT TO REVIEW",
                "text": f"Polypharmacy Management: You are actively logging {len(medications)} concurrent medications. Maintain an up-to-date printed medication card for all clinical visits.",
                "priority": "Medium"
            })

        # Dosage discrepancy check
        dosage_deviations = [
            m.get("medicine_name", "") for m in medications
            if m.get("prescribed_dosage", "").strip().lower() != m.get("actual_dosage", "").strip().lower()
            and m.get("prescribed_dosage", "").strip() != ""
        ]
        if dosage_deviations:
            meds_str = ", ".join(dosage_deviations)
            recommendations.append({
                "category": "WHAT TO REVIEW",
                "text": f"Dosage Discrepancy Detected for [{meds_str}]: Verify actual taken dosage against your physician's prescription instructions. Do not self-adjust doses without consultation.",
                "priority": "High"
            })

        # Duplicates check
        duplicates = interaction_data.get("duplicates", [])
        if duplicates:
            recommendations.append({
                "category": "WHAT TO REVIEW",
                "text": "Therapeutic Duplication: Check with your pharmacist whether multiple active medicines share the same class or therapeutic mechanism.",
                "priority": "High"
            })

        # -------------------------------------------------------------
        # TIER 3: WHAT TO AVOID (Dietary, Food, Beverage & Drug Clashes)
        # -------------------------------------------------------------
        drug_food_alerts = interaction_data.get("drug_food", [])
        for df in drug_food_alerts:
            recommendations.append({
                "category": "WHAT TO AVOID",
                "text": f"Food-Drug Interaction Alert: {df.get('description', '')}",
                "priority": "High" if df.get("severity") == "Major" else "Medium"
            })

        # Alcohol check
        foods_text = " ".join([f.get("food_name", "").lower() + " " + f.get("category", "").lower() for f in foods])
        if "alcohol" in foods_text and len(medications) > 0:
            recommendations.append({
                "category": "WHAT TO AVOID",
                "text": "Alcohol Precaution: Concurrent alcohol intake can potentiate central nervous system depression, hepatotoxicity, and alter hepatic drug clearance.",
                "priority": "High"
            })

        # Grapefruit check
        if "grapefruit" in foods_text:
            recommendations.append({
                "category": "WHAT TO AVOID",
                "text": "Grapefruit Caution: Grapefruit and bitter citrus juices inhibit intestinal CYP3A4 enzymes and can sharply increase the potency and side effects of certain medications.",
                "priority": "Medium"
            })

        # Dairy/Calcium check
        if "milk" in foods_text or "dairy" in foods_text:
            recommendations.append({
                "category": "WHAT TO AVOID",
                "text": "Calcium Chelation Notice: Calcium-rich dairy foods can bind to certain antibiotics (fluoroquinolones, tetracyclines) and iron; separate ingestion by at least 2 hours.",
                "priority": "Standard"
            })

        # -------------------------------------------------------------
        # TIER 4: WHAT TO MONITOR (Symptoms & Health Conditions)
        # -------------------------------------------------------------
        if symptoms:
            sym_names = [f"{s.get('symptom_name')} ({s.get('severity', 'Mild')})" for s in symptoms]
            recommendations.append({
                "category": "WHAT TO MONITOR",
                "text": f"Active Symptom Tracking: Record the onset and frequency of current symptoms [{', '.join(sym_names)}] and seek immediate care if they intensify.",
                "priority": "Medium"
            })

        conditions = patient.get("conditions", [])
        if any("kidney" in c.lower() or "renal" in c.lower() for c in conditions):
            recommendations.append({
                "category": "WHAT TO MONITOR",
                "text": "Renal Function Monitoring: Given your documented renal condition, ensure regular serum creatinine and eGFR blood tests, and exercise caution with OTC NSAIDs.",
                "priority": "High"
            })
        if any("liver" in c.lower() or "hepatic" in c.lower() for c in conditions):
            recommendations.append({
                "category": "WHAT TO MONITOR",
                "text": "Hepatic Function Monitoring: Exercise caution with hepatically metabolized drugs (e.g. acetaminophen/paracetamol exceeding safe daily limits).",
                "priority": "High"
            })

        # General safety advice if list is small
        if len(recommendations) < 3:
            recommendations.append({
                "category": "WHAT TO MONITOR",
                "text": "Routine Vigilance: Monitor for unexpected fatigue, rashes, or gastrointestinal discomfort after initiating any new prescription or supplement.",
                "priority": "Standard"
            })

        return recommendations

# Singleton instance
recommendation_service = RecommendationService()
