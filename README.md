# ✚ DOSEWEAVE
## Clinical Medication Safety & Healthcare Decision Support Platform
> **Smart Medication Safety, Multi-Drug Risk Prediction, Food-Drug Interaction Screening, and Emergency Dispatch Intelligence**

---

## 📋 Table of Contents
1. [Overview & Purpose](#-overview--purpose)
2. [Key Capabilities & Features](#-key-capabilities--features)
3. [The 4-Step Clinical Workflow](#-the-4-step-clinical-workflow)
4. [Quick Demo Credentials](#-quick-demo-credentials)
5. [System Architecture & Tech Stack](#-system-architecture--tech-stack)
6. [Folder Structure](#-folder-structure)
7. [Installation & Setup](#-installation--setup)
8. [Automated Testing & Verification](#-automated-testing--verification)
9. [Clinical Safety & Guardrails](#-clinical-safety--guardrails)

---

## 🩺 Overview & Purpose

**DoseWeave** is an enterprise-grade clinical decision-support and medication safety platform. It helps patients, caregivers, and medical practitioners prevent adverse drug reactions (ADRs), audit multi-drug prescriptions, evaluate food-drug interactions, analyze prescription labels with computer vision, and locate emergency facilities in real time.

### Why DoseWeave?
- **Adverse Drug Event Prevention**: Over 1.5 million preventable medication errors occur annually. DoseWeave detects severe contraindications and harmful interactions *before* consumption.
- **Explainable Machine Learning**: Rather than black-box models, DoseWeave pairs calibrated ML models (96.6% accuracy) with local factor attribution so users understand *why* a risk level is assigned.
- **Multimodal AI Assistance**: Evaluates queries via natural text and extracts medication info from camera photos or scanned labels using Gemini Vision AI.
- **Flexible Navigation**: Work directly on any clinical step at any time without artificial progression locks.

---

## ✨ Key Capabilities & Features

| Feature | Description |
| :--- | :--- |
| **Multi-Drug Interaction Auditing** | Cross-checks prescribed medications against known FDA, SIDER, and RxNorm interaction datasets in real time. |
| **Food & Beverage Contraindications** | Analyzes whether dietary items (e.g., grapefruit juice, dairy, alcohol) interfere with prescription pharmacokinetics. |
| **ML Risk Prediction Engine** | Evaluates patient age, conditions, symptoms, and regimen using trained Random Forest and XGBoost classifiers. |
| **Multimodal Vision OCR** | Upload photos of prescriptions or medication boxes; Gemini Vision AI extracts drug details and provides safety advice. |
| **Dual-Engine Emergency Locator** | Searches nearby hospitals and clinics using your GPS location or manual address with Google Places + OpenStreetMap fallback. |
| **Modern Healthcare SaaS Design** | Ultra-responsive UI featuring ambient glowing themes, glassmorphism cards, and accessibility support. |

---

## 🔄 The 4-Step Clinical Workflow

DoseWeave features an open, flexible 4-step pipeline accessible in any order:

```
[ 1. COLLECT DATA ] ➔ [ 2. ANALYSE RISK ] ➔ [ 3. RECOMMENDATIONS ] ➔ [ 4. NEARBY LOCATIONS ]
```

### 1. Collect User Data (`pages/patient_info.py`)
- Enter patient demographics (Age, Gender, Blood Group, Weight, Height).
- Select chronic conditions (Hypertension, Type 2 Diabetes, Asthma, CKD, etc.) and known allergies.
- Add active prescriptions (Medicine Name, Dosage, Frequency, Start Date).
- Record dietary intake and active symptoms with severity levels.

### 2. Analyse Risk (`pages/risk_prediction.py`)
- Automatically retrieves the saved patient profile from the encrypted SQLite database.
- Runs the offline-trained Machine Learning risk model (`risk_model.pkl` + `preprocessor.pkl`).
- Visualizes results on an interactive risk gauge (Low, Moderate, High, Severe).
- Provides **Explainable AI (XAI)** factor breakdown highlighting specific interaction drivers.

### 3. AI Recommendation System (`pages/ai_analysis.py`)
- **Option A (Ask Using Text)**: Type custom clinical questions or choose common preset queries to receive contextual advice.
- **Option B (Ask Using an Image)**: Upload a prescription photo, medicine bottle label, or document for multimodal OCR extraction.
- **Structured 6-Tier Guidelines**: Generates comprehensive summaries, pharmacological reviews, foods to avoid, and doctor discussion points.

### 4. Nearby Healthcare Locations (`pages/nearby_hospitals.py`)
- Automatically detects current GPS coordinates (via browser geolocation) or accepts manual location queries.
- Finds open 24/7 emergency departments, trauma centers, and clinics with distance calculations.
- Direct Google Maps routing and emergency hotline speed-dials (e.g., 911 / 112).

---

## 🔑 Quick Demo Credentials

For evaluators and rapid testing, a pre-populated clinical demo account is included:

| Role | Email Address | Password |
| :--- | :--- | :--- |
| **Evaluator Demo** | `demo@doseweave.ai` | `password123` |

*(You can also click **CREATE ACCOUNT** on the portal to register any new clinical profile).*

---

## 🛠️ System Architecture & Tech Stack

```
[ Frontend (Streamlit + Modern CSS) ]
                 │
                 ▼
[ Process Router & Session Management (app.py) ]
  ├── Step 1: Patient Intake (pages/patient_info.py)
  ├── Step 2: ML Risk Engine (pages/risk_prediction.py)
  ├── Step 3: AI Analysis (pages/ai_analysis.py)
  └── Step 4: Emergency Facilities (pages/nearby_hospitals.py)
                 │
        ┌────────┴────────┬──────────────────┐
        ▼                 ▼                  ▼
[ Machine Learning ]  [ Database ]   [ External Services ]
- Scikit-Learn        - SQLite       - Google Gemini Vision
- XGBoost             - SHA-256      - Google Places API
- Joblib Models       - SQL Schema   - OpenStreetMap (OSM)
```

- **Frontend & UI**: Streamlit 1.63, Custom Glassmorphic CSS Design System, Responsive Layouts.
- **Machine Learning**: Scikit-Learn, XGBoost, Pandas, NumPy (Trained on 20,000 clinically grounded records).
- **Computer Vision & LLM**: Google Gemini 1.5 Pro / Flash via `google-generativeai`.
- **Database**: SQLite3 with thread-safe connection pooling, user scoping, and SHA-256 password hashing.
- **Geospatial Dispatch**: Haversine distance algorithm, Google Places API with automatic OpenStreetMap Overpass fallback.

---

## 📁 Folder Structure

```
Medical/
├── app.py                          # Application entrypoint & page routing
├── README.md                       # Comprehensive documentation
├── requirements.txt                # Python package dependencies
│
├── pages/                          # Clinical Flow Pages
│   ├── landing_page.py             # Landing page with animations & feature overview
│   ├── auth.py                     # Login & Registration portal
│   ├── process_flow.py             # 4-Step workflow controller (unlocked direct access)
│   ├── patient_info.py             # Step 1: Patient demographics & intake form
│   ├── risk_prediction.py          # Step 2: ML risk classification & XAI gauge
│   ├── ai_analysis.py              # Step 3: AI Text & Image OCR analysis
│   ├── nearby_hospitals.py         # Step 4: Nearby emergency hospital locator
│   ├── dashboard.py                # Executive summary dashboard
│   └── user_profile.py             # User profile & clinical account settings
│
├── components/                     # Reusable UI Components
│   ├── top_nav.py                  # Top navigation bar with logo glow & user avatar
│   ├── header.py                   # Clinical header with active patient badge
│   ├── risk_gauge.py               # Speedometer risk visualization
│   └── emergency_alert.py          # High-acuity warning banners
│
├── models/                         # ML Model Training & Inference
│   ├── predict.py                  # Real-time risk predictor class
│   ├── train_model.py              # Multi-model training pipeline
│   ├── feature_engineering.py      # Column transformers & scalers
│   └── saved/                      # risk_model.pkl & preprocessor.pkl
│
├── services/                       # Business Logic & Integrations
│   ├── interaction_service.py      # Drug-drug and drug-food interaction logic
│   ├── recommendation_service.py   # 5-tier recommendation synthesis engine
│   ├── emergency_service.py        # Acute symptom triage & emergency hotlines
│   ├── hospital_service.py         # Dual-engine GPS hospital locator
│   └── gemini_service.py           # Gemini Vision OCR & medical LLM service
│
├── database/                       # Relational Storage Layer
│   ├── database.py                 # Thread-safe SQLite queries and user auth
│   ├── schema.py                   # DDL table schemas and indexes
│   └── doseweave.db                # SQLite database file
│
├── styles/                         # Styling System
│   └── main.css                    # Modern healthcare light theme & animations
│
└── tests/                          # Automated Verification Suite
    ├── test_database.py            # SQLite CRUD & Authentication tests
    ├── test_interactions.py        # Pharmacological interaction tests
    ├── test_models.py              # ML risk predictions & overrides
    └── run_tests.py                # Command-line test suite runner
```

---

## 🚀 Installation & Setup

### 1. Clone or Open the Workspace
```bash
cd Medical
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure API Keys (`.env`)
Create or edit the `.env` file in the project root:
```env
# Google Gemini API key for multimodal image analysis & prescription OCR
GOOGLE_API_KEY=your_gemini_api_key_here

# Optional: Google Places API key for hospital search (falls back to OpenStreetMap if omitted)
PLACES_API_KEY=your_google_places_api_key_here
```
> *Note: If `PLACES_API_KEY` is not provided, the hospital locator automatically switches to OpenStreetMap Overpass API without requiring payment or credentials.*

### 4. Launch the Web Application
```bash
streamlit run app.py
```
Open your browser at: **`http://localhost:8501`**

---

## 🧪 Automated Testing & Verification

DoseWeave includes an end-to-end automated test suite verifying database integrity, cryptographic authentication, interaction matching, and ML inference.

To execute all tests:
```bash
python tests/run_tests.py
```

### Expected Output:
```text
test_add_and_fetch_medication ... ok
test_create_and_fetch_patient ... ok
test_get_patients ... ok
test_save_complete_patient_data ... ok
test_user_authentication_flow ... ok
test_allergy_cross_reaction ... ok
test_condition_contraindication ... ok
test_drug_drug_interaction ... ok
test_drug_food_interaction ... ok
test_high_risk_emergency_override ... ok
test_low_risk_prediction ... ok
test_model_loaded ... ok

----------------------------------------------------------------------
Ran 13 tests in 0.12s

OK
[SUCCESS] ALL DOSEWEAVE SYSTEM TESTS PASSED SUCCESSFULLY!
```

---

## 🛡️ Clinical Safety & Guardrails

> [!IMPORTANT]
> **Clinical Decision Support Notice**: DoseWeave is built strictly as a decision-support, risk-screening, and educational research tool.
> - It does not provide medical diagnoses or prescribe controlled substances.
> - It does not instruct users to alter prescribed therapy without consulting their physician.
> - Acute emergency symptoms (e.g., chest pain, anaphylaxis) trigger an immediate high-risk override directing users to contact 911 / 112 or visit an emergency room.
