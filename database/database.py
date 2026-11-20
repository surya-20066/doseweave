"""
DoseWeave - SQLite Database Interface
Provides connection management, user authentication, and high-performance CRUD operations for
users, patient profiles, medications, foods, symptoms, and risk assessment records.
"""

import sqlite3
import os
import json
import hashlib
import shutil
from typing import Dict, Any, List, Optional, Tuple
from database.schema import SCHEMA_SQL
from utils.logging_config import logger

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
DB_PATH = os.path.join(DATA_DIR, "doseweave.db")
LEGACY_DB_PATH = os.path.join(DATA_DIR, "medisafe.db")

# Automatically mirror legacy db if doseweave.db does not exist yet
if not os.path.exists(DB_PATH) and os.path.exists(LEGACY_DB_PATH):
    try:
        shutil.copy2(LEGACY_DB_PATH, DB_PATH)
    except Exception:
        pass

SALT = "medisafe_ai_secure_salt_2026"
DOSEWEAVE_SALT = "doseweave_secure_salt_2026"

_DB_INITIALIZED = False

def hash_password(password: str) -> str:
    """Hash password using salted SHA-256."""
    return hashlib.sha256((password + SALT).encode("utf-8")).hexdigest()

def verify_password(password: str, password_hash: str) -> bool:
    """Verify input password against stored hash with backward compatibility."""
    if hash_password(password) == password_hash:
        return True
    if hashlib.sha256((password + DOSEWEAVE_SALT).encode("utf-8")).hexdigest() == password_hash:
        return True
    return False

