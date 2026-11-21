"""
NSBM EduSphere — Deterministic GPA and Academic Records Engine
Provides standard grading calculations, GPA/CGPA determinations,
credit completion audits, academic standing rules, and verifiable digital transcript signatures.
"""
from typing import List, Dict, Any, Tuple
import hashlib
import json
import secrets


GRADE_SCALE: Dict[str, float] = {
    "A+": 4.0,
    "A":  4.0,
    "A-": 3.7,
    "B+": 3.3,
    "B":  3.0,
    "B-": 2.7,
    "C+": 2.3,
    "C":  2.0,
    "C-": 1.7,
    "D+": 1.3,
    "D":  1.0,
    "F":  0.0,
}


def score_to_letter_grade(score: float) -> Tuple[str, float]:
    """Convert numeric score (0-100) to standard letter grade and grade points."""
    if score >= 90:
        return "A+", 4.0
    elif score >= 85:
        return "A", 4.0
    elif score >= 80:
        return "A-", 3.7
    elif score >= 75:
        return "B+", 3.3
    elif score >= 70:
        return "B", 3.0
    elif score >= 65:
        return "B-", 2.7
    elif score >= 60:
        return "C+", 2.3
    elif score >= 55:
        return "C", 2.0
    elif score >= 50:
        return "C-", 1.7
    elif score >= 45:
        return "D+", 1.3
    elif score >= 40:
        return "D", 1.0
    else:
        return "F", 0.0


def calculate_gpa(courses_and_grades: List[Dict[str, Any]]) -> Tuple[float, int, int]:
    """
    Calculate GPA, credits attempted, and credits earned.
    courses_and_grades format: [{'credits': int, 'grade_points': float, 'letter_grade': str}]
    Returns (gpa, credits_attempted, credits_earned).
    """
    total_quality_points = 0.0
    credits_attempted = 0
    credits_earned = 0

    for item in courses_and_grades:
        cr = item.get("credits", 0)
        gp = item.get("grade_points")
        letter = item.get("letter_grade", "F")

        if gp is None:
            gp = GRADE_SCALE.get(letter, 0.0)

        credits_attempted += cr
        total_quality_points += gp * cr

        # Passing grades (C- and above, or non-F) earn academic credits
        if letter not in {"F", "W", "I", "INC"}:
            credits_earned += cr

    gpa = round(total_quality_points / credits_attempted, 2) if credits_attempted > 0 else 0.0
    return gpa, credits_attempted, credits_earned


def evaluate_academic_standing(cgpa: float, attempted_credits: int) -> str:
    """
    Determine institutional academic standing:
    - deans_list: CGPA >= 3.70 with at least 12 attempted credits
    - good_standing: CGPA >= 2.00
    - academic_probation: 1.50 <= CGPA < 2.00
    - academic_suspension: CGPA < 1.50 (or critical failure)
    """
    if attempted_credits >= 12 and cgpa >= 3.70:
        return "deans_list"
    elif cgpa >= 2.00:
        return "good_standing"
    elif cgpa >= 1.50:
        return "academic_probation"
    else:
        return "academic_suspension"


def generate_transcript_signature(data_snapshot: Dict[str, Any]) -> Tuple[str, str]:
    """
    Generate verifiable transcript verification code and SHA-256 digital signature hash.
    Returns (verification_code, signature_hash).
    """
    verification_code = secrets.token_urlsafe(24)
    canonical_repr = json.dumps(data_snapshot, sort_keys=True, default=str)
    signature_hash = hashlib.sha256(f"{verification_code}:{canonical_repr}".encode("utf-8")).hexdigest()
    return verification_code, signature_hash
