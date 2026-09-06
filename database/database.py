"""
MediSafe AI - SQLite Database Interface
Provides connection management, user authentication, and CRUD operations for
users, patient profiles, medications, foods, symptoms, and risk assessment records.
"""

import sqlite3
import os
import json
import hashlib
from typing import Dict, Any, List, Optional, Tuple
from database.schema import SCHEMA_SQL
from utils.logging_config import logger

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "medisafe.db")
SALT = "medisafe_ai_secure_salt_2026"

def hash_password(password: str) -> str:
    """Hash password using salted SHA-256."""
    return hashlib.sha256((password + SALT).encode("utf-8")).hexdigest()

def verify_password(password: str, password_hash: str) -> bool:
    """Verify input password against stored hash."""
    return hash_password(password) == password_hash

def get_db_connection():
    """Create and return a database connection with dict-like row access."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    """Initializes database schema and ensures default demo user & patient exist."""
    conn = get_db_connection()
    try:
        conn.executescript(SCHEMA_SQL)
        conn.commit()

        cursor = conn.cursor()
        # Migration check: ensure user_id exists on patients table
        cursor.execute("PRAGMA table_info(patients)")
        columns = [row["name"] for row in cursor.fetchall()]
        if "user_id" not in columns:
            cursor.execute("ALTER TABLE patients ADD COLUMN user_id INTEGER DEFAULT 1")
            conn.commit()

        # Seed initial demo user if empty
        cursor.execute("SELECT COUNT(*) FROM users")
        if cursor.fetchone()[0] == 0:
            demo_hash = hash_password("password123")
            cursor.execute("""
                INSERT INTO users (full_name, email, password_hash)
                VALUES ('Dr. Alex Morgan', 'demo@medisafe.ai', ?)
            """, (demo_hash,))
            user_id = cursor.lastrowid

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
            logger.info("Initialized database with default demo user and patient profile.")
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
        cur.execute("SELECT user_id, full_name, email, created_at FROM users WHERE user_id = ?", (user_id,))
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

# Auto-initialize database schema when module is loaded
init_db()