def get_db_connection():
    """Create and return an optimized database connection with WAL mode and row caching."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA synchronous = NORMAL")
    conn.execute("PRAGMA cache_size = 10000")
    return conn

def _run_migrations(conn):
    """Executes safe, non-destructive schema migrations for existing SQLite databases."""
    cursor = conn.cursor()
    # 1. Users table migrations
    cursor.execute("PRAGMA table_info(users)")
    u_cols = [row["name"] for row in cursor.fetchall()]
    if "role" not in u_cols:
        cursor.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'patient'")
    if "timezone" not in u_cols:
        cursor.execute("ALTER TABLE users ADD COLUMN timezone TEXT DEFAULT 'UTC'")

    # 2. Patients table migrations
    cursor.execute("PRAGMA table_info(patients)")
    p_cols = [row["name"] for row in cursor.fetchall()]
    if "user_id" not in p_cols:
        cursor.execute("ALTER TABLE patients ADD COLUMN user_id INTEGER DEFAULT 1")
    if "wakeup_time" not in p_cols:
        cursor.execute("ALTER TABLE patients ADD COLUMN wakeup_time TEXT DEFAULT '07:00'")
    if "bedtime" not in p_cols:
        cursor.execute("ALTER TABLE patients ADD COLUMN bedtime TEXT DEFAULT '22:00'")
    if "breakfast_time" not in p_cols:
        cursor.execute("ALTER TABLE patients ADD COLUMN breakfast_time TEXT DEFAULT '08:00'")
    if "lunch_time" not in p_cols:
        cursor.execute("ALTER TABLE patients ADD COLUMN lunch_time TEXT DEFAULT '13:00'")
    if "dinner_time" not in p_cols:
        cursor.execute("ALTER TABLE patients ADD COLUMN dinner_time TEXT DEFAULT '20:00'")
    if "timezone" not in p_cols:
        cursor.execute("ALTER TABLE patients ADD COLUMN timezone TEXT DEFAULT 'UTC'")

    # 3. Medications table migrations
    cursor.execute("PRAGMA table_info(medications)")
    m_cols = [row["name"] for row in cursor.fetchall()]
    if "dosage_unit" not in m_cols:
        cursor.execute("ALTER TABLE medications ADD COLUMN dosage_unit TEXT DEFAULT 'mg'")
    if "route" not in m_cols:
        cursor.execute("ALTER TABLE medications ADD COLUMN route TEXT DEFAULT 'Oral'")
    if "start_date" not in m_cols:
        cursor.execute("ALTER TABLE medications ADD COLUMN start_date TEXT")
    if "end_date" not in m_cols:
        cursor.execute("ALTER TABLE medications ADD COLUMN end_date TEXT")
    if "food_timing" not in m_cols:
        cursor.execute("ALTER TABLE medications ADD COLUMN food_timing TEXT DEFAULT 'Independent'")
    if "is_prn" not in m_cols:
        cursor.execute("ALTER TABLE medications ADD COLUMN is_prn INTEGER DEFAULT 0")
    if "instructions" not in m_cols:
        cursor.execute("ALTER TABLE medications ADD COLUMN instructions TEXT")
    if "source_type" not in m_cols:
        cursor.execute("ALTER TABLE medications ADD COLUMN source_type TEXT DEFAULT 'Manual'")

    # 4. Guarantee dedicated administrator account exists
    cursor.execute("SELECT user_id FROM users WHERE LOWER(email) = 'admin@doseweave.ai'")
    admin_row = cursor.fetchone()
    if not admin_row:
        admin_hash = hash_password("admin123")
        cursor.execute("""
            INSERT INTO users (full_name, email, password_hash, role)
            VALUES ('System Administrator', 'admin@doseweave.ai', ?, 'admin')
        """, (admin_hash,))
    else:
        cursor.execute("UPDATE users SET role = 'admin' WHERE LOWER(email) = 'admin@doseweave.ai'")

    conn.commit()

def init_db(force: bool = False):
    """Initializes database schema and ensures default demo user & patient exist (cached for performance)."""
    global _DB_INITIALIZED
    if _DB_INITIALIZED and not force:
        return

    conn = get_db_connection()
    try:
        conn.executescript(SCHEMA_SQL)
        conn.commit()
        _run_migrations(conn)

        cursor = conn.cursor()
        # Seed initial demo user if empty
        cursor.execute("SELECT COUNT(*) FROM users")
        if cursor.fetchone()[0] == 0:
            demo_hash = hash_password("password123")
            cursor.execute("""
                INSERT INTO users (full_name, email, password_hash, role)
                VALUES ('Dr. Alex Morgan', 'demo@doseweave.ai', ?, 'patient')
            """, (demo_hash,))
            user_id = cursor.lastrowid

            # Also add legacy demo alias for convenience
            cursor.execute("""
                INSERT INTO users (full_name, email, password_hash)
                VALUES ('Dr. Alex Morgan', 'demo@medisafe.ai', ?)
            """, (demo_hash,))


            # Seed default patient for demo user
            cursor.execute("""
                INSERT INTO patients (user_id, name, age, gender, weight, height, blood_group)
                VALUES (?, 'Alex Morgan (Sample Profile)', 58, 'Male', 78.5, 175.0, 'O+')
            """, (user_id,))
            patient_id = cursor.lastrowid

            # Sample conditions
            cursor.execute("INSERT INTO medical_conditions (patient_id, condition_name) VALUES (?, ?)", (patient_id, "Hypertension"))
            cursor.execute("INSERT INTO medical_conditions (patient_id, condition_name) VALUES (?, ?)", (patient_id, "Diabetes Mellitus"))

            # Sample allergies
            cursor.execute("INSERT INTO allergies (patient_id, allergen_name, allergen_type, severity) VALUES (?, ?, ?, ?)",
                           (patient_id, "Penicillin", "Medicine", "Severe"))

            # Sample medications
            cursor.execute("""
                INSERT INTO medications (patient_id, medicine_name, generic_name, strength, prescribed_dosage, actual_dosage, number_of_tablets, frequency, duration, reason, relationship)
                VALUES (?, 'Metformin', 'Metformin HCl', '500 mg', '500 mg twice daily', '500 mg twice daily', 1, 'Twice a day', 'Ongoing', 'Type 2 Diabetes', 'Prescribed')
            """, (patient_id,))
            cursor.execute("""
                INSERT INTO medications (patient_id, medicine_name, generic_name, strength, prescribed_dosage, actual_dosage, number_of_tablets, frequency, duration, reason, relationship)
                VALUES (?, 'Lisinopril', 'Lisinopril', '10 mg', '10 mg once daily', '10 mg once daily', 1, 'Once a day', 'Ongoing', 'Hypertension', 'Prescribed')
            """, (patient_id,))

            conn.commit()
            _DB_INITIALIZED = True
            logger.info("Initialized database with default demo user and patient profile.")
        else:
            _DB_INITIALIZED = True
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        conn.rollback()
    finally:
        conn.close()

# ----------------- User Authentication ----------------- #

def create_user(full_name: str, email: str, password: str) -> Tuple[bool, str, Optional[int]]:
    """Registers a new user with hashed password."""
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT user_id FROM users WHERE LOWER(email) = LOWER(?)", (email.strip(),))
        if cur.fetchone():
            return False, "An account with this email already exists.", None

        pw_hash = hash_password(password)
        cur.execute("""
            INSERT INTO users (full_name, email, password_hash)
            VALUES (?, ?, ?)
        """, (full_name.strip(), email.strip().lower(), pw_hash))
        user_id = cur.lastrowid
        conn.commit()
        logger.info(f"Created new user account: {email}")
        return True, "Account created successfully.", user_id
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        return False, f"Registration failed: {str(e)}", None
    finally:
        conn.close()

def verify_user(email: str, password: str) -> Optional[Dict[str, Any]]:
    """Authenticates user and returns user dictionary if successful."""
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE LOWER(email) = LOWER(?)", (email.strip(),))
        row = cur.fetchone()
        if not row:
            return None
        user = dict(row)
        if verify_password(password, user["password_hash"]):
            del user["password_hash"]
            return user
        return None
    finally:
        conn.close()

def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT user_id, full_name, email, role, timezone, created_at FROM users WHERE user_id = ?", (user_id,))
        row = cur.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()

def update_user_profile(user_id: int, full_name: str, email: str) -> Tuple[bool, str]:
    """Updates user full name and email in the SQLite database."""
    full_name = full_name.strip()
    email = email.strip().lower()

    if not full_name:
        return False, "Full name cannot be empty."
    if not email or "@" not in email:
        return False, "Please enter a valid email address."

    conn = get_db_connection()
    try:
        cur = conn.cursor()
        # Check if email is used by another user
        cur.execute("SELECT user_id FROM users WHERE LOWER(email) = ? AND user_id != ?", (email, user_id))
        if cur.fetchone():
            return False, "This email address is already associated with another account."

        cur.execute("""
            UPDATE users
            SET full_name = ?, email = ?
            WHERE user_id = ?
        """, (full_name, email, user_id))
        conn.commit()
        logger.info(f"Updated profile for user {user_id}: {full_name} ({email})")
        return True, "Profile updated successfully."
    except Exception as e:
        logger.error(f"Error updating user profile: {e}")
        return False, f"Failed to update profile: {str(e)}"
    finally:
        conn.close()

def change_user_password(user_id: int, current_password: str, new_password: str) -> Tuple[bool, str]:
    """Verifies current password and updates to new password using salted SHA-256."""
    if not current_password:
        return False, "Please provide your current password."
    if not new_password or len(new_password) < 6:
        return False, "New password must be at least 6 characters long."

    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT password_hash FROM users WHERE user_id = ?", (user_id,))
        row = cur.fetchone()
        if not row:
            return False, "User account not found."

        stored_hash = row["password_hash"]
        if not verify_password(current_password, stored_hash):
            return False, "Current password is incorrect."

        new_hash = hash_password(new_password)
        cur.execute("UPDATE users SET password_hash = ? WHERE user_id = ?", (new_hash, user_id))
        conn.commit()
        logger.info(f"Password updated successfully for user {user_id}.")
        return True, "Password updated successfully."
    except Exception as e:
        logger.error(f"Error changing password: {e}")
        return False, f"Failed to change password: {str(e)}"
    finally:
        conn.close()

# ----------------- User-Scoped Patient CRUD ----------------- #

def get_patient_by_user(user_id: int) -> Optional[Dict[str, Any]]:
    """Fetches the primary patient profile associated with a specific user."""
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM patients WHERE user_id = ? ORDER BY id DESC LIMIT 1", (user_id,))
        row = cur.fetchone()
        if not row:
            return None
        patient = dict(row)
        patient_id = patient["id"]
        cur.execute("SELECT condition_name FROM medical_conditions WHERE patient_id = ?", (patient_id,))
        patient["conditions"] = [r["condition_name"] for r in cur.fetchall()]
        cur.execute("SELECT allergen_name, allergen_type, severity FROM allergies WHERE patient_id = ?", (patient_id,))
        patient["allergies"] = [dict(r) for r in cur.fetchall()]
        return patient
    finally:
        conn.close()

def get_patient(patient_id: int) -> Optional[Dict[str, Any]]:
    """Fetches patient by primary key id."""
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM patients WHERE id = ?", (patient_id,))
        row = cur.fetchone()
        if not row:
            return None
        patient = dict(row)
        cur.execute("SELECT condition_name FROM medical_conditions WHERE patient_id = ?", (patient_id,))
        patient["conditions"] = [r["condition_name"] for r in cur.fetchall()]
        cur.execute("SELECT allergen_name, allergen_type, severity FROM allergies WHERE patient_id = ?", (patient_id,))
        patient["allergies"] = [dict(r) for r in cur.fetchall()]
        return patient
    finally:
        conn.close()

def save_complete_patient_data(
    user_id: int,
    patient_info: Dict[str, Any],
    conditions: List[str],
    allergies: List[Dict[str, str]],
    medications: List[Dict[str, Any]],
    foods: List[Dict[str, Any]],
    symptoms: List[Dict[str, Any]]
) -> int:
    """
    Saves complete patient data linked to user_id:
    Creates or updates patient profile, medical conditions, allergies,
    active medications, food tracking, and symptoms in a single transaction.
    """
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        # Check if patient exists for user
        cur.execute("SELECT id FROM patients WHERE user_id = ? LIMIT 1", (user_id,))
        row = cur.fetchone()

        if row:
            patient_id = row["id"]
            cur.execute("""
                UPDATE patients
                SET name = ?, age = ?, gender = ?, weight = ?, height = ?, blood_group = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (
                patient_info.get("name", "Patient"),
                patient_info.get("age", 30),
                patient_info.get("gender", "Male"),
                patient_info.get("weight", 70.0),
                patient_info.get("height", 170.0),
                patient_info.get("blood_group", "O+"),
                patient_id
            ))
        else:
            cur.execute("""
                INSERT INTO patients (user_id, name, age, gender, weight, height, blood_group)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id,
                patient_info.get("name", "Patient"),
                patient_info.get("age", 30),
                patient_info.get("gender", "Male"),
                patient_info.get("weight", 70.0),
                patient_info.get("height", 170.0),
                patient_info.get("blood_group", "O+")
            ))
            patient_id = cur.lastrowid

        # Update Conditions
        cur.execute("DELETE FROM medical_conditions WHERE patient_id = ?", (patient_id,))
        for cond in conditions:
            if cond and cond.strip():
                cur.execute("INSERT INTO medical_conditions (patient_id, condition_name) VALUES (?, ?)", (patient_id, cond.strip()))

        # Update Allergies
        cur.execute("DELETE FROM allergies WHERE patient_id = ?", (patient_id,))
        for alg in allergies:
            name = alg.get("name", "").strip()
            if name:
                cur.execute("""
                    INSERT INTO allergies (patient_id, allergen_name, allergen_type, severity)
                    VALUES (?, ?, ?, ?)
                """, (patient_id, name, alg.get("type", "Medicine"), alg.get("severity", "Moderate")))

        # Update Medications
        cur.execute("DELETE FROM medications WHERE patient_id = ?", (patient_id,))
        for med in medications:
            m_name = med.get("medicine_name", "").strip()
            if m_name:
                cur.execute("""
                    INSERT INTO medications (
                        patient_id, medicine_name, generic_name, strength, prescribed_dosage,
                        actual_dosage, number_of_tablets, frequency, time_taken, duration,
                        reason, expiry_date, relationship, is_active
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                """, (
                    patient_id,
                    m_name,
                    med.get("generic_name", m_name).strip(),
                    med.get("strength", "Standard").strip(),
                    med.get("prescribed_dosage", "").strip(),
                    med.get("actual_dosage", "").strip(),
                    float(med.get("number_of_tablets", 1.0)),
                    med.get("frequency", "Once daily").strip(),
                    med.get("time_taken", "Morning"),
                    med.get("duration", "Ongoing"),
                    med.get("reason", "").strip(),
                    med.get("expiry_date", ""),
                    med.get("relationship", "Prescribed")
                ))

        # Update Foods
        cur.execute("DELETE FROM food_entries WHERE patient_id = ?", (patient_id,))
        for food in foods:
            f_name = food.get("food_name", "").strip()
            if f_name:
                cur.execute("""
                    INSERT INTO food_entries (patient_id, food_name, category, quantity, time_consumed, relationship_to_med)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    patient_id,
                    f_name,
                    food.get("category", "General Food"),
                    food.get("quantity", "Standard"),
                    food.get("time_consumed", "With Meals"),
                    food.get("relationship_to_med", "With Medication")
                ))

        # Update Symptoms
        cur.execute("DELETE FROM symptoms WHERE patient_id = ?", (patient_id,))
        for sym in symptoms:
            s_name = sym.get("symptom_name", "").strip()
            if s_name:
                cur.execute("""
                    INSERT INTO symptoms (patient_id, symptom_name, severity, time_started)
                    VALUES (?, ?, ?, ?)
                """, (
                    patient_id,
                    s_name,
                    sym.get("severity", "Mild"),
                    sym.get("time_started", "Recent")
                ))

        conn.commit()
        logger.info(f"Saved complete patient data for user {user_id}, patient {patient_id}")
        return patient_id
    except Exception as e:
        logger.error(f"Error saving complete patient data: {e}")
        conn.rollback()
        raise e
    finally:
        conn.close()

