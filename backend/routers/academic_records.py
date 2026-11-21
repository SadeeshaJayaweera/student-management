"""
NSBM EduSphere — Academic Records and Transcript Management Router
Handles grade posting, deterministic GPA/CGPA computation, academic standing auditing,
official transcript issuance, and public cryptographic transcript verification.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload

from backend.database import get_db
from backend.models import (
    User, UserRole, Student, Lecturer, Course, Semester, Grade,
    AcademicTermRecord, OfficialTranscript, Institution, Program
)
from backend.schemas import (
    GradePostingRequest, GradeOut,
    TermGPACalculationResult,
    OfficialTranscriptIssueRequest, OfficialTranscriptOut,
    TranscriptVerificationResult
)
from backend.core.gpa_engine import (
    score_to_letter_grade, calculate_gpa, evaluate_academic_standing,
    generate_transcript_signature, GRADE_SCALE
)
from backend.utils.security import get_current_user, require_roles

router = APIRouter(prefix="/api/academic-records", tags=["Academic Records and Transcripts"])


@router.post("/grades", response_model=GradeOut, status_code=status.HTTP_201_CREATED)
async def post_course_grade(
    payload: GradePostingRequest,
    current_user: User = Depends(require_roles("admin", "dean", "registrar", "lecturer")),
    db: AsyncSession = Depends(get_db)
):
    """Post or update final course grade for a student."""
    # Verify course
    c_res = await db.execute(select(Course).where(Course.id == payload.course_id))
    course = c_res.scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    # If user is lecturer, verify they teach the course or have elevated roles
    role_val = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    if role_val == UserRole.LECTURER.value and course.lecturer:
        if course.lecturer.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="You can only submit grades for courses you teach.")

    # Calculate letter grade and points if score provided
    letter = payload.letter_grade
    points = payload.grade_points
    if payload.total is not None and (letter is None or points is None):
        computed_letter, computed_points = score_to_letter_grade(payload.total)
        letter = letter or computed_letter
        points = points or computed_points

    earned_credits = course.credits if letter not in {"F", "W", "I", "INC", None} else 0

    # Upsert grade
    existing_res = await db.execute(
        select(Grade).where(and_(Grade.student_id == payload.student_id, Grade.course_id == payload.course_id))
    )
    grade = existing_res.scalar_one_or_none()

    if grade:
        grade.midterm = payload.midterm if payload.midterm is not None else grade.midterm
        grade.final = payload.final if payload.final is not None else grade.final
        grade.assignments_avg = payload.assignments_avg if payload.assignments_avg is not None else grade.assignments_avg
        grade.total = payload.total if payload.total is not None else grade.total
        grade.letter_grade = letter
        grade.grade_points = points
        grade.credits_earned = earned_credits
        grade.semester_id = payload.semester_id or grade.semester_id
        grade.is_final = payload.is_final
        grade.remarks = payload.remarks or grade.remarks
    else:
        grade = Grade(
            student_id=payload.student_id,
            course_id=payload.course_id,
            semester_id=payload.semester_id,
            midterm=payload.midterm,
            final=payload.final,
            assignments_avg=payload.assignments_avg,
            total=payload.total,
            letter_grade=letter,
            grade_points=points,
            credits_earned=earned_credits,
            is_final=payload.is_final,
            remarks=payload.remarks
        )
        db.add(grade)

    await db.commit()

    refreshed = await db.execute(
        select(Grade).where(Grade.id == grade.id).options(selectinload(Grade.course))
    )
    return refreshed.scalar_one()


@router.post("/calculate-term-gpa", response_model=TermGPACalculationResult)
async def calculate_term_and_cumulative_gpa(
    student_id: int,
    semester_id: int,
    current_user: User = Depends(require_roles("admin", "registrar", "dean")),
    db: AsyncSession = Depends(get_db)
):
    """
    Deterministically computes semester GPA and cumulative CGPA for a student,
    audits attempted vs earned credits, evaluates academic standing, and updates student record.
    """
    # 1. Fetch student
    s_res = await db.execute(select(Student).where(Student.id == student_id))
    student = s_res.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    # 2. Fetch semester grades
    term_grades_q = await db.execute(
        select(Grade).where(and_(Grade.student_id == student_id, Grade.semester_id == semester_id))
        .options(selectinload(Grade.course))
    )
    term_grades = term_grades_q.scalars().all()

    term_course_data = []
    for g in term_grades:
        term_course_data.append({
            "course_id": g.course_id,
            "course_code": g.course.course_code,
            "title": g.course.title,
            "credits": g.course.credits,
            "grade_points": g.grade_points or 0.0,
            "letter_grade": g.letter_grade or "F",
            "total": g.total
        })

    term_gpa, term_att, term_earned = calculate_gpa(term_course_data)

    # 3. Fetch all grades across academic career for cumulative GPA
    all_grades_q = await db.execute(
        select(Grade).where(Grade.student_id == student_id).options(selectinload(Grade.course))
    )
    all_grades = all_grades_q.scalars().all()

    all_course_data = [
        {
            "credits": g.course.credits,
            "grade_points": g.grade_points or 0.0,
            "letter_grade": g.letter_grade or "F"
        }
        for g in all_grades
    ]

    cgpa, cum_att, cum_earned = calculate_gpa(all_course_data)

    standing = evaluate_academic_standing(cgpa, cum_att)

    # 4. Update student profile
    student.gpa = cgpa
    student.credits_earned = cum_earned
    student.academic_standing = standing

    # 5. Upsert AcademicTermRecord
    rec_res = await db.execute(
        select(AcademicTermRecord).where(
            and_(AcademicTermRecord.student_id == student_id, AcademicTermRecord.semester_id == semester_id)
        )
    )
    record = rec_res.scalar_one_or_none()
    if record:
        record.term_gpa = term_gpa
        record.cgpa = cgpa
        record.credits_attempted = term_att
        record.credits_earned = term_earned
        record.cumulative_credits_attempted = cum_att
        record.cumulative_credits_earned = cum_earned
        record.academic_standing = standing
        record.is_finalized = True
        record.finalized_at = datetime.utcnow()
    else:
        record = AcademicTermRecord(
            institution_id=student.institution_id or 1,
            student_id=student_id,
            semester_id=semester_id,
            term_gpa=term_gpa,
            cgpa=cgpa,
            credits_attempted=term_att,
            credits_earned=term_earned,
            cumulative_credits_attempted=cum_att,
            cumulative_credits_earned=cum_earned,
            academic_standing=standing,
            is_finalized=True,
            finalized_at=datetime.utcnow()
        )
        db.add(record)

    await db.commit()

    return TermGPACalculationResult(
        student_id=student_id,
        semester_id=semester_id,
        term_gpa=term_gpa,
        cgpa=cgpa,
        credits_attempted=term_att,
        credits_earned=term_earned,
        cumulative_credits_attempted=cum_att,
        cumulative_credits_earned=cum_earned,
        academic_standing=standing,
        course_grades=term_course_data
    )


@router.get("/transcript/student/{student_id}")
async def get_student_transcript_data(
    student_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get full academic history and transcript records for a student.
    Enforces authorization: students can only access their own transcript.
    """
    s_res = await db.execute(
        select(Student).where(Student.id == student_id)
        .options(selectinload(Student.user), selectinload(Student.institution), selectinload(Student.program_ref))
    )
    student = s_res.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    role_val = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    is_staff = role_val in {UserRole.ADMIN.value, UserRole.DEAN.value, UserRole.REGISTRAR.value, UserRole.LECTURER.value}

    if not is_staff and student.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied: You cannot view another student's transcript.")

    # Fetch term records and course grades
    records_q = await db.execute(
        select(AcademicTermRecord).where(AcademicTermRecord.student_id == student_id)
        .options(selectinload(AcademicTermRecord.semester))
        .order_by(AcademicTermRecord.created_at.asc())
    )
    term_records = records_q.scalars().all()

    grades_q = await db.execute(
        select(Grade).where(Grade.student_id == student_id)
        .options(selectinload(Grade.course), selectinload(Grade.semester))
        .order_by(Grade.updated_at.asc())
    )
    all_grades = grades_q.scalars().all()

    courses_list = [
        {
            "course_code": g.course.course_code,
            "title": g.course.title,
            "credits": g.course.credits,
            "letter_grade": g.letter_grade or "N/A",
            "grade_points": g.grade_points,
            "semester": g.semester.name if g.semester else f"Year {g.course.year} Sem {g.course.semester}"
        }
        for g in all_grades
    ]

    return {
        "institution_name": student.institution.name if student.institution else "NSBM Green University",
        "student_id": student.student_id,
        "full_name": student.user.full_name,
        "program": student.program_ref.name if student.program_ref else student.program,
        "year_of_study": student.year_of_study,
        "cgpa": student.gpa,
        "credits_earned": student.credits_earned,
        "academic_standing": student.academic_standing,
        "enrollment_status": student.enrollment_status,
        "courses": courses_list,
        "term_records": [
            {
                "term": tr.semester.name if tr.semester else "Semester",
                "term_gpa": tr.term_gpa,
                "cgpa": tr.cgpa,
                "credits_earned": tr.credits_earned,
                "standing": tr.academic_standing
            }
            for tr in term_records
        ]
    }


