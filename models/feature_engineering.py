"""
MediSafe AI - Feature Engineering & Preprocessing Pipeline
Defines feature schema, transformation pipelines (ColumnTransformer, StandardScaler, OneHotEncoder),
and real-time patient feature extraction.
"""

import os
import joblib
import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple, List
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.model_selection import train_test_split
from utils.logging_config import logger

PREPROCESSOR_PATH = os.path.join(os.path.dirname(__file__), "saved", "preprocessor.pkl")

# Numerical features to standardize
NUMERICAL_FEATURES = [
    "age",
    "weight",
    "number_of_health_conditions",
    "number_of_known_allergies",
    "number_of_medicines",
    "medicine_class_count",
    "known_drug_drug_interaction_count",
    "interaction_severity_score",
    "drug_food_interaction_count",
    "symptom_count",
    "severe_symptom_count",
    "age_risk_score",
    "health_condition_risk_score",
    "dosage_risk_score",
    "interaction_risk_score",
    "food_interaction_risk_score",
    "symptom_risk_score"
]

# Categorical features to one-hot encode
CATEGORICAL_FEATURES = [
    "gender",
    "age_group"
]

# Binary / flag features to pass through
BINARY_FEATURES = [
    "kidney_disease",
    "liver_disease",
    "heart_disease",
    "diabetes",
    "duplicate_active_ingredient_flag",
    "dosage_deviation_flag",
    "unknown_dosage_flag",
    "frequency_risk_flag",
    "multiple_medicines_taken_together",
    "drug_alcohol_interaction_flag",
    "supplement_interaction_flag",
    "food_consumed_with_medicine",
    "grapefruit_flag",
    "alcohol_flag",
    "milk_flag",
    "caffeine_flag",
    "herbal_supplement_flag",
    "vitamin_k_food_flag",
    "nausea",
    "vomiting",
    "dizziness",
    "drowsiness",
    "confusion",
    "abdominal_pain",
    "difficulty_breathing",
    "chest_pain",
    "loss_of_consciousness",
    "seizure"
]

ALL_FEATURE_COLUMNS = NUMERICAL_FEATURES + CATEGORICAL_FEATURES + BINARY_FEATURES

def create_preprocessor() -> ColumnTransformer:
    """Builds a scikit-learn ColumnTransformer for numerical, categorical, and binary inputs."""
    preprocessor = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), NUMERICAL_FEATURES),
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CATEGORICAL_FEATURES),
            ("bin", "passthrough", BINARY_FEATURES)
        ],
        remainder="drop"
    )
    return preprocessor

def prepare_train_test_data(
    df: pd.DataFrame,
    test_size: float = 0.20,
    random_state: int = 42
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, ColumnTransformer]:
    """Prepares and transforms training and testing splits."""
    X = df[ALL_FEATURE_COLUMNS].copy()
    y = df["risk_level"].values

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y
    )

    preprocessor = create_preprocessor()
    X_train_transformed = preprocessor.fit_transform(X_train)
    X_test_transformed = preprocessor.transform(X_test)

    # Save preprocessor
    os.makedirs(os.path.dirname(PREPROCESSOR_PATH), exist_ok=True)
    joblib.dump(preprocessor, PREPROCESSOR_PATH)
    logger.info(f"Preprocessor saved to {PREPROCESSOR_PATH}")

    return X_train_transformed, X_test_transformed, y_train, y_test, preprocessor

def get_feature_names(preprocessor: ColumnTransformer) -> List[str]:
    """Extracts human-readable transformed feature names."""
    try:
        return list(preprocessor.get_feature_names_out())
    except Exception:
        # Fallback names
        cat_encoder = preprocessor.named_transformers_["cat"]
        cat_names = list(cat_encoder.get_feature_names_out(CATEGORICAL_FEATURES))
        return NUMERICAL_FEATURES + cat_names + BINARY_FEATURES