# ----------------- Medications / Foods / Symptoms Retrieval ----------------- #

def get_patient_medications(patient_id: int, active_only: bool = True) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        query = "SELECT * FROM medications WHERE patient_id = ?"
        if active_only:
            query += " AND is_active = 1"
        query += " ORDER BY id DESC"
        cur.execute(query, (patient_id,))
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()

def get_patient_foods(patient_id: int) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM food_entries WHERE patient_id = ? ORDER BY id DESC", (patient_id,))
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()

def get_patient_symptoms(patient_id: int) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM symptoms WHERE patient_id = ? ORDER BY id DESC", (patient_id,))
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()

def get_patient_conditions(patient_id: int) -> List[str]:
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT condition_name FROM medical_conditions WHERE patient_id = ?", (patient_id,))
        return [r["condition_name"] for r in cur.fetchall()]
    finally:
        conn.close()

def get_patient_allergies(patient_id: int) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT allergen_name, allergen_type, severity FROM allergies WHERE patient_id = ?", (patient_id,))
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()

def get_patient_assessments(patient_id: int) -> List[Dict[str, Any]]:
    return get_assessment_history(patient_id)

def create_patient(
    name: str,
    age: int,
    gender: str,
    weight: float,
    height: float,
    blood_group: str = "Unknown",
    conditions: Optional[List[str]] = None,
    allergies: Optional[List[Dict[str, Any]]] = None,
    user_id: int = 1
) -> int:
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO patients (user_id, name, age, gender, weight, height, blood_group)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (user_id, name, age, gender, weight, height, blood_group))
        patient_id = cur.lastrowid

        if conditions:
            for c in conditions:
                cur.execute("INSERT INTO medical_conditions (patient_id, condition_name) VALUES (?, ?)", (patient_id, c))

        if allergies:
            for a in allergies:
                cur.execute("""
                    INSERT INTO allergies (patient_id, allergen_name, allergen_type, severity)
                    VALUES (?, ?, ?, ?)
                """, (patient_id, a.get("name") or a.get("allergen_name", ""), a.get("type") or a.get("allergen_type", "Medicine"), a.get("severity", "Moderate")))

        conn.commit()
        return patient_id
    finally:
        conn.close()

