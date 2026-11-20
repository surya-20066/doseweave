"""
DoseWeave - Database Unit Tests
Verifies SQLite CRUD operations for users, patient records, medications, and assessment logs.
"""

import unittest
import time
from database.database import (
    get_all_patients, get_patient, create_patient,
    add_medication, get_patient_medications, save_risk_assessment,
    get_assessment_history, create_user, verify_user,
    save_complete_patient_data, get_patient_by_user,
    update_user_profile, change_user_password
)

class TestDatabase(unittest.TestCase):
    def test_user_authentication_flow(self):
        test_email = f"test_user_{int(time.time())}@example.com"
        # 1. Registration
        ok, msg, uid = create_user("Test Officer", test_email, "SecurePass123!")
        self.assertTrue(ok)
        self.assertIsNotNone(uid)

        # 2. Duplicate prevention
        dup_ok, dup_msg, _ = create_user("Duplicate", test_email, "SecurePass123!")
        self.assertFalse(dup_ok)

        # 3. Successful verification
        user = verify_user(test_email, "SecurePass123!")
        self.assertIsNotNone(user)
        self.assertEqual(user["email"], test_email.lower())
        self.assertNotIn("password_hash", user)

        # 4. Failed verification
        bad_user = verify_user(test_email, "WrongPassword")
        self.assertIsNone(bad_user)

    def test_save_complete_patient_data(self):
        user_email = f"patient_owner_{int(time.time())}@example.com"
        _, _, uid = create_user("Patient Owner", user_email, "Password999")
        
        pid = save_complete_patient_data(
            user_id=uid,
            patient_info={
                "name": "Intake Flow Patient",
                "age": 52,
                "gender": "Female",
                "weight": 70.0,
                "height": 168.0,
                "blood_group": "A+"
            },
            conditions=["Hypertension", "Dyslipidemia"],
            allergies=[{"name": "Aspirin", "type": "Medicine", "severity": "Severe"}],
            medications=[{
                "medicine_name": "Atorvastatin",
                "generic_name": "Atorvastatin Calcium",
                "strength": "20 mg",
                "prescribed_dosage": "20 mg daily",
                "actual_dosage": "20 mg daily",
                "number_of_tablets": 1,
                "frequency": "Once daily",
                "duration": "Ongoing",
                "reason": "Cholesterol",
                "relationship": "Prescribed"
            }],
            foods=[{
                "food_name": "Grapefruit Juice",
                "category": "Beverage",
                "quantity": "1 glass",
                "time_consumed": "Morning",
                "relationship_to_med": "With Medication"
            }],
            symptoms=[{
                "symptom_name": "Muscle cramps",
                "severity": "Moderate",
                "time_started": "3 days ago"
            }]
        )
        self.assertIsNotNone(pid)

        # Verify retrieval via user_id
        retrieved = get_patient_by_user(uid)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved["name"], "Intake Flow Patient")
        self.assertIn("Hypertension", retrieved["conditions"])

    def test_get_patients(self):
        patients = get_all_patients()
        self.assertIsInstance(patients, list)
        self.assertGreaterEqual(len(patients), 1)

    def test_create_and_fetch_patient(self):
        pid = create_patient(
            name="Test Patient Unit",
            age=45,
            gender="Female",
            weight=65.0,
            height=165.0,
            blood_group="B+",
            conditions=["Asthma / COPD"],
            allergies=[{"name": "Aspirin", "type": "Medicine", "severity": "Major"}]
        )
        patient = get_patient(pid)
        self.assertIsNotNone(patient)
        self.assertEqual(patient["name"], "Test Patient Unit")
        self.assertIn("Asthma / COPD", patient["conditions"])

    def test_add_and_fetch_medication(self):
        patients = get_all_patients()
        pid = patients[0]["id"]
        mid = add_medication(pid, {
            "medicine_name": "TestDrug 100",
            "generic_name": "TestCompound",
            "strength": "100 mg",
            "prescribed_dosage": "100 mg daily",
            "actual_dosage": "100 mg daily",
            "frequency": "Once a day",
            "relationship": "Prescribed"
        })
        meds = get_patient_medications(pid)
        names = [m["medicine_name"] for m in meds]
    def test_update_profile_and_change_password(self):
        email = f"profile_test_{int(time.time())}@example.com"
        ok, _, uid = create_user("Original Name", email, "InitialPass123")
        self.assertTrue(ok)

        # Update profile
        upd_ok, _ = update_user_profile(uid, "Updated Officer Name", f"new_{email}")
        self.assertTrue(upd_ok)

        # Verify updated user
        updated_user = verify_user(f"new_{email}", "InitialPass123")
        self.assertIsNotNone(updated_user)
        self.assertEqual(updated_user["full_name"], "Updated Officer Name")

        # Change password
        pwd_ok, _ = change_user_password(uid, "InitialPass123", "NewSecretPass456")
        self.assertTrue(pwd_ok)

        # Verify login with new password
        login_new = verify_user(f"new_{email}", "NewSecretPass456")
        self.assertIsNotNone(login_new)

        # Old password should fail
        login_old = verify_user(f"new_{email}", "InitialPass123")
        self.assertIsNone(login_old)

if __name__ == "__main__":
    unittest.main()