def extract_features_from_patient(
    patient: Dict[str, Any],
    medications: List[Dict[str, Any]],
    foods: List[Dict[str, Any]],
    symptoms: List[Dict[str, Any]],
    interaction_data: Dict[str, Any]
) -> pd.DataFrame:
    """
    Constructs a 1-row feature DataFrame from real patient data, active medications,
    foods consumed, current symptoms, and verified interaction analysis results.
    """
    age = int(patient.get("age", 30))
    weight = float(patient.get("weight", 70.0))
    gender = patient.get("gender", "Male")
    if gender not in ["Male", "Female"]:
        gender = "Male"

    # Age group
    if age < 18:
        age_group = "Pediatric (<18)"
    elif age <= 45:
        age_group = "Young Adult (18-45)"
    elif age <= 65:
        age_group = "Middle-aged (46-65)"
    else:
        age_group = "Geriatric (65+)"

    # Conditions
    cond_list = [c.lower() for c in patient.get("conditions", [])]
    kidney = 1 if any("kidney" in c or "renal" in c for c in cond_list) else 0
    liver = 1 if any("liver" in c or "hepatic" in c or "cirrhosis" in c for c in cond_list) else 0
    heart = 1 if any("heart" in c or "cardiac" in c or "cad" in c for c in cond_list) else 0
    diabetes = 1 if any("diabet" in c for c in cond_list) else 0
    num_conditions = len(cond_list)

    # Allergies
    allergies = patient.get("allergies", [])
    num_allergies = len(allergies)

    # Medications
    num_meds = len(medications)
    med_classes = set(m.get("generic_name", m.get("medicine_name", "")) for m in medications)
    class_count = max(1, len(med_classes))

    duplicate_flag = 1 if len(interaction_data.get("duplicates", [])) > 0 else 0

    dosage_dev = 0
    unknown_dose = 0
    freq_risk = 0
    for m in medications:
        p_dose = m.get("prescribed_dosage", "").strip().lower()
        a_dose = m.get("actual_dosage", "").strip().lower()
        if not p_dose or not a_dose or "unknown" in a_dose or "not sure" in a_dose:
            unknown_dose = 1
        elif p_dose != a_dose:
            dosage_dev = 1
        freq = m.get("frequency", "").lower()
        if "as needed" in freq or "prn" in freq or "irregular" in freq:
            freq_risk = 1

    multiple_together = 1 if num_meds > 1 else 0

    # Interactions
    known_dd_count = len(interaction_data.get("drug_drug", []))
    df_count = len(interaction_data.get("drug_food", []))
    severity_score = float(interaction_data.get("interaction_severity_score", 0.0))

    # Foods
    food_cats = [f.get("category", "").lower() for f in foods]
    food_names = [f.get("food_name", "").lower() for f in foods]
    all_food_text = " ".join(food_cats + food_names)

    alcohol_flag = 1 if "alcohol" in all_food_text or "beer" in all_food_text or "wine" in all_food_text else 0
    grapefruit_flag = 1 if "grapefruit" in all_food_text or "citrus" in all_food_text else 0
    milk_flag = 1 if "milk" in all_food_text or "dairy" in all_food_text or "calcium" in all_food_text else 0
    caffeine_flag = 1 if "coffee" in all_food_text or "tea" in all_food_text or "caffeine" in all_food_text else 0
    herbal_flag = 1 if "herbal" in all_food_text or "wort" in all_food_text or "ginkgo" in all_food_text else 0
    vitamin_k_flag = 1 if "spinach" in all_food_text or "kale" in all_food_text or "vitamin k" in all_food_text else 0
    food_consumed_with_med = 1 if any(f.get("relationship_to_med") == "With Medication" for f in foods) else 0

    drug_alcohol_flag = 1 if alcohol_flag and num_meds > 0 else 0
    supp_flag = 1 if herbal_flag and num_meds > 0 else 0

    # Symptoms
    sym_dict = {s.get("symptom_name", "").lower(): s.get("severity", "Mild") for s in symptoms}
    nausea = 1 if "nausea" in sym_dict else 0
    vomiting = 1 if "vomiting" in sym_dict else 0
    dizziness = 1 if "dizziness" in sym_dict else 0
    drowsiness = 1 if "drowsiness" in sym_dict else 0
    confusion = 1 if "confusion" in sym_dict else 0
    abdominal_pain = 1 if "abdominal pain" in sym_dict or "stomach" in sym_dict else 0
    difficulty_breathing = 1 if "difficulty breathing" in sym_dict or "shortness of breath" in sym_dict else 0
    chest_pain = 1 if "chest pain" in sym_dict else 0
    loss_of_consciousness = 1 if "loss of consciousness" in sym_dict or "fainting" in sym_dict else 0
    seizure = 1 if "seizure" in sym_dict or "seizures" in sym_dict else 0

    symptom_count = len(symptoms)
    severe_symptom_count = sum(
        1 for s in symptoms
        if s.get("severity") == "Severe" or s.get("symptom_name") in [
            "Difficulty Breathing", "Chest Pain", "Loss of Consciousness", "Seizures"
        ]
    )

    # Component Risk Scores
    age_risk_score = 20.0 if age >= 75 else (12.0 if age >= 65 else (10.0 if age < 18 else 4.0))
    health_cond_risk = min(30.0, (kidney * 14.0) + (liver * 14.0) + (heart * 10.0) + (diabetes * 6.0))
    dosage_risk = min(35.0, (dosage_dev * 22.0) + (unknown_dose * 10.0) + (freq_risk * 12.0) + (duplicate_flag * 15.0))
    interaction_risk = min(35.0, (known_dd_count * 18.0) + (severity_score * 0.35) + (multiple_together * 5.0))
    food_risk = min(25.0, (drug_alcohol_flag * 20.0) + (df_count * 12.0) + (supp_flag * 10.0))
    symptom_risk = min(45.0, (symptom_count * 5.0) + (severe_symptom_count * 25.0))

    row_data = {
        "age": age,
        "age_group": age_group,
        "weight": weight,
        "gender": gender,
        "kidney_disease": kidney,
        "liver_disease": liver,
        "heart_disease": heart,
        "diabetes": diabetes,
        "number_of_health_conditions": num_conditions,
        "number_of_known_allergies": num_allergies,
        "number_of_medicines": num_meds,
        "medicine_class_count": class_count,
        "duplicate_active_ingredient_flag": duplicate_flag,
        "dosage_deviation_flag": dosage_dev,
        "unknown_dosage_flag": unknown_dose,
        "frequency_risk_flag": freq_risk,
        "multiple_medicines_taken_together": multiple_together,
        "known_drug_drug_interaction_count": known_dd_count,
        "interaction_severity_score": severity_score,
        "drug_food_interaction_count": df_count,
        "drug_alcohol_interaction_flag": drug_alcohol_flag,
        "supplement_interaction_flag": supp_flag,
        "food_consumed_with_medicine": food_consumed_with_med,
        "grapefruit_flag": grapefruit_flag,
        "alcohol_flag": alcohol_flag,
        "milk_flag": milk_flag,
        "caffeine_flag": caffeine_flag,
        "herbal_supplement_flag": herbal_flag,
        "vitamin_k_food_flag": vitamin_k_flag,
        "symptom_count": symptom_count,
        "nausea": nausea,
        "vomiting": vomiting,
        "dizziness": dizziness,
        "drowsiness": drowsiness,
        "confusion": confusion,
        "abdominal_pain": abdominal_pain,
        "difficulty_breathing": difficulty_breathing,
        "chest_pain": chest_pain,
        "loss_of_consciousness": loss_of_consciousness,
        "seizure": seizure,
        "severe_symptom_count": severe_symptom_count,
        "age_risk_score": age_risk_score,
        "health_condition_risk_score": health_cond_risk,
        "dosage_risk_score": dosage_risk,
        "interaction_risk_score": interaction_risk,
        "food_interaction_risk_score": food_risk,
        "symptom_risk_score": symptom_risk
    }

    return pd.DataFrame([row_data])
