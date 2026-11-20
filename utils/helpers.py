"""
DoseWeave - General Utility Helpers
Provides mathematical formulas, distance calculators, formatting helpers, and conversions.
"""

import math
from datetime import datetime
from typing import Optional, Dict, Any, Tuple

def calculate_bmi(weight_kg: float, height_cm: float) -> Tuple[Optional[float], str]:
    """Calculate BMI and return value with clinical category."""
    if weight_kg <= 0 or height_cm <= 0:
        return None, "Unknown"
    height_m = height_cm / 100.0
    bmi = round(weight_kg / (height_m * height_m), 1)
    if bmi < 18.5:
        category = "Underweight"
    elif bmi < 25.0:
        category = "Normal weight"
    elif bmi < 30.0:
        category = "Overweight"
    else:
        category = "Obesity"
    return bmi, category

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate great-circle distance between two geographic coordinates in kilometers."""
    R = 6371.0  # Earth's radius in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 2)

def format_timestamp(ts_str: Optional[str]) -> str:
    """Formats ISO or SQLite timestamp into human-readable clinical time."""
    if not ts_str:
        return "N/A"
    try:
        dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        return dt.strftime("%b %d, %Y - %I:%M %p")
    except Exception:
        return ts_str

def get_age_group(age: int) -> str:
    """Return clinical age group category."""
    if age < 18:
        return "Pediatric (<18)"
    elif age <= 45:
        return "Young Adult (18-45)"
    elif age <= 65:
        return "Middle-aged (46-65)"
    else:
        return "Geriatric (65+)"
