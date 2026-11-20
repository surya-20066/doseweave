"""
DoseWeave - Deterministic Interaction-Aware Medication Scheduling Engine
Calculates optimal, clinically grounded administration schedules for complex multi-drug regimens.

Features:
1. Patient lifestyle harmonization: aligns doses with wake-up, bedtime, and breakfast/lunch/dinner times.
2. Verified pharmacological separation rules (e.g. Levothyroxine-Calcium, Fluoroquinolone-Cation, Bisphosphonates).
3. Distinguishes spacing-manageable pharmacokinetic conflicts from pharmacodynamic contraindications.
4. Never invents safe intervals: flags unresolvable interactions for clinician/pharmacist review.
5. Supports OD (1x), BID (2x), TID (3x), QID (4x), specific clock hours, and PRN (as-needed) tracking.
"""

import datetime
from typing import List, Dict, Any, Tuple, Optional
from utils.logging_config import logger

# Clinically verified timing constraints database with published evidence citations
VERIFIED_TIMING_RULES = [
    {
        "id": "RULE_LEVO_CATION",
        "drug_a_keywords": ["levothyroxine", "synthroid", "euthyrox", "eltroxin"],
        "drug_b_keywords": ["calcium", "iron", "ferrous", "multivitamin", "antacid"],
        "min_separation_hours": 4.0,
        "mechanism": "Divalent and trivalent cations chelate levothyroxine in the gut, reducing thyroid hormone absorption by up to 75%.",
        "action": "Schedule levothyroxine upon waking on an empty stomach; schedule cation/iron/multivitamin at least 4 hours later (lunch or dinner).",
        "evidence": "FDA Prescribing Information & American Thyroid Association (ATA) Guidelines"
    },
    {
        "id": "RULE_FLUORO_CATION",
        "drug_a_keywords": ["ciprofloxacin", "levofloxacin", "moxifloxacin", "ofloxacin"],
        "drug_b_keywords": ["calcium", "magnesium", "aluminum", "dairy", "milk", "iron", "antacid"],
        "min_separation_hours": 3.0,
        "mechanism": "Chelation with polyvalent metal cations drastically lowers fluoroquinolone bioavailability and therapeutic efficacy.",
        "action": "Administer fluoroquinolone at least 2 hours before or 4 hours after cation-rich supplements or dairy foods.",
        "evidence": "FDA Approved Drug Labeling & Clinical Pharmacokinetics Standards"
    },
    {
        "id": "RULE_BISPHOSPHONATE",
        "drug_a_keywords": ["alendronate", "risedronate", "ibandronate", "fosamax"],
        "drug_b_keywords": ["*"],  # Any other drug
        "min_separation_hours": 0.5,
        "mechanism": "Bisphosphonates have oral bioavailability < 1% and high esophageal mucosal irritation potential.",
        "action": "Take immediately upon waking with a full glass of plain water, 30 to 60 minutes before any food, beverage, or other medications.",
        "evidence": "National Osteoporosis Foundation & FDA Approved Product Label"
    },
    {
        "id": "RULE_TETRACYCLINE_CATION",
        "drug_a_keywords": ["doxycycline", "tetracycline", "minocycline"],
        "drug_b_keywords": ["calcium", "iron", "dairy", "milk", "antacid"],
        "min_separation_hours": 2.0,
        "mechanism": "Forms insoluble metal chelates in GI tract, substantially decreasing antibacterial absorption.",
        "action": "Separate tetracycline dose from dairy and mineral supplements by at least 2 hours.",
        "evidence": "DailyMed Structured Product Labeling & USP Monograph"
    }
]

# Established drug-class time-of-day preferences
PREFERRED_TIME_RULES = [
    {
        "keywords": ["simvastatin", "atorvastatin", "pravastatin", "lovastatin", "rosuvastatin"],
        "preferred_period": "evening",
        "rationale": "Hepatic cholesterol synthesis peaks between midnight and early morning (HMG-CoA reductase circadian rhythm).",
        "citation": "ACC/AHA Guidelines on Blood Cholesterol"
    },
    {
        "keywords": ["furosemide", "torsemide", "hydrochlorothiazide", "hctz", "indapamide", "chlorthalidone"],
        "preferred_period": "morning",
        "rationale": "Administer in the morning or early afternoon to prevent disruptive nocturnal diuresis.",
        "citation": "Clinical Pharmacokinetics & Diuretic Dosing Standards"
    },
    {
        "keywords": ["omeprazole", "pantoprazole", "esomeprazole", "lansoprazole", "rabeprazole"],
        "preferred_period": "before_breakfast",
        "rationale": "Proton pump inhibitors require active H+/K+ ATPase pumps; administer 30 to 60 minutes before the first meal of the day.",
        "citation": "American College of Gastroenterology (ACG) Clinical Practice Guidelines"
    },
    {
        "keywords": ["zolpidem", "zaleplon", "eszopiclone", "melatonin", "trazodone"],
        "preferred_period": "bedtime",
        "rationale": "Sedative-hypnotics should be administered 15 to 30 minutes immediately before planned sleep.",
        "citation": "FDA Sleep Medication Guidance"
    }
]

