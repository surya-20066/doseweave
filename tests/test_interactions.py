"""
DoseWeave - Interaction Intelligence Unit Tests
Verifies pharmacological cross-matching against verified databases.
"""

import unittest
from services.interaction_service import interaction_service

class TestInteractions(unittest.TestCase):
    def test_drug_drug_interaction(self):
        meds = [
            {"medicine_name": "Aspirin", "generic_name": "Aspirin"},
            {"medicine_name": "Warfarin Sodium", "generic_name": "Warfarin"}
        ]
        res = interaction_service.analyze_all(meds, [], [], [])
        self.assertGreater(len(res["drug_drug"]), 0)
        self.assertEqual(res["drug_drug"][0]["severity"], "Major")

    def test_drug_food_interaction(self):
        meds = [{"medicine_name": "Atorvastatin Calcium", "generic_name": "Atorvastatin"}]
        foods = [{"food_name": "Fresh Grapefruit Juice", "category": "Grapefruit & Citrus Juice"}]
        res = interaction_service.analyze_all(meds, foods, [], [])
        self.assertGreater(len(res["drug_food"]), 0)

    def test_condition_contraindication(self):
        meds = [{"medicine_name": "Ibuprofen Advil", "generic_name": "Ibuprofen"}]
        conditions = ["Chronic Kidney Disease"]
        res = interaction_service.analyze_all(meds, [], conditions, [])
        self.assertGreater(len(res["contraindications"]), 0)

    def test_allergy_cross_reaction(self):
        meds = [{"medicine_name": "Amoxicillin", "generic_name": "Amoxicillin"}]
        allergies = [{"allergen_name": "Penicillin", "type": "Medicine"}]
        res = interaction_service.analyze_all(meds, [], [], allergies)
        self.assertGreater(len(res["allergies"]), 0)

if __name__ == "__main__":
    unittest.main()
