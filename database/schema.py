"""
MediSafe AI - SQLite Database Schema
Defines DDL tables for users, patients, medical history, allergies, medications,
food tracking, symptoms, risk assessments, interactions, and clinical recommendations.
"""

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS patients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL DEFAULT 1,
    name TEXT NOT NULL,
    age INTEGER NOT NULL,
    gender TEXT NOT NULL,
    weight REAL NOT NULL,
    height REAL NOT NULL,
    blood_group TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS medical_conditions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER NOT NULL,
    condition_name TEXT NOT NULL,
    notes TEXT,
    FOREIGN KEY(patient_id) REFERENCES patients(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS allergies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER NOT NULL,
    allergen_name TEXT NOT NULL,
    allergen_type TEXT DEFAULT 'Medicine', -- 'Medicine', 'Food', 'Other'
    severity TEXT DEFAULT 'Moderate',
    FOREIGN KEY(patient_id) REFERENCES patients(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS medications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER NOT NULL,
    medicine_name TEXT NOT NULL,
    generic_name TEXT,
    strength TEXT NOT NULL,
    prescribed_dosage TEXT NOT NULL,
    actual_dosage TEXT NOT NULL,
    number_of_tablets REAL DEFAULT 1,
    frequency TEXT NOT NULL,
    time_taken TEXT,
    duration TEXT,
    reason TEXT,
    expiry_date TEXT,
    relationship TEXT DEFAULT 'Prescribed', -- 'Prescribed', 'Self-Medicated', 'Unknown'
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(patient_id) REFERENCES patients(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS food_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER NOT NULL,
    food_name TEXT NOT NULL,
    category TEXT NOT NULL,
    quantity TEXT,
    time_consumed TEXT,
    relationship_to_med TEXT DEFAULT 'With Medication', -- 'Before Medication', 'With Medication', 'After Medication'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(patient_id) REFERENCES patients(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS symptoms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER NOT NULL,
    symptom_name TEXT NOT NULL,
    severity TEXT NOT NULL, -- 'Mild', 'Moderate', 'Severe'
    time_started TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(patient_id) REFERENCES patients(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS risk_assessments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER NOT NULL,
    risk_level TEXT NOT NULL, -- 'LOW RISK', 'MODERATE RISK', 'HIGH RISK'
    risk_score REAL NOT NULL,
    model_confidence REAL NOT NULL,
    top_factors_json TEXT,
    raw_features_json TEXT,
    emergency_flag INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(patient_id) REFERENCES patients(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS interaction_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    assessment_id INTEGER,
    patient_id INTEGER NOT NULL,
    interaction_type TEXT NOT NULL, -- 'Drug-Drug', 'Drug-Food', 'Drug-Condition', 'Drug-Alcohol'
    item1 TEXT NOT NULL,
    item2 TEXT NOT NULL,
    severity TEXT NOT NULL, -- 'Major', 'Moderate', 'Minor'
    description TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(assessment_id) REFERENCES risk_assessments(id) ON DELETE CASCADE,
    FOREIGN KEY(patient_id) REFERENCES patients(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS recommendations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    assessment_id INTEGER,
    patient_id INTEGER NOT NULL,
    category TEXT NOT NULL, -- 'WHAT TO REVIEW', 'WHAT TO AVOID', 'WHAT TO MONITOR', 'CONSULT PROFESSIONAL'
    recommendation_text TEXT NOT NULL,
    priority TEXT DEFAULT 'Standard',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(assessment_id) REFERENCES risk_assessments(id) ON DELETE CASCADE,
    FOREIGN KEY(patient_id) REFERENCES patients(id) ON DELETE CASCADE
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_medications_patient ON medications(patient_id);
CREATE INDEX IF NOT EXISTS idx_food_patient ON food_entries(patient_id);
CREATE INDEX IF NOT EXISTS idx_symptoms_patient ON symptoms(patient_id);
CREATE INDEX IF NOT EXISTS idx_assessments_patient ON risk_assessments(patient_id);
"""
