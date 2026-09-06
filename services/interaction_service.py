"""
MediSafe AI - Interaction Intelligence Service
Analyzes drug-drug, drug-food, drug-alcohol, and condition contraindications
against verified pharmacological safety databases.
"""

import json
import os
import re
from typing import List, Dict, Any, Tuple
from utils.logging_config import logger

INTERACTIONS_FILE = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "data", "external", "verified_interactions.json"
)

class InteractionService:
    def __init__(self):
        self.rules = self._load_rules()

    def _load_rules(self) -> Dict[str, Any]:
        if not os.path.exists(INTERACTIONS_FILE):
            logger.warning(f"Interaction database not found at {INTERACTIONS_FILE}")
            return {"drug_drug_interactions": [], "drug_food_interactions": [], "disease_contraindications": [], "allergy_cross_reactions": []}
        try:
            with open(INTERACTIONS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load interactions JSON: {e}")
            return {"drug_drug_interactions": [], "drug_food_interactions": [], "disease_contraindications": [], "allergy_cross_reactions": []}

    def _normalize_name(self, text: str) -> str:
        if not text:
            return ""
        return re.sub(r"[^a-zA-Z0-9]", "", text.strip().lower())

    def _fuzzy_match(self, name1: str, name2: str) -> bool:
        """Check if one medicine/substance name is contained in or equals another."""
        n1 = self._normalize_name(name1)
        n2 = self._normalize_name(name2)
        if not n1 or not n2:
            return False
        return n1 in n2 or n2 in n1

    def analyze_all(
        self,
        medications: List[Dict[str, Any]],
        foods: List[Dict[str, Any]],
        conditions: List[str],
        allergies: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Runs comprehensive clinical analysis:
        1. Drug-Drug Interactions
        2. Drug-Food Interactions
        3. Drug-Condition Contraindications
        4. Allergy Cross-Reactions
        5. Duplicate Active Ingredient Check
        """
        drug_drug = self.check_drug_drug(medications)
        drug_food = self.check_drug_food(medications, foods)
        contraindications = self.check_disease_contraindications(medications, conditions)
        allergy_alerts = self.check_allergies(medications, allergies)
        duplicates = self.check_duplicate_ingredients(medications)

        total_alerts = (
            len(drug_drug)
            + len(drug_food)
            + len(contraindications)
            + len(allergy_alerts)
            + len(duplicates)
        )

        major_count = sum(
            1 for item in (drug_drug + drug_food + contraindications + allergy_alerts + duplicates)
            if item.get("severity") == "Major"
        )
        moderate_count = sum(
            1 for item in (drug_drug + drug_food + contraindications + allergy_alerts + duplicates)
            if item.get("severity") == "Moderate"
        )

        # Interaction severity score: Major = 35, Moderate = 15, Minor = 5
        severity_score = min(100.0, (major_count * 35.0) + (moderate_count * 15.0))

        return {
            "drug_drug": drug_drug,
            "drug_food": drug_food,
            "contraindications": contraindications,
            "allergies": allergy_alerts,
            "duplicates": duplicates,
            "total_alerts": total_alerts,
            "major_count": major_count,
            "moderate_count": moderate_count,
            "interaction_severity_score": severity_score
        }

    def check_drug_drug(self, medications: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        results = []
        dd_rules = self.rules.get("drug_drug_interactions", [])
        med_names = [m.get("medicine_name", "") for m in medications]
        med_generics = [m.get("generic_name", "") for m in medications]

        # Compare every pair
        for i in range(len(medications)):
            for j in range(i + 1, len(medications)):
                name_a = med_names[i]
                gen_a = med_generics[i]
                name_b = med_names[j]
                gen_b = med_generics[j]

                matched_rule = None
                for r in dd_rules:
                    p1, p2 = r["pair"]
                    # Check match in both directions
                    match_dir1 = (self._fuzzy_match(p1, name_a) or self._fuzzy_match(p1, gen_a)) and \
                                 (self._fuzzy_match(p2, name_b) or self._fuzzy_match(p2, gen_b))
                    match_dir2 = (self._fuzzy_match(p2, name_a) or self._fuzzy_match(p2, gen_a)) and \
                                 (self._fuzzy_match(p1, name_b) or self._fuzzy_match(p1, gen_b))
                    if match_dir1 or match_dir2:
                        matched_rule = r
                        break

                if matched_rule:
                    results.append({
                        "type": "Drug-Drug",
                        "item1": name_a,
                        "item2": name_b,
                        "severity": matched_rule.get("severity", "Major"),
                        "description": matched_rule.get("effect", ""),
                        "evidence": matched_rule.get("evidence_level", "Clinical Reference")
                    })
        return results

    def check_drug_food(self, medications: List[Dict[str, Any]], foods: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        results = []
        df_rules = self.rules.get("drug_food_interactions", [])

        for med in medications:
            m_name = med.get("medicine_name", "")
            m_gen = med.get("generic_name", "")

            for food in foods:
                f_name = food.get("food_name", "")
                f_cat = food.get("category", "")

                for rule in df_rules:
                    rule_drug = rule["drug"]
                    rule_cat = rule["food_category"]

                    drug_match = self._fuzzy_match(rule_drug, m_name) or self._fuzzy_match(rule_drug, m_gen)
                    food_match = (rule_cat.lower() in f_cat.lower()) or (rule_cat.lower() in f_name.lower()) or (f_cat.lower() in rule_cat.lower())

                    if drug_match and food_match:
                        results.append({
                            "type": "Drug-Food",
                            "item1": m_name,
                            "item2": f"{f_name} ({f_cat})",
                            "severity": rule.get("severity", "Major"),
                            "description": f"{rule.get('mechanism', '')} - {rule.get('recommendation', '')}",
                            "evidence": "FDA / Pharmacology Guidance"
                        })
                        break
        return results

    def check_disease_contraindications(self, medications: List[Dict[str, Any]], conditions: List[str]) -> List[Dict[str, Any]]:
        results = []
        contra_rules = self.rules.get("disease_contraindications", [])

        for med in medications:
            m_name = med.get("medicine_name", "")
            m_gen = med.get("generic_name", "")

            for cond in conditions:
                for rule in contra_rules:
                    rule_drug = rule["drug"]
                    rule_cond = rule["condition"]

                    drug_match = self._fuzzy_match(rule_drug, m_name) or self._fuzzy_match(rule_drug, m_gen)
                    cond_match = (self._normalize_name(rule_cond) in self._normalize_name(cond)) or \
                                 (self._normalize_name(cond) in self._normalize_name(rule_cond))

                    if drug_match and cond_match:
                        results.append({
                            "type": "Drug-Condition",
                            "item1": m_name,
                            "item2": cond,
                            "severity": rule.get("severity", "Major"),
                            "description": rule.get("warning", ""),
                            "evidence": "Clinical Practice Contraindication"
                        })
                        break
        return results

    def check_allergies(self, medications: List[Dict[str, Any]], allergies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        results = []
        cross_rules = self.rules.get("allergy_cross_reactions", [])

        for med in medications:
            m_name = med.get("medicine_name", "")
            m_gen = med.get("generic_name", "")

            for alg in allergies:
                alg_name = alg.get("allergen_name", "")

                # 1. Direct match
                if self._fuzzy_match(alg_name, m_name) or self._fuzzy_match(alg_name, m_gen):
                    results.append({
                        "type": "Allergy Alert",
                        "item1": m_name,
                        "item2": alg_name,
                        "severity": "Major",
                        "description": f"Known active allergy reported for {alg_name}. High risk of hypersensitivity reaction.",
                        "evidence": "Patient Documented Allergy"
                    })
                    continue

                # 2. Cross reaction rules
                for cross in cross_rules:
                    if self._fuzzy_match(cross["allergen"], alg_name):
                        for match_med in cross["matches"]:
                            if self._fuzzy_match(match_med, m_name) or self._fuzzy_match(match_med, m_gen):
                                results.append({
                                    "type": "Cross-Allergy Alert",
                                    "item1": m_name,
                                    "item2": f"{alg_name} cross-sensitivity",
                                    "severity": cross.get("severity", "Major"),
                                    "description": cross.get("warning", "Cross-reactivity risk with documented allergy."),
                                    "evidence": "Immunological Cross-Reactivity Standard"
                                })
                                break
        return results

    def check_duplicate_ingredients(self, medications: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identifies unintentional duplicate therapies or active ingredients."""
        results = []
        seen = {}
        for med in medications:
            gen = self._normalize_name(med.get("generic_name", "")) or self._normalize_name(med.get("medicine_name", ""))
            if not gen:
                continue
            if gen in seen:
                results.append({
                    "type": "Duplicate Active Therapy",
                    "item1": seen[gen],
                    "item2": med.get("medicine_name", ""),
                    "severity": "Moderate",
                    "description": f"Duplicate active compound or therapeutic class detected ({gen}). May cause accidental cumulative overdose.",
                    "evidence": "Therapeutic Duplication Warning"
                })
            else:
                seen[gen] = med.get("medicine_name", "")
        return results

# Singleton instance
interaction_service = InteractionService()
