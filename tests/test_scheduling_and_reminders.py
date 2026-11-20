"""
DoseWeave - Scheduling Engine, Reminder Service & Dynamic Database Tests
Comprehensive validation of deterministic scheduling, pharmacological constraints,
adherence logging, medicine search, and role-based access control.
"""

import unittest
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.database import (
    init_db, create_user, verify_user, create_or_update_schedule,
    get_active_schedule, get_scheduled_doses, update_dose_status,
    record_adherence, get_adherence_stats, get_reminder_preferences,
    save_reminder_preferences, get_cached_drug_info, save_cached_drug_info,
    get_admin_system_stats, get_table_data_paginated
)
from services.scheduling_engine import scheduling_engine
from services.reminder_service import reminder_service
from services.medicine_service import medicine_service
from services.interaction_service import interaction_service

class TestSchedulingAndReminders(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db(force=True)

    def test_multi_medicine_frequency_scheduling(self):
        """Test scheduling medicines with 1x, 2x, 3x, and bedtime frequencies."""
        patient = {
            "name": "Test Patient",
            "wakeup_time": "07:00",
            "bedtime": "22:00",
            "breakfast_time": "08:00",
            "lunch_time": "13:00",
            "dinner_time": "20:00"
        }
        meds = [
            {"medicine_name": "Lisinopril", "frequency": "Once daily", "food_timing": "Independent"},
            {"medicine_name": "Metformin", "frequency": "Twice a day", "food_timing": "With Food"},
            {"medicine_name": "Amoxicillin", "frequency": "Three times daily", "food_timing": "With Food"},
            {"medicine_name": "Zolpidem", "frequency": "At bedtime", "food_timing": "Independent"},
            {"medicine_name": "Paracetamol", "frequency": "As needed (PRN)", "food_timing": "Independent", "is_prn": 1}
        ]
        res = scheduling_engine.generate_schedule(patient, meds)

        # 1 + 2 + 3 + 1 = 7 scheduled doses, 1 PRN med
        self.assertEqual(res["total_doses"], 7)
        self.assertEqual(len(res["prn_medications"]), 1)
        self.assertEqual(res["prn_medications"][0]["medicine_name"], "Paracetamol")

        # Verify Zolpidem is scheduled at bedtime
        zolp_doses = [d for d in res["scheduled_doses"] if d["medicine_name"] == "Zolpidem"]
        self.assertEqual(len(zolp_doses), 1)
        self.assertIn("bedtime", zolp_doses[0]["meal_relation"].lower())

    def test_pharmacological_separation_rule(self):
        """Test that Levothyroxine and Calcium are spaced by at least 4 hours."""
        patient = {
            "name": "Thyroid Patient",
            "wakeup_time": "06:30",
            "bedtime": "22:00",
            "breakfast_time": "07:30",
            "lunch_time": "12:30",
            "dinner_time": "19:30"
        }
        meds = [
            {"medicine_name": "Levothyroxine", "frequency": "Once daily", "food_timing": "Before Food"},
            {"medicine_name": "Calcium Carbonate", "frequency": "Once daily", "food_timing": "With Food"}
        ]
        res = scheduling_engine.generate_schedule(patient, meds)
        self.assertEqual(len(res["applied_timing_constraints"]), 1)
        constraint = res["applied_timing_constraints"][0]
        self.assertEqual(constraint["rule_id"], "RULE_LEVO_CATION")
        self.assertGreaterEqual(constraint["min_separation_hours"], 4.0)

        # Confirm actual minutes difference >= 240 minutes (4 hours)
        levo_time = next(d["raw_minutes"] for d in res["scheduled_doses"] if d["medicine_name"] == "Levothyroxine")
        calc_time = next(d["raw_minutes"] for d in res["scheduled_doses"] if d["medicine_name"] == "Calcium Carbonate")
        self.assertGreaterEqual(abs(calc_time - levo_time), 240)

    def test_unresolvable_pharmacodynamic_conflict(self):
        """Verify that severe pharmacodynamic contraindications (e.g. Warfarin + Aspirin) are flagged as unresolvable."""
        patient = {"name": "Anticoag Patient"}
        meds = [
            {"medicine_name": "Warfarin", "frequency": "Once daily", "food_timing": "Independent"},
            {"medicine_name": "Aspirin", "frequency": "Once daily", "food_timing": "With Food"}
        ]
        interactions = interaction_service.analyze_all(medications=meds)
        res = scheduling_engine.generate_schedule(patient, meds, interaction_data=interactions)

        self.assertGreater(len(res["unresolvable_conflicts"]), 0)
        unres = res["unresolvable_conflicts"][0]
        self.assertIn("Warfarin", unres["pair"])
        self.assertIn("Aspirin", unres["pair"])
        self.assertIn("CRITICAL", unres["clinical_warning"])

    def test_schedule_persistence_and_adherence(self):
        """Test saving a schedule and recording Taken/Missed/Snooze adherence events."""
        from database.database import create_patient
        user_email = f"sched_user_{int(time.time())}@example.com"
        ok, _, user_id = create_user("Schedule Test User", user_email, "securepwd123")
        self.assertTrue(ok)

        # Create real patient record linked to user
        patient_id = create_patient(user_id, "Schedule Test Patient", 45, "Female", 62.0, 165.0, "A+")
        self.assertIsNotNone(patient_id)

        # Create schedule
        doses = [
            {"medicine_name": "Metformin", "dose_amount": "500 mg", "scheduled_time": "08:00", "instructions": "Take with breakfast"},
            {"medicine_name": "Lisinopril", "dose_amount": "10 mg", "scheduled_time": "09:00", "instructions": "Take with water"}
        ]
        sched_id = create_or_update_schedule(
            patient_id=patient_id,
            user_id=user_id,
            schedule_name="Test Adherence Schedule",
            status="active",
            schedule_data_json="{}",
            conflict_warnings_json="[]",
            doses=doses
        )
        self.assertIsNotNone(sched_id)

        # Fetch doses
        saved_doses = get_scheduled_doses(schedule_id=sched_id)
        self.assertEqual(len(saved_doses), 2)
        dose1_id = saved_doses[0]["id"]
        dose2_id = saved_doses[1]["id"]

        # Mark dose 1 as taken
        reminder_service.mark_dose_taken(dose1_id, user_id=user_id)
        # Mark dose 2 as missed
        reminder_service.mark_dose_missed(dose2_id, user_id=user_id)

        # Verify adherence stats
        stats = get_adherence_stats(patient_id)
        self.assertEqual(stats["total"], 2)
        self.assertEqual(stats["taken"], 1)
        self.assertEqual(stats["missed"], 1)
        self.assertEqual(stats["adherence_rate"], 50.0)

    def test_medicine_search_and_retrieval(self):
        """Test drug search and monograph lookup with verified source attribution."""
        results = medicine_service.search_medicines("atorvastatin")
        self.assertGreater(len(results), 0)
        mono = results[0]
        self.assertEqual(mono["drug_name"], "Atorvastatin")
        self.assertIn("HMG-CoA", mono["drug_class"])
        self.assertIn("FDA", mono["source_attribution"])

    def test_admin_role_authorization_and_stats(self):
        """Test admin authentication and database system statistics."""
        admin_user = verify_user("admin@doseweave.ai", "admin123")
        self.assertIsNotNone(admin_user)
        self.assertEqual(admin_user["role"], "admin")

        stats = get_admin_system_stats()
        self.assertGreaterEqual(stats["total_users"], 1)
        self.assertIn("recent_users", stats)

        # Test paginated table inspector
        rows, count = get_table_data_paginated("users", limit=10, offset=0)
        self.assertGreaterEqual(count, 1)
        self.assertLessEqual(len(rows), 10)

if __name__ == "__main__":
    unittest.main()