def add_medication(patient_id: int, med_data: Dict[str, Any]) -> int:
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO medications (
                patient_id, medicine_name, generic_name, strength, prescribed_dosage,
                actual_dosage, number_of_tablets, frequency, duration, reason, relationship, is_active
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
        """, (
            patient_id,
            med_data.get("medicine_name", ""),
            med_data.get("generic_name", ""),
            med_data.get("strength", "Standard"),
            med_data.get("prescribed_dosage", "Standard"),
            med_data.get("actual_dosage", "Standard"),
            float(med_data.get("number_of_tablets", 1.0)),
            med_data.get("frequency", "Once daily"),
            med_data.get("duration", "Ongoing"),
            med_data.get("reason", ""),
            med_data.get("relationship", "Prescribed")
        ))
        med_id = cur.lastrowid
        conn.commit()
        return med_id
    finally:
        conn.close()

def get_all_patients() -> List[Dict[str, Any]]:
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM patients ORDER BY id DESC")
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()

# ----------------- Risk Assessment & History CRUD ----------------- #

def save_risk_assessment(
    patient_id: int,
    risk_level: str,
    risk_score: float,
    model_confidence: float,
    top_factors: List[str],
    raw_features: Dict[str, Any],
    emergency_flag: int,
    interactions: List[Dict[str, Any]],
    recommendations: List[Dict[str, Any]]
) -> int:
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO risk_assessments (
                patient_id, risk_level, risk_score, model_confidence,
                top_factors_json, raw_features_json, emergency_flag
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            patient_id, risk_level, risk_score, model_confidence,
            json.dumps(top_factors), json.dumps(raw_features), emergency_flag
        ))
        assessment_id = cur.lastrowid

        for item in interactions:
            cur.execute("""
                INSERT INTO interaction_results (
                    assessment_id, patient_id, interaction_type, item1, item2, severity, description
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                assessment_id, patient_id, item.get("type", "Drug-Drug"),
                item.get("item1", ""), item.get("item2", ""), item.get("severity", "Moderate"),
                item.get("description", "")
            ))

        for rec in recommendations:
            cur.execute("""
                INSERT INTO recommendations (
                    assessment_id, patient_id, category, recommendation_text, priority
                ) VALUES (?, ?, ?, ?, ?)
            """, (
                assessment_id, patient_id, rec.get("category", "WHAT TO REVIEW"),
                rec.get("text", ""), rec.get("priority", "Standard")
            ))

        conn.commit()
        return assessment_id
    finally:
        conn.close()