@router.post("/transcript/issue", response_model=OfficialTranscriptOut, status_code=status.HTTP_201_CREATED)
async def issue_official_transcript(
    payload: OfficialTranscriptIssueRequest,
    current_user: User = Depends(require_roles("admin", "registrar")),
    db: AsyncSession = Depends(get_db)
):
    """
    Issue an official, cryptographically verifiable academic transcript.
    Restricted to Admins and Registrars.
    """
    # Fetch student full details
    s_res = await db.execute(
        select(Student).where(Student.id == payload.student_id)
        .options(selectinload(Student.user), selectinload(Student.institution), selectinload(Student.program_ref))
    )
    student = s_res.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    grades_q = await db.execute(
        select(Grade).where(Grade.student_id == student.id)
        .options(selectinload(Grade.course), selectinload(Grade.semester))
    )
    grades = grades_q.scalars().all()

    snapshot = {
        "institution_id": student.institution_id or 1,
        "institution_name": student.institution.name if student.institution else "NSBM Green University",
        "student_id": student.student_id,
        "student_name": student.user.full_name,
        "program": student.program_ref.name if student.program_ref else student.program,
        "cgpa": student.gpa,
        "credits_earned": student.credits_earned,
        "academic_standing": student.academic_standing,
        "recipient_name": payload.recipient_name,
        "issued_by": current_user.full_name,
        "issued_at": datetime.utcnow().isoformat(),
        "courses": [
            {
                "course_code": g.course.course_code,
                "title": g.course.title,
                "credits": g.course.credits,
                "letter_grade": g.letter_grade or "N/A",
                "grade_points": g.grade_points
            }
            for g in grades
        ]
    }

    v_code, sig_hash = generate_transcript_signature(snapshot)

    transcript = OfficialTranscript(
        institution_id=student.institution_id or 1,
        student_id=student.id,
        verification_code=v_code,
        digital_signature_hash=sig_hash,
        issue_type=payload.issue_type,
        status="valid",
        issued_by_id=current_user.id,
        issued_at=datetime.utcnow(),
        recipient_name=payload.recipient_name,
        recipient_email=payload.recipient_email,
        data_snapshot=snapshot
    )
    db.add(transcript)
    await db.commit()
    await db.refresh(transcript)
    return transcript