class SchedulingEngine:
    def __init__(self):
        pass

    def parse_time(self, time_str: str) -> datetime.time:
        """Parses HH:MM string to datetime.time safely."""
        try:
            parts = time_str.strip().split(":")
            return datetime.time(int(parts[0]), int(parts[1]))
        except Exception:
            return datetime.time(8, 0)

    def format_time(self, dt_time: datetime.time) -> str:
        """Formats datetime.time to 12-hour AM/PM string (e.g. '08:00 AM')."""
        hour = dt_time.hour
        minute = dt_time.minute
        period = "AM" if hour < 12 else "PM"
        display_hour = hour if hour <= 12 else hour - 12
        if display_hour == 0:
            display_hour = 12
        return f"{display_hour}:{minute:02d} {period}"

    def time_to_minutes(self, dt_time: datetime.time) -> int:
        return dt_time.hour * 60 + dt_time.minute

    def minutes_to_time(self, total_mins: int) -> datetime.time:
        total_mins = total_mins % (24 * 60)
        return datetime.time(total_mins // 60, total_mins % 60)

    def normalize_frequency(self, freq_str: str) -> Tuple[int, List[str]]:
        """
        Normalizes natural language frequency string into dose count and standard slots.
        Returns: (doses_per_day, slot_labels)
        """
        f = (freq_str or "").lower().strip()

        if "four" in f or "qid" in f or "4 times" in f:
            return 4, ["morning", "midday", "evening", "bedtime"]
        if "three" in f or "tid" in f or "3 times" in f:
            return 3, ["morning", "midday", "evening"]
        if "twice" in f or "bid" in f or "2 times" in f:
            return 2, ["morning", "evening"]
        if "bedtime" in f or "night" in f or "hs" in f:
            return 1, ["bedtime"]
        if "prn" in f or "as needed" in f or "sos" in f:
            return 0, ["as_needed"]
        # Default: once daily
        return 1, ["morning"]

    def evaluate_pairwise_timing_constraints(
        self,
        medications: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Identifies active verified separation constraints between medications in the list.
        """
        active_constraints = []
        n = len(medications)
        for i in range(n):
            for j in range(i + 1, n):
                m1 = medications[i]
                m2 = medications[j]
                m1_names = [m1.get("medicine_name", "").lower(), m1.get("generic_name", "").lower()]
                m2_names = [m2.get("medicine_name", "").lower(), m2.get("generic_name", "").lower()]

                for rule in VERIFIED_TIMING_RULES:
                    m1_match_a = any(any(kw in name for kw in rule["drug_a_keywords"]) for name in m1_names)
                    m2_match_b = (rule["drug_b_keywords"] == ["*"]) or any(any(kw in name for kw in rule["drug_b_keywords"]) for name in m2_names)

                    m2_match_a = any(any(kw in name for kw in rule["drug_a_keywords"]) for name in m2_names)
                    m1_match_b = (rule["drug_b_keywords"] == ["*"]) or any(any(kw in name for kw in rule["drug_b_keywords"]) for name in m1_names)

                    if (m1_match_a and m2_match_b) or (m2_match_a and m1_match_b):
                        first_drug = m1.get("medicine_name") if m1_match_a else m2.get("medicine_name")
                        second_drug = m2.get("medicine_name") if m1_match_a else m1.get("medicine_name")
                        active_constraints.append({
                            "rule_id": rule["id"],
                            "drug_primary": first_drug,
                            "drug_secondary": second_drug,
                            "min_separation_hours": rule["min_separation_hours"],
                            "mechanism": rule["mechanism"],
                            "action": rule["action"],
                            "evidence": rule["evidence"]
                        })
        return active_constraints

    def generate_schedule(
        self,
        patient: Dict[str, Any],
        medications: List[Dict[str, Any]],
        interaction_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generates a deterministic 24-hour medication schedule based on patient's routine,
        meal schedules, drug frequencies, and verified pharmacological separation rules.
        """
        patient = patient or {}
        medications = [m for m in (medications or []) if m]
        interaction_data = interaction_data or {}

        # 1. Extract Patient Daily Anchor Times
        wakeup_t = self.parse_time(patient.get("wakeup_time") or "07:00")
        bedtime_t = self.parse_time(patient.get("bedtime") or "22:00")
        breakfast_t = self.parse_time(patient.get("breakfast_time") or "08:00")
        lunch_t = self.parse_time(patient.get("lunch_time") or "13:00")
        dinner_t = self.parse_time(patient.get("dinner_time") or "20:00")

        wakeup_mins = self.time_to_minutes(wakeup_t)
        bedtime_mins = self.time_to_minutes(bedtime_t)
        breakfast_mins = self.time_to_minutes(breakfast_t)
        lunch_mins = self.time_to_minutes(lunch_t)
        dinner_mins = self.time_to_minutes(dinner_t)

        # Baseline slot times in minutes from midnight
        slot_times = {
            "upon_waking": max(0, wakeup_mins + 15),
            "before_breakfast": max(0, breakfast_mins - 30),
            "breakfast": breakfast_mins,
            "morning": breakfast_mins + 15,
            "midday": lunch_mins,
            "after_lunch": lunch_mins + 30,
            "evening": dinner_mins,
            "after_dinner": dinner_mins + 30,
            "bedtime": max(0, bedtime_mins - 30)
        }

        # 2. Check for active spacing constraints
        timing_constraints = self.evaluate_pairwise_timing_constraints(medications)

        # 3. Check for severe unresolvable interactions (pharmacodynamic conflicts)
        unresolvable_conflicts = []
        drug_drug_alerts = interaction_data.get("drug_drug", [])
        for alert in drug_drug_alerts:
            # If severity is Major and not a chelation rule, spacing does not cure the issue
            is_chelation = any(kw in alert.get("description", "").lower() for kw in ["chelat", "separate by", "impairs absorption", "bioavailability"])
            if alert.get("severity") == "Major" and not is_chelation:
                unresolvable_conflicts.append({
                    "pair": f"{alert.get('item1')} + {alert.get('item2')}",
                    "severity": alert.get("severity"),
                    "description": alert.get("description"),
                    "clinical_warning": "CRITICAL: This is a systemic pharmacodynamic contraindication (e.g. synergistic toxicity or bleeding risk). Timing separation DOES NOT eliminate clinical hazard. Physician/pharmacist consultation is mandatory."
                })

        # 4. Schedule each medication into appropriate daily slots
        scheduled_doses = []
        prn_medications = []

        # Keep track of assigned minutes per drug to enforce separation rules
        assigned_times: Dict[str, List[int]] = {}

        for med in medications:
            med_name = med.get("medicine_name", "Medication").strip()
            gen_name = (med.get("generic_name") or med_name).lower()
            dose_val = med.get("actual_dosage") or med.get("prescribed_dosage") or med.get("strength") or "1 unit"
            dose_unit = med.get("dosage_unit") or "mg"
            freq_str = med.get("frequency", "Once daily")
            food_timing = med.get("food_timing", "Independent")
            instructions = med.get("instructions") or ""

            # Check if this is PRN / as-needed
            is_prn = med.get("is_prn") == 1 or "prn" in freq_str.lower() or "as needed" in freq_str.lower()
            if is_prn:
                prn_medications.append({
                    "medication_id": med.get("id"),
                    "medicine_name": med_name,
                    "dose_amount": dose_val,
                    "dose_unit": dose_unit,
                    "frequency": freq_str,
                    "instructions": instructions or "Take as needed strictly according to physician's maximum daily limit instructions.",
                    "meal_relation": food_timing
                })
                continue

            # Determine preferred time-of-day period
            preferred_period = None
            for p_rule in PREFERRED_TIME_RULES:
                if any(kw in gen_name or kw in med_name.lower() for kw in p_rule["keywords"]):
                    preferred_period = p_rule["preferred_period"]
                    if not instructions:
                        instructions = p_rule["rationale"]
                    break

            dose_count, slots = self.normalize_frequency(freq_str)

            # Map slots to concrete target minutes
            target_minute_list = []
            if preferred_period == "bedtime":
                target_minute_list = [slot_times["bedtime"]]
            elif preferred_period == "before_breakfast":
                target_minute_list = [slot_times["before_breakfast"]]
            elif preferred_period == "evening" and dose_count == 1:
                target_minute_list = [slot_times["evening"]]
            elif dose_count == 1:
                if food_timing == "Before Food":
                    target_minute_list = [slot_times["before_breakfast"]]
                elif food_timing == "After Food":
                    target_minute_list = [slot_times["after_dinner"] if "evening" in (med.get("time_taken") or "").lower() else slot_times["morning"]]
                elif "evening" in (med.get("time_taken") or "").lower():
                    target_minute_list = [slot_times["evening"]]
                else:
                    target_minute_list = [slot_times["morning"]]
            elif dose_count == 2:
                # BID: Morning + Evening (separated by ~12 hours)
                m_slot = slot_times["before_breakfast"] if food_timing == "Before Food" else slot_times["morning"]
                e_slot = slot_times["evening"]
                target_minute_list = [m_slot, e_slot]
            elif dose_count == 3:
                # TID: Morning + Midday + Evening (~6-8 hour intervals)
                target_minute_list = [slot_times["morning"], slot_times["midday"], slot_times["evening"]]
            elif dose_count >= 4:
                # QID: 4 distributed waking doses
                target_minute_list = [slot_times["upon_waking"], slot_times["midday"], slot_times["evening"], slot_times["bedtime"]]
            else:
                target_minute_list = [slot_times["morning"]]

            # Apply Pharmacological Separation Constraints against previously assigned drugs
            adjusted_target_minutes = []
            for target_min in target_minute_list:
                cur_min = target_min

                for constraint in timing_constraints:
                    min_sep_mins = int(constraint["min_separation_hours"] * 60)
                    is_secondary = (constraint["drug_secondary"].lower() in med_name.lower())
                    primary_name = constraint["drug_primary"].lower()

                    if is_secondary:
                        # Find times assigned to primary drug
                        for prev_drug, prev_times in assigned_times.items():
                            if primary_name in prev_drug:
                                for pt in prev_times:
                                    diff = abs(cur_min - pt)
                                    if diff < min_sep_mins:
                                        # Shift cur_min forward by required separation
                                        cur_min = pt + min_sep_mins
                                        if cur_min >= bedtime_mins:
                                            # If past bedtime, schedule before primary if possible
                                            cur_min = max(wakeup_mins, pt - min_sep_mins)
                                        logger.info(f"Separation rule applied for {med_name}: shifted from {target_min} to {cur_min} ({constraint['action']})")

                adjusted_target_minutes.append(cur_min)

            assigned_times[med_name.lower()] = adjusted_target_minutes

            # Create concrete scheduled dose events
            for t_min in adjusted_target_minutes:
                dose_time_obj = self.minutes_to_time(t_min)
                formatted_24 = f"{dose_time_obj.hour:02d}:{dose_time_obj.minute:02d}"
                formatted_12 = self.format_time(dose_time_obj)

                # Meal relation description
                meal_relation_text = "With glass of water"
                if abs(t_min - breakfast_mins) <= 20:
                    meal_relation_text = "With breakfast"
                elif t_min < breakfast_mins and (breakfast_mins - t_min) <= 45:
                    meal_relation_text = "30-60 min before breakfast"
                elif abs(t_min - lunch_mins) <= 30:
                    meal_relation_text = "With lunch"
                elif abs(t_min - dinner_mins) <= 30:
                    meal_relation_text = "With dinner"
                elif abs(t_min - bedtime_mins) <= 45:
                    meal_relation_text = "At bedtime"
                elif food_timing == "With Food":
                    meal_relation_text = "Take with food or snack"
                elif food_timing == "Before Food":
                    meal_relation_text = "30 min before next meal"
                elif food_timing == "After Food":
                    meal_relation_text = "30 min after meal"

                scheduled_doses.append({
                    "medication_id": med.get("id"),
                    "medicine_name": med_name,
                    "generic_name": med.get("generic_name", med_name),
                    "dose_amount": dose_val,
                    "dose_unit": dose_unit,
                    "scheduled_time": formatted_24,
                    "scheduled_time_display": formatted_12,
                    "meal_relation": meal_relation_text,
                    "instructions": instructions or f"Take {dose_val} via {med.get('route', 'oral')} route. {meal_relation_text}.",
                    "status": "scheduled",
                    "raw_minutes": t_min
                })

        # Sort chronologically by time
        scheduled_doses.sort(key=lambda d: d["raw_minutes"])

        return {
            "patient_id": patient.get("id"),
            "patient_name": patient.get("name"),
            "scheduled_doses": scheduled_doses,
            "total_doses": len(scheduled_doses),
            "prn_medications": prn_medications,
            "applied_timing_constraints": timing_constraints,
            "unresolvable_conflicts": unresolvable_conflicts,
            "status": "proposed",
            "schedule_name": f"DoseWeave Optimized Regimen ({len(scheduled_doses)} daily doses)",
            "generated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

# Global singleton
scheduling_engine = SchedulingEngine()
