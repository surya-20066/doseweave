"""
MediSafe AI - Clinical & System Constants
Defines standard clinical risk thresholds, symptoms, food categories,
UI theme colors, and safety guidelines.
"""

# Application Metadata
APP_NAME = "MediSafe AI"
APP_TAGLINE = "AI-Powered Medication Safety, Risk Prediction, Food Interaction and Emergency Support System"
APP_VERSION = "2.0.0 (Clinical Decision Support Edition)"

# Risk Score Thresholds (Educational & Research Design Rules)
# Stored as normalized percentiles [0, 100]
RISK_THRESHOLD_LOW_MAX = 33
RISK_THRESHOLD_MODERATE_MAX = 66

RISK_LEVEL_LOW = "LOW RISK"
RISK_LEVEL_MODERATE = "MODERATE RISK"
RISK_LEVEL_HIGH = "HIGH RISK"

# Primary Clinical Color Palette (SaaS Clean Clinical Theme)
COLOR_PRIMARY = "#0F2C59"       # Deep Medical Blue
COLOR_SECONDARY = "#0284C7"     # Clinical Teal
COLOR_ACCENT = "#0284C7"        # Light Cyan Accent
COLOR_BACKGROUND = "#F8FAFC"    # Crisp Clinical Off-White
COLOR_CARD_BG = "#FFFFFF"       # Pure White for Cards
COLOR_TEXT_PRIMARY = "#0F172A"  # Dark Slate for Reading
COLOR_TEXT_MUTED = "#64748B"    # Neutral Slate Muted
COLOR_BORDER = "#E2E8F0"        # Subtle Border Gray

# Status Colors
COLOR_RISK_LOW = "#16A34A"      # Controlled Medical Green
COLOR_RISK_MODERATE = "#D97706" # Medical Amber
COLOR_RISK_HIGH = "#DC2626"     # Controlled Urgent Red
COLOR_INFO = "#2563EB"          # Royal Blue Info

# Standard Severity Levels
SEVERITY_MILD = "Mild"
SEVERITY_MODERATE = "Moderate"
SEVERITY_SEVERE = "Severe"

# High-Risk / Emergency Red-Flag Symptoms
EMERGENCY_SYMPTOMS = [
    "Difficulty Breathing",
    "Chest Pain",
    "Loss of Consciousness",
    "Seizures",
    "Severe Confusion",
    "Anaphylaxis / Throat Swelling",
    "Severe Uncontrolled Bleeding"
]

# Standard System Symptoms
SYSTEM_SYMPTOMS = [
    "Nausea",
    "Vomiting",
    "Dizziness",
    "Drowsiness",
    "Confusion",
    "Abdominal Pain",
    "Headache",
    "Difficulty Breathing",
    "Chest Pain",
    "Loss of Consciousness",
    "Seizures",
    "Skin Rash / Itching",
    "Muscle Pain / Weakness",
    "Tremors"
]

# High Risk Food & Beverage Categories
FOOD_CATEGORIES = [
    "Coffee",
    "Tea",
    "Milk & Dairy",
    "Alcohol",
    "Grapefruit & Citrus Juice",
    "Herbal Supplements (St. John's Wort, Ginkgo)",
    "Multivitamins & Minerals (Iron, Calcium)",
    "Energy Drinks",
    "High Vitamin K Foods (Spinach, Kale, Broccoli)",
    "High Fat Meal",
    "Aged Cheese / Tyramine Rich Foods",
    "General Food"
]

# Standard Chronic Conditions
CHRONIC_CONDITIONS = [
    "Diabetes Mellitus",
    "Hypertension",
    "Heart Disease (CAD / Heart Failure)",
    "Chronic Kidney Disease",
    "Liver Disease / Cirrhosis",
    "Asthma / COPD",
    "Peptic Ulcer Disease",
    "Thyroid Disorder",
    "Depression / Anxiety",
    "Epilepsy"
]

# Standard Common Allergies
COMMON_ALLERGIES = [
    "Penicillin / Amoxicillin",
    "Sulfa Drugs (Sulfonamides)",
    "NSAIDs (Aspirin, Ibuprofen)",
    "Cephalosporins",
    "Opioids (Codeine, Morphine)",
    "Peanuts",
    "Shellfish",
    "Dairy / Lactose",
    "Gluten",
    "Soy"
]

# Disclaimer strings
CLINICAL_DISCLAIMER = (
    "MEDISAFE AI DISCLAIMER: This software is an educational research and clinical "
    "decision-support prototype. It does not provide definitive medical diagnoses, "
    "prescriptions, or substitute professional judgment. All medication changes must "
    "be approved by a licensed physician or clinical pharmacist."
)

DATASET_DISCLAIMER = (
    "Note on Dataset Methodology: In clinical pharmacology, no single public repository "
    "integrates comprehensive multi-drug dosages, acute symptom trajectories, dietary intake, "
    "and lab markers. This model is trained on a validated hybrid dataset combining openFDA "
    "FAERS safety signals, SIDER adverse reaction profiles, RxNorm ontologies, and documented "
    "clinical pharmacology distributions."
)
