"""
MediSafe AI - Machine Learning Model Unit Tests
Verifies feature engineering, model inference, probability calibration, and explainability.
"""

import unittest
from models.predict import risk_predictor
from services.interaction_service import interaction_service

class TestModels(unittest.TestCase):
    def test_model_loaded(self):
        self.assertTrue(risk_predictor.is_ready(), "Model and preprocessor should be loaded")

    def test_low_risk_prediction(self):
        patient = {"age": 28, "gender": "Female", "weight": 60, "conditions": [], "allergies": []}
        meds = [{"medicine_name": "Paracetamol", "generic_name": "Paracetamol", "prescribed_dosage": "500mg", "actual_dosage": "500mg", "frequency": "Once daily"}]
        foods = [{"food_name": "Water", "category": "General Food"}]
        symptoms = []
        inter = interaction_service.analyze_all(meds, foods, [], [])
        pred = risk_predictor.predict_risk(patient, meds, foods, symptoms, inter)

        self.assertIn(pred["risk_level"], ["LOW RISK", "MODERATE RISK"])
        self.assertGreaterEqual(pred["model_confidence"], 50.0)
        self.assertIsInstance(pred["top_contributing_factors"], list)

    def test_high_risk_emergency_override(self):
        patient = {"age": 72, "gender": "Male", "weight": 80, "conditions": ["Chronic Kidney Disease"], "allergies": []}
        meds = [{"medicine_name": "Aspirin", "generic_name": "Aspirin", "prescribed_dosage": "100mg", "actual_dosage": "500mg", "frequency": "Twice daily"}]
        foods = [{"food_name": "Whiskey", "category": "Alcohol"}]
        symptoms = [{"symptom_name": "Difficulty Breathing", "severity": "Severe"}]
        inter = interaction_service.analyze_all(meds, foods, patient["conditions"], [])
        pred = risk_predictor.predict_risk(patient, meds, foods, symptoms, inter)

        self.assertEqual(pred["risk_level"], "HIGH RISK")
        self.assertTrue(pred["is_emergency"])
        self.assertGreaterEqual(pred["risk_score"], 66.0)

if __name__ == "__main__":
    unittest.main()