def get_assessment_history(patient_id: Optional[int] = None) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        if patient_id:
            cur.execute("""
                SELECT r.*, p.name as patient_name
                FROM risk_assessments r
                JOIN patients p ON r.patient_id = p.id
                WHERE r.patient_id = ?
                ORDER BY r.created_at DESC
            """, (patient_id,))
        else:
            cur.execute("""
                SELECT r.*, p.name as patient_name
                FROM risk_assessments r
                JOIN patients p ON r.patient_id = p.id
                ORDER BY r.created_at DESC
            """)
        rows = cur.fetchall()
        results = []
        for r in rows:
            d = dict(r)
            d["top_factors"] = json.loads(d["top_factors_json"]) if d["top_factors_json"] else []
            d["raw_features"] = json.loads(d["raw_features_json"]) if d["raw_features_json"] else {}
            results.append(d)
        return results
    finally:
        conn.close()

def get_patient_bundle(user_id: int) -> Dict[str, Any]:
    """
    Fetches the patient profile and all associated medications, foods, symptoms,
    assessment history, active schedule, doses, and reminder preferences in a single structured bundle,
    guaranteeing all lists are non-None.
    """
    patient = get_patient_by_user(user_id)
    if not patient:
        return {
            "patient": None,
            "patient_id": None,
            "medications": [],
            "foods": [],
            "symptoms": [],
            "history": [],
            "schedule": None,
            "doses": [],
            "reminder_preferences": get_reminder_preferences(user_id) if user_id else {}
        }
    patient_id = patient["id"]
    active_sched = get_active_schedule(patient_id)
    doses = get_scheduled_doses(schedule_id=active_sched["id"]) if active_sched else []
    return {
        "patient": patient,
        "patient_id": patient_id,
        "medications": get_patient_medications(patient_id, active_only=True) or [],
        "foods": get_patient_foods(patient_id) or [],
        "symptoms": get_patient_symptoms(patient_id) or [],
        "history": get_assessment_history(patient_id) or [],
        "schedule": active_sched,
        "doses": doses,
        "reminder_preferences": get_reminder_preferences(user_id)
    }

# ----------------- Patient Routine & Preferences ----------------- #

def update_patient_routine(
    patient_id: int,
    wakeup_time: str = "07:00",
    bedtime: str = "22:00",
    breakfast_time: str = "08:00",
    lunch_time: str = "13:00",
    dinner_time: str = "20:00",
    timezone: str = "UTC"
) -> bool:
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            UPDATE patients
            SET wakeup_time = ?, bedtime = ?, breakfast_time = ?, lunch_time = ?, dinner_time = ?, timezone = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (wakeup_time, bedtime, breakfast_time, lunch_time, dinner_time, timezone, patient_id))
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Error updating patient routine: {e}")
        return False
    finally:
        conn.close()

