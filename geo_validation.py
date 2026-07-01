"""
geo_validation.py — Campus GPS Boundary Validation
Smart Campus Attendance System

Uses the Haversine formula to compute great-circle distance
between two GPS coordinates on Earth's surface.
"""

import math
from dataclasses import dataclass
from flask import current_app


# ── Earth radius (mean) ───────────────────────────────────────
EARTH_RADIUS_KM = 6371.0


# ── Result dataclass ─────────────────────────────────────────
@dataclass
class ValidationResult:
    is_valid:        bool
    distance_metres: float
    campus_lat:      float
    campus_lon:      float
    campus_radius:   float
    student_lat:     float
    student_lon:     float
    message:         str


# ============================================================
# CORE FORMULA
# ============================================================
def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Return the great-circle distance in **metres** between two
    points on Earth given their decimal-degree coordinates.

    Parameters
    ----------
    lat1, lon1 : float  — first  point (campus centre)
    lat2, lon2 : float  — second point (student device)

    Returns
    -------
    float — distance in metres
    """
    # Convert degrees → radians
    phi1    = math.radians(lat1)
    phi2    = math.radians(lat2)
    d_phi   = math.radians(lat2 - lat1)
    d_lam   = math.radians(lon2 - lon1)

    # Haversine formula
    a = (math.sin(d_phi / 2) ** 2
         + math.cos(phi1) * math.cos(phi2) * math.sin(d_lam / 2) ** 2)

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return EARTH_RADIUS_KM * c * 1000   # convert km → metres


# ============================================================
# VALIDATION ENTRY POINT
# ============================================================
def validate_campus_location(student_lat: float, student_lon: float) -> ValidationResult:
    """
    Check whether the given coordinates fall inside the
    configured campus boundary.

    Reads CAMPUS_LAT, CAMPUS_LON, CAMPUS_RADIUS from Flask app config.

    Parameters
    ----------
    student_lat : float — latitude  from student's browser
    student_lon : float — longitude from student's browser

    Returns
    -------
    ValidationResult
    """
    campus_lat    = current_app.config['CAMPUS_LAT']
    campus_lon    = current_app.config['CAMPUS_LON']
    campus_radius = current_app.config['CAMPUS_RADIUS']   # metres

    distance = haversine(campus_lat, campus_lon, student_lat, student_lon)
    is_valid = distance <= campus_radius

    if is_valid:
        msg = f'Within campus — {distance:.0f}m from centre (limit {campus_radius:.0f}m)'
    else:
        excess = distance - campus_radius
        msg = f'Outside campus — {distance:.0f}m from centre, {excess:.0f}m beyond limit'

    return ValidationResult(
        is_valid        = is_valid,
        distance_metres = round(distance, 2),
        campus_lat      = campus_lat,
        campus_lon      = campus_lon,
        campus_radius   = campus_radius,
        student_lat     = student_lat,
        student_lon     = student_lon,
        message         = msg,
    )


# ============================================================
# INPUT VALIDATION
# ============================================================
def parse_coords(lat_str: str, lon_str: str) -> tuple[float, float] | None:
    """
    Safely parse latitude / longitude strings from form / JSON input.
    Returns (lat, lon) floats or None on invalid input.
    """
    try:
        lat = float(lat_str)
        lon = float(lon_str)
        # Sanity check ranges
        if not (-90 <= lat <= 90):
            return None
        if not (-180 <= lon <= 180):
            return None
        return lat, lon
    except (TypeError, ValueError):
        return None