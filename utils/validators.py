"""
DoseWeave - Input Validators and Sanitizers
Provides strict data validation for patient demographics, medication entries,
dosages, and dietary inputs.
"""

from typing import Tuple, List, Optional
import re

def validate_patient_profile(
    name: str,
    age: int,
    gender: str,
    weight: float,
    height: float
) -> Tuple[bool, List[str]]:
    """Validate patient demographic entries."""
    errors = []
    if not name or len(name.strip()) < 2:
        errors.append("Patient name must be at least 2 characters.")
    if age < 0 or age > 125:
        errors.append("Age must be between 0 and 125.")
    if gender not in ["Male", "Female", "Other", "Prefer not to say"]:
        errors.append("Please select a valid gender option.")
    if weight <= 0 or weight > 400:
        errors.append("Weight must be between 1 and 400 kg.")
    if height <= 0 or height > 270:
        errors.append("Height must be between 10 and 270 cm.")
    return (len(errors) == 0, errors)

def validate_medication_entry(
    name: str,
    strength: str,
    prescribed_dosage: str,
    actual_dosage: str,
    frequency: str
) -> Tuple[bool, List[str]]:
    """Validate medication inputs."""
    errors = []
    if not name or len(name.strip()) < 2:
        errors.append("Medicine name is required.")
    if not strength or len(strength.strip()) == 0:
        errors.append("Medicine strength (e.g. 500mg) is required.")
    if not prescribed_dosage or len(prescribed_dosage.strip()) == 0:
        errors.append("Prescribed dosage is required.")
    if not actual_dosage or len(actual_dosage.strip()) == 0:
        errors.append("Actual dosage taken is required.")
    if not frequency or len(frequency.strip()) == 0:
        errors.append("Frequency (e.g. Once daily) is required.")
    return (len(errors) == 0, errors)

def detect_dosage_discrepancy(prescribed: str, actual: str) -> bool:
    """
    Detects if actual dosage differs from prescribed dosage.
    Returns True if a likely deviation exists.
    """
    p = prescribed.strip().lower()
    a = actual.strip().lower()
    if p == a:
        return False
    # Extract numbers if available
    p_num = re.findall(r"\d+(?:\.\d+)?", p)
    a_num = re.findall(r"\d+(?:\.\d+)?", a)
    if p_num and a_num and p_num[0] != a_num[0]:
        return True
    return p != a

def sanitize_text(text: Optional[str]) -> str:
    """Strip unnecessary whitespace and clean strings."""
    if not text:
        return ""
    return text.strip()