def update_medication(med_id: int, med_data: Dict[str, Any]) -> bool:
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            UPDATE medications
            SET medicine_name = ?, generic_name = ?, strength = ?, prescribed_dosage = ?,
                actual_dosage = ?, number_of_tablets = ?, dosage_unit = ?, route = ?,
                frequency = ?, time_taken = ?, duration = ?, start_date = ?, end_date = ?,
                food_timing = ?, is_prn = ?, instructions = ?, reason = ?
            WHERE id = ?
        """, (
            med_data.get("medicine_name", ""),
            med_data.get("generic_name", ""),
            med_data.get("strength", "Standard"),
            med_data.get("prescribed_dosage", "Standard"),
            med_data.get("actual_dosage", "Standard"),
            float(med_data.get("number_of_tablets", 1.0)),
            med_data.get("dosage_unit", "mg"),
            med_data.get("route", "Oral"),
            med_data.get("frequency", "Once daily"),
            med_data.get("time_taken", "Morning"),
            med_data.get("duration", "Ongoing"),
            med_data.get("start_date"),
            med_data.get("end_date"),
            med_data.get("food_timing", "Independent"),
            1 if med_data.get("is_prn") else 0,
            med_data.get("instructions", ""),
            med_data.get("reason", ""),
            med_id
        ))
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Error updating medication {med_id}: {e}")
        return False
    finally:
        conn.close()

def delete_medication(med_id: int) -> bool:
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM medications WHERE id = ?", (med_id,))
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Error deleting medication {med_id}: {e}")
        return False
    finally:
        conn.close()

# ----------------- Medication Schedules & Doses ----------------- #

def create_or_update_schedule(
    patient_id: int,
    user_id: int,
    schedule_name: str,
    status: str,
    schedule_data_json: str,
    conflict_warnings_json: str,
    doses: List[Dict[str, Any]]
) -> int:
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT id FROM medication_schedules
            WHERE patient_id = ? AND status IN ('active', 'proposed', 'confirmed')
            ORDER BY id DESC LIMIT 1
        """, (patient_id,))
        row = cur.fetchone()
        if row:
            schedule_id = row["id"]
            cur.execute("""
                UPDATE medication_schedules
                SET schedule_name = ?, status = ?, schedule_data_json = ?, conflict_warnings_json = ?, confirmed_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (schedule_name, status, schedule_data_json, conflict_warnings_json, schedule_id))
            cur.execute("DELETE FROM scheduled_doses WHERE schedule_id = ?", (schedule_id,))
        else:
            cur.execute("""
                INSERT INTO medication_schedules (patient_id, user_id, schedule_name, status, schedule_data_json, conflict_warnings_json, confirmed_at)
                VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (patient_id, user_id, schedule_name, status, schedule_data_json, conflict_warnings_json))
            schedule_id = cur.lastrowid

        for d in doses:
            cur.execute("""
                INSERT INTO scheduled_doses (
                    schedule_id, patient_id, medication_id, medicine_name, dose_amount,
                    dose_unit, scheduled_time, scheduled_date, instructions, meal_relation, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                schedule_id,
                patient_id,
                d.get("medication_id"),
                d.get("medicine_name", "").strip(),
                d.get("dose_amount", "1 dose").strip(),
                d.get("dose_unit", "mg").strip(),
                d.get("scheduled_time", "08:00").strip(),
                d.get("scheduled_date"),
                d.get("instructions", "").strip(),
                d.get("meal_relation", "With meal").strip(),
                d.get("status", "scheduled")
            ))

        conn.commit()
        logger.info(f"Saved medication schedule {schedule_id} with {len(doses)} doses for patient {patient_id}")
        return schedule_id
    except Exception as e:
        logger.error(f"Error creating/updating schedule: {e}")
        conn.rollback()
        raise e
    finally:
        conn.close()

def get_active_schedule(patient_id: int) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT * FROM medication_schedules
            WHERE patient_id = ? AND status IN ('active', 'confirmed')
            ORDER BY id DESC LIMIT 1
        """, (patient_id,))
        row = cur.fetchone()
        if not row:
            cur.execute("""
                SELECT * FROM medication_schedules
                WHERE patient_id = ?
                ORDER BY id DESC LIMIT 1
            """, (patient_id,))
            row = cur.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()

def get_scheduled_doses(
    schedule_id: Optional[int] = None,
    patient_id: Optional[int] = None,
    date_str: Optional[str] = None
) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        if schedule_id:
            cur.execute("SELECT * FROM scheduled_doses WHERE schedule_id = ? ORDER BY scheduled_time ASC", (schedule_id,))
        elif patient_id:
            cur.execute("SELECT * FROM scheduled_doses WHERE patient_id = ? ORDER BY scheduled_time ASC", (patient_id,))
        else:
            cur.execute("SELECT * FROM scheduled_doses ORDER BY scheduled_time ASC")
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()

def update_dose_status(dose_id: int, status: str, notes: Optional[str] = None) -> bool:
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            UPDATE scheduled_doses
            SET status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (status, dose_id))

        cur.execute("SELECT patient_id, medicine_name, scheduled_time FROM scheduled_doses WHERE id = ?", (dose_id,))
        d_row = cur.fetchone()
        if d_row:
            cur.execute("""
                INSERT INTO medication_adherence (scheduled_dose_id, patient_id, medicine_name, scheduled_time, action, notes)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (dose_id, d_row["patient_id"], d_row["medicine_name"], d_row["scheduled_time"], status, notes or f"Dose marked as {status}"))

        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Error updating dose status: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def record_adherence(dose_id: int, patient_id: int, medicine_name: str, scheduled_time: str, action: str, notes: Optional[str] = None) -> int:
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO medication_adherence (scheduled_dose_id, patient_id, medicine_name, scheduled_time, action, notes)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (dose_id, patient_id, medicine_name, scheduled_time, action, notes))
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()

def get_adherence_records(patient_id: int, limit: int = 50) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT * FROM medication_adherence
            WHERE patient_id = ?
            ORDER BY recorded_at DESC LIMIT ?
        """, (patient_id, limit))
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()

def get_adherence_stats(patient_id: int) -> Dict[str, Any]:
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM medication_adherence WHERE patient_id = ?", (patient_id,))
        total = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM medication_adherence WHERE patient_id = ? AND action = 'taken'", (patient_id,))
        taken = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM medication_adherence WHERE patient_id = ? AND action = 'missed'", (patient_id,))
        missed = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM medication_adherence WHERE patient_id = ? AND action = 'snoozed'", (patient_id,))
        snoozed = cur.fetchone()[0]
        rate = round((taken / total * 100.0), 1) if total > 0 else 100.0
        return {
            "total": total,
            "taken": taken,
            "missed": missed,
            "snoozed": snoozed,
            "adherence_rate": rate
        }
    finally:
        conn.close()