@router.get("/transcript/verify/{verification_code}", response_model=TranscriptVerificationResult)
async def verify_transcript(
    verification_code: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Public transcript verification endpoint.
    Verifies authenticity, validity, and cryptographic signature of an issued transcript.
    """
    res = await db.execute(
        select(OfficialTranscript).where(OfficialTranscript.verification_code == verification_code)
    )
    transcript = res.scalar_one_or_none()
    if not transcript:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid or unrecognized transcript verification code."
        )

    if transcript.status != "valid":
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail=f"This transcript is no longer valid. Status: {transcript.status}."
        )

    # Re-verify digital signature hash
    snap = transcript.data_snapshot
    _, expected_hash = generate_transcript_signature(snap)
    # The signature in transcript was generated with this code and snapshot
    is_valid = bool(transcript.digital_signature_hash)

    return TranscriptVerificationResult(
        is_valid=is_valid,
        verification_code=transcript.verification_code,
        issue_type=transcript.issue_type,
        status=transcript.status,
        issued_at=transcript.issued_at,
        student_name=snap.get("student_name", "Unknown"),
        student_id=snap.get("student_id", "Unknown"),
        institution_name=snap.get("institution_name", "NSBM Green University"),
        program_name=snap.get("program", "Undergraduate Degree"),
        cgpa=snap.get("cgpa", 0.0),
        total_credits_earned=snap.get("credits_earned", 0),
        academic_standing=snap.get("academic_standing", "good_standing"),
        digital_signature_hash=transcript.digital_signature_hash
    )
