"""
DoseWeave - SQLite Database Schema
Defines DDL tables for users, patients, medical history, allergies, medications,
food tracking, symptoms, risk assessments, interactions, clinical recommendations,
medication schedules, scheduled doses, reminder preferences, reminder notifications,
medication adherence records, medicine recognition history, prescription records,
audit logs, and verified drug information monographs.
"""

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT DEFAULT 'patient', -- 'patient', 'admin'
    timezone TEXT DEFAULT 'UTC',
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
    wakeup_time TEXT DEFAULT '07:00',
    bedtime TEXT DEFAULT '22:00',
    breakfast_time TEXT DEFAULT '08:00',
    lunch_time TEXT DEFAULT '13:00',
    dinner_time TEXT DEFAULT '20:00',
    timezone TEXT DEFAULT 'UTC',
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
    dosage_unit TEXT DEFAULT 'mg',
    route TEXT DEFAULT 'Oral',
    frequency TEXT NOT NULL,
    time_taken TEXT,
    duration TEXT,
    start_date TEXT,
    end_date TEXT,
    food_timing TEXT DEFAULT 'Independent', -- 'Before Food', 'With Food', 'After Food', 'Empty Stomach', 'Independent'
    is_prn INTEGER DEFAULT 0,
    instructions TEXT,
    source_type TEXT DEFAULT 'Manual', -- 'Manual', 'Search', 'Image_Recognition', 'Prescription_Analysis'
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
    relationship_to_med TEXT DEFAULT 'With Medication',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(patient_id) REFERENCES patients(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS symptoms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER NOT NULL,
    symptom_name TEXT NOT NULL,
    severity TEXT NOT NULL,
    time_started TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(patient_id) REFERENCES patients(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS risk_assessments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER NOT NULL,
    risk_level TEXT NOT NULL,
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
    interaction_type TEXT NOT NULL,
    item1 TEXT NOT NULL,
    item2 TEXT NOT NULL,
    severity TEXT NOT NULL,
    description TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(assessment_id) REFERENCES risk_assessments(id) ON DELETE CASCADE,
    FOREIGN KEY(patient_id) REFERENCES patients(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS recommendations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    assessment_id INTEGER,
    patient_id INTEGER NOT NULL,
    category TEXT NOT NULL,
    recommendation_text TEXT NOT NULL,
    priority TEXT DEFAULT 'Standard',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(assessment_id) REFERENCES risk_assessments(id) ON DELETE CASCADE,
    FOREIGN KEY(patient_id) REFERENCES patients(id) ON DELETE CASCADE
);

-- =========================================================================
-- DOSEWEAVE ADVANCED SCHEDULING & REMINDER TABLES
-- =========================================================================

CREATE TABLE IF NOT EXISTS medication_schedules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    schedule_name TEXT DEFAULT 'Active Medication Schedule',
    status TEXT DEFAULT 'proposed', -- 'proposed', 'confirmed', 'active', 'archived'
    schedule_data_json TEXT,
    conflict_warnings_json TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    confirmed_at TIMESTAMP,
    FOREIGN KEY(patient_id) REFERENCES patients(id) ON DELETE CASCADE,
    FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS scheduled_doses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    schedule_id INTEGER NOT NULL,
    patient_id INTEGER NOT NULL,
    medication_id INTEGER,
    medicine_name TEXT NOT NULL,
    dose_amount TEXT NOT NULL,
    dose_unit TEXT DEFAULT 'mg',
    scheduled_time TEXT NOT NULL, -- e.g. '08:00', '20:00'
    scheduled_date TEXT,          -- 'YYYY-MM-DD' or NULL (recurring daily)
    instructions TEXT,
    meal_relation TEXT,          -- 'With breakfast', 'Empty stomach', etc.
    status TEXT DEFAULT 'scheduled', -- 'scheduled', 'taken', 'missed', 'snoozed', 'skipped'
    snoozed_until TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(schedule_id) REFERENCES medication_schedules(id) ON DELETE CASCADE,
    FOREIGN KEY(patient_id) REFERENCES patients(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS reminder_preferences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER UNIQUE NOT NULL,
    in_app_enabled INTEGER DEFAULT 1,
    email_enabled INTEGER DEFAULT 0,
    email_address TEXT,
    browser_enabled INTEGER DEFAULT 1,
    sound_enabled INTEGER DEFAULT 1,
    reminder_lead_minutes INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS reminder_notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scheduled_dose_id INTEGER,
    user_id INTEGER NOT NULL,
    patient_id INTEGER NOT NULL,
    channel TEXT NOT NULL, -- 'in_app', 'email', 'browser'
    scheduled_for TIMESTAMP NOT NULL,
    sent_at TIMESTAMP,
    delivery_status TEXT DEFAULT 'pending', -- 'pending', 'sent', 'failed'
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(scheduled_dose_id) REFERENCES scheduled_doses(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS medication_adherence (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scheduled_dose_id INTEGER,
    patient_id INTEGER NOT NULL,
    medicine_name TEXT NOT NULL,
    scheduled_time TEXT NOT NULL,
    action TEXT NOT NULL, -- 'taken', 'missed', 'snoozed'
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    FOREIGN KEY(patient_id) REFERENCES patients(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS medicine_recognition_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    patient_id INTEGER,
    image_filename TEXT,
    identified_name TEXT NOT NULL,
    generic_name TEXT,
    confidence REAL DEFAULT 0.0,
    user_corrected_name TEXT,
    status TEXT DEFAULT 'identified', -- 'identified', 'confirmed', 'rejected'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS prescription_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    patient_id INTEGER,
    image_filename TEXT,
    raw_ocr_text TEXT,
    extracted_json TEXT,
    confirmed_json TEXT,
    status TEXT DEFAULT 'extracted', -- 'extracted', 'confirmed', 'applied_to_schedule'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    action TEXT NOT NULL,
    entity_type TEXT,
    entity_id INTEGER,
    details TEXT,
    ip_address TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS drug_information_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    drug_name TEXT UNIQUE NOT NULL,
    generic_name TEXT,
    drug_class TEXT,
    indications TEXT,
    standard_dosage TEXT,
    administration_guidance TEXT,
    contraindications TEXT,
    common_side_effects TEXT,
    food_interactions TEXT,
    source_attribution TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_medications_patient ON medications(patient_id);
CREATE INDEX IF NOT EXISTS idx_food_patient ON food_entries(patient_id);
CREATE INDEX IF NOT EXISTS idx_symptoms_patient ON symptoms(patient_id);
CREATE INDEX IF NOT EXISTS idx_assessments_patient ON risk_assessments(patient_id);
CREATE INDEX IF NOT EXISTS idx_schedules_patient ON medication_schedules(patient_id);
CREATE INDEX IF NOT EXISTS idx_doses_schedule ON scheduled_doses(schedule_id);
CREATE INDEX IF NOT EXISTS idx_doses_patient ON scheduled_doses(patient_id);
CREATE INDEX IF NOT EXISTS idx_adherence_patient ON medication_adherence(patient_id);
CREATE INDEX IF NOT EXISTS idx_notifications_user ON reminder_notifications(user_id);
"""