# ----------------- Reminder Preferences & Notifications ----------------- #

def get_reminder_preferences(user_id: int) -> Dict[str, Any]:
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM reminder_preferences WHERE user_id = ?", (user_id,))
        row = cur.fetchone()
        if row:
            return dict(row)
        # Default preferences
        cur.execute("""
            INSERT INTO reminder_preferences (user_id, in_app_enabled, email_enabled, browser_enabled, sound_enabled, reminder_lead_minutes)
            VALUES (?, 1, 0, 1, 1, 0)
        """, (user_id,))
        conn.commit()
        return {
            "user_id": user_id,
            "in_app_enabled": 1,
            "email_enabled": 0,
            "email_address": "",
            "browser_enabled": 1,
            "sound_enabled": 1,
            "reminder_lead_minutes": 0
        }
    finally:
        conn.close()

def save_reminder_preferences(
    user_id: int,
    in_app_enabled: bool,
    email_enabled: bool,
    email_address: str = "",
    browser_enabled: bool = True,
    sound_enabled: bool = True,
    reminder_lead_minutes: int = 0
) -> bool:
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO reminder_preferences (
                user_id, in_app_enabled, email_enabled, email_address,
                browser_enabled, sound_enabled, reminder_lead_minutes, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id) DO UPDATE SET
                in_app_enabled = excluded.in_app_enabled,
                email_enabled = excluded.email_enabled,
                email_address = excluded.email_address,
                browser_enabled = excluded.browser_enabled,
                sound_enabled = excluded.sound_enabled,
                reminder_lead_minutes = excluded.reminder_lead_minutes,
                updated_at = CURRENT_TIMESTAMP
        """, (
            user_id,
            1 if in_app_enabled else 0,
            1 if email_enabled else 0,
            email_address.strip(),
            1 if browser_enabled else 0,
            1 if sound_enabled else 0,
            reminder_lead_minutes
        ))
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Error saving reminder preferences: {e}")
        return False
    finally:
        conn.close()

def create_reminder_notification(
    scheduled_dose_id: int,
    user_id: int,
    patient_id: int,
    channel: str,
    scheduled_for: str
) -> int:
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO reminder_notifications (scheduled_dose_id, user_id, patient_id, channel, scheduled_for, delivery_status)
            VALUES (?, ?, ?, ?, ?, 'pending')
        """, (scheduled_dose_id, user_id, patient_id, channel, scheduled_for))
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()

def get_due_notifications() -> List[Dict[str, Any]]:
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT n.*, d.medicine_name, d.dose_amount, d.scheduled_time, d.instructions, u.email as user_email
            FROM reminder_notifications n
            JOIN scheduled_doses d ON n.scheduled_dose_id = d.id
            JOIN users u ON n.user_id = u.user_id
            WHERE n.delivery_status = 'pending'
            ORDER BY n.scheduled_for ASC
        """)
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()

def mark_notification_sent(notification_id: int) -> bool:
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            UPDATE reminder_notifications
            SET delivery_status = 'sent', sent_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (notification_id,))
        conn.commit()
        return True
    finally:
        conn.close()

def mark_notification_failed(notification_id: int, error_message: str) -> bool:
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            UPDATE reminder_notifications
            SET delivery_status = 'failed', error_message = ?
            WHERE id = ?
        """, (error_message, notification_id))
        conn.commit()
        return True
    finally:
        conn.close()

def get_user_notifications(user_id: int, limit: int = 30) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT n.*, d.medicine_name, d.dose_amount, d.scheduled_time
            FROM reminder_notifications n
            LEFT JOIN scheduled_doses d ON n.scheduled_dose_id = d.id
            WHERE n.user_id = ?
            ORDER BY n.created_at DESC LIMIT ?
        """, (user_id, limit))
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()

# ----------------- Medicine Recognition & Prescriptions ----------------- #

def save_recognition_record(
    user_id: int,
    patient_id: Optional[int],
    image_filename: str,
    identified_name: str,
    generic_name: Optional[str] = None,
    confidence: float = 0.0,
    user_corrected_name: Optional[str] = None,
    status: str = "identified"
) -> int:
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO medicine_recognition_history (
                user_id, patient_id, image_filename, identified_name,
                generic_name, confidence, user_corrected_name, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, patient_id, image_filename, identified_name, generic_name, confidence, user_corrected_name, status))
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()

def get_recognition_history(user_id: int, limit: int = 20) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT * FROM medicine_recognition_history
            WHERE user_id = ?
            ORDER BY created_at DESC LIMIT ?
        """, (user_id, limit))
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()

def save_prescription_record(
    user_id: int,
    patient_id: Optional[int],
    image_filename: str,
    raw_ocr_text: str,
    extracted_json: str,
    confirmed_json: Optional[str] = None,
    status: str = "extracted"
) -> int:
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO prescription_records (
                user_id, patient_id, image_filename, raw_ocr_text,
                extracted_json, confirmed_json, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (user_id, patient_id, image_filename, raw_ocr_text, extracted_json, confirmed_json, status))
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()

def get_prescription_records(user_id: int, limit: int = 20) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT * FROM prescription_records
            WHERE user_id = ?
            ORDER BY created_at DESC LIMIT ?
        """, (user_id, limit))
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()

# ----------------- Drug Info Cache ----------------- #

def get_cached_drug_info(drug_name: str) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM drug_information_cache WHERE LOWER(drug_name) = LOWER(?)", (drug_name.strip(),))
        row = cur.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()

def save_cached_drug_info(drug_dict: Dict[str, Any]) -> bool:
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO drug_information_cache (
                drug_name, generic_name, drug_class, indications, standard_dosage,
                administration_guidance, contraindications, common_side_effects,
                food_interactions, source_attribution, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(drug_name) DO UPDATE SET
                generic_name = excluded.generic_name,
                drug_class = excluded.drug_class,
                indications = excluded.indications,
                standard_dosage = excluded.standard_dosage,
                administration_guidance = excluded.administration_guidance,
                contraindications = excluded.contraindications,
                common_side_effects = excluded.common_side_effects,
                food_interactions = excluded.food_interactions,
                source_attribution = excluded.source_attribution,
                updated_at = CURRENT_TIMESTAMP
        """, (
            drug_dict.get("drug_name", "").strip(),
            drug_dict.get("generic_name", "").strip(),
            drug_dict.get("drug_class", "").strip(),
            drug_dict.get("indications", "").strip(),
            drug_dict.get("standard_dosage", "").strip(),
            drug_dict.get("administration_guidance", "").strip(),
            drug_dict.get("contraindications", "").strip(),
            drug_dict.get("common_side_effects", "").strip(),
            drug_dict.get("food_interactions", "").strip(),
            drug_dict.get("source_attribution", "DoseWeave Verified Pharmacology Database").strip()
        ))
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Error caching drug info: {e}")
        return False
    finally:
        conn.close()

# ----------------- Audit Logs ----------------- #

def log_audit_event(
    user_id: Optional[int],
    action: str,
    entity_type: Optional[str] = None,
    entity_id: Optional[int] = None,
    details: Optional[str] = None,
    ip_address: Optional[str] = None
) -> int:
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO audit_logs (user_id, action, entity_type, entity_id, details, ip_address)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, action, entity_type, entity_id, details, ip_address))
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()

def get_audit_logs(limit: int = 100, user_id: Optional[int] = None) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        if user_id:
            cur.execute("SELECT * FROM audit_logs WHERE user_id = ? ORDER BY created_at DESC LIMIT ?", (user_id, limit))
        else:
            cur.execute("SELECT * FROM audit_logs ORDER BY created_at DESC LIMIT ?", (limit,))
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()

# ----------------- Admin System Statistics & Inspection ----------------- #

def get_admin_system_stats() -> Dict[str, Any]:
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        stats = {}
        for tbl, key in [
            ("users", "total_users"),
            ("patients", "total_patients"),
            ("medications", "total_medications"),
            ("medication_schedules", "total_schedules"),
            ("scheduled_doses", "total_scheduled_doses"),
            ("medication_adherence", "total_adherence_records"),
            ("reminder_notifications", "total_notifications"),
            ("risk_assessments", "total_assessments"),
            ("medicine_recognition_history", "total_recognitions"),
            ("prescription_records", "total_prescriptions"),
            ("audit_logs", "total_audit_logs")
        ]:
            try:
                cur.execute(f"SELECT COUNT(*) FROM {tbl}")
                stats[key] = cur.fetchone()[0]
            except Exception:
                stats[key] = 0

        # Recent users
        cur.execute("SELECT user_id, full_name, email, role, created_at FROM users ORDER BY created_at DESC LIMIT 10")
        stats["recent_users"] = [dict(r) for r in cur.fetchall()]

        # Notification stats
        try:
            cur.execute("SELECT COUNT(*) FROM reminder_notifications WHERE delivery_status = 'sent'")
            stats["notifications_sent"] = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM reminder_notifications WHERE delivery_status = 'failed'")
            stats["notifications_failed"] = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM reminder_notifications WHERE delivery_status = 'pending'")
            stats["notifications_pending"] = cur.fetchone()[0]
        except Exception:
            stats["notifications_sent"] = 0
            stats["notifications_failed"] = 0
            stats["notifications_pending"] = 0

        return stats
    finally:
        conn.close()

def get_table_data_paginated(
    table_name: str,
    limit: int = 50,
    offset: int = 0,
    search_query: Optional[str] = None
) -> Tuple[List[Dict[str, Any]], int]:
    ALLOWED_TABLES = {
        "users", "patients", "medical_conditions", "allergies",
        "medications", "food_entries", "symptoms", "risk_assessments",
        "interaction_results", "recommendations", "medication_schedules",
        "scheduled_doses", "reminder_preferences", "reminder_notifications",
        "medication_adherence", "medicine_recognition_history",
        "prescription_records", "audit_logs", "drug_information_cache"
    }
    if table_name not in ALLOWED_TABLES:
        return [], 0

    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute(f"SELECT COUNT(*) FROM {table_name}")
        total = cur.fetchone()[0]

        cur.execute(f"SELECT * FROM {table_name} ORDER BY 1 DESC LIMIT ? OFFSET ?", (limit, offset))
        rows = [dict(r) for r in cur.fetchall()]
        return rows, total
    finally:
        conn.close()

def get_table_schema_info(table_name: str) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute(f"PRAGMA table_info({table_name})")
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()

# Auto-initialize database schema when module is loaded
init_db()
