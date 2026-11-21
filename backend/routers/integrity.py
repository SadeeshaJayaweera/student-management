"""
NSBM EduSphere — Academic Integrity and Plagiarism Checks Router
Provides text tokenization, n-gram shingling, peer submission cross-matching,
similarity scoring, originality report generation, and instructor dispute review workflows.
"""
from typing import List, Optional, Set
from datetime import datetime
import hashlib
import re

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, func, desc
from sqlalchemy.orm import selectinload

from backend.database import get_db
from backend.models import (
    User, UserRole, Course, Student, Lecturer,
    Assignment, AssignmentSubmission, PlagiarismScanReport
)
from backend.schemas import (
    PlagiarismReportReview, PlagiarismReportOut, PlagiarismBulkScanResult
)
from backend.utils.security import get_current_user
from backend.core.sanitization import sanitize_rich_content
from backend.routers.assignments import verify_course_assignment_access

router = APIRouter(tags=["Academic Integrity & Plagiarism Checks"])


def compute_ngrams(text: str, n: int = 3) -> Set[str]:
    """Tokenize text into lowercase alpha words and generate n-gram set"""
    words = re.findall(r"\b[a-zA-Z0-9_]+\b", text.lower())
    if len(words) < n:
        return set(words)
    return set(" ".join(words[i:i+n]) for i in range(len(words) - n + 1))


def calculate_jaccard_similarity(text1: str, text2: str) -> float:
    """Calculate Jaccard similarity coefficient between two text bodies using 3-grams"""
    s1 = compute_ngrams(text1, n=3)
    s2 = compute_ngrams(text2, n=3)
    if not s1 or not s2:
        return 0.0
    intersection = s1.intersection(s2)
    union = s1.union(s2)
    if not union:
        return 0.0
    return len(intersection) / len(union)


def serialize_plagiarism_report(report: PlagiarismScanReport) -> PlagiarismReportOut:
    return PlagiarismReportOut(
        id=report.id,
        submission_id=report.submission_id,
        assignment_id=report.assignment_id,
        student_id=report.student_id,
        similarity_score=report.similarity_score,
        status=report.status,
        integrity_flag=report.integrity_flag,
        matched_sources=report.matched_sources or [],
        scanned_content_hash=report.scanned_content_hash,
        instructor_notes=report.instructor_notes,
        reviewed_by_id=report.reviewed_by_id,
        reviewed_at=report.reviewed_at,
        created_at=report.created_at,
        updated_at=report.updated_at,
    )


# ─── Plagiarism Scan Endpoints ────────────────────────────────────────────────

@router.post("/api/assignments/{assignment_id}/submissions/{submission_id}/plagiarism-scan", response_model=PlagiarismReportOut)
async def scan_submission_for_plagiarism(
    assignment_id: int,
    submission_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Execute deep text shingling and peer similarity scan on a student submission.
    Detects collusion with peer cohorts and archives, classifies integrity risk,
    and updates submission originality ratings. (Instructors/Admins only)
    """
    res_asg = await db.execute(select(Assignment).where(Assignment.id == assignment_id))
    assignment = res_asg.scalar_one_or_none()
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
        )

    _, is_instructor_or_admin = await verify_course_assignment_access(assignment.course_id, current_user, db)
    if not is_instructor_or_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only instructors and administrators can trigger plagiarism scans."
        )

    # 1. Load target submission
    res_target = await db.execute(
        select(AssignmentSubmission).where(
            AssignmentSubmission.id == submission_id,
            AssignmentSubmission.assignment_id == assignment_id
        )
    )
    target_sub = res_target.scalar_one_or_none()
    if not target_sub:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found"
        )

    target_text = (target_sub.text_content or "").strip()
    content_hash = hashlib.sha256(target_text.encode()).hexdigest() if target_text else None

    # 2. Load peer candidate submissions for the same assignment
    q_peers = (
        select(AssignmentSubmission)
        .where(
            AssignmentSubmission.assignment_id == assignment_id,
            AssignmentSubmission.id != submission_id,
            AssignmentSubmission.text_content != None
        )
    )
    res_peers = await db.execute(q_peers)
    peers = res_peers.scalars().all()

    matched_sources = []
    max_similarity = 0.0

    if target_text:
        for peer in peers:
            peer_text = (peer.text_content or "").strip()
            if not peer_text:
                continue
            sim = calculate_jaccard_similarity(target_text, peer_text)
            percentage = round(sim * 100.0, 2)
            if percentage > 5.0:  # Threshold for reporting match
                matched_sources.append({
                    "source_submission_id": peer.id,
                    "source_student_id": peer.student_id,
                    "matched_percentage": percentage,
                    "submitted_at": peer.submitted_at.isoformat() if peer.submitted_at else None,
                })
                if percentage > max_similarity:
                    max_similarity = percentage

    # Classify integrity flag
    if max_similarity > 30.0:
        flag = "flagged"
    elif max_similarity >= 15.0:
        flag = "suspicious"
    else:
        flag = "clean"

    # Check for existing report or create
    res_rep = await db.execute(
        select(PlagiarismScanReport).where(PlagiarismScanReport.submission_id == submission_id)
    )
    report = res_rep.scalar_one_or_none()

    if report:
        report.similarity_score = max_similarity
        report.status = "completed"
        report.integrity_flag = flag
        report.matched_sources = matched_sources
        report.scanned_content_hash = content_hash
    else:
        report = PlagiarismScanReport(
            submission_id=submission_id,
            assignment_id=assignment_id,
            student_id=target_sub.student_id,
            similarity_score=max_similarity,
            status="completed",
            integrity_flag=flag,
            matched_sources=matched_sources,
            scanned_content_hash=content_hash,
        )
        db.add(report)

    # Sync back to submission
    target_sub.originality_score = round(max(0.0, 100.0 - max_similarity), 2)
    target_sub.originality_report_url = f"/api/submissions/{submission_id}/plagiarism-report"

    await db.commit()
    await db.refresh(report)

    return serialize_plagiarism_report(report)


@router.post("/api/assignments/{assignment_id}/plagiarism-scan-all", response_model=PlagiarismBulkScanResult)
async def bulk_scan_assignment_submissions(
    assignment_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Execute bulk batch plagiarism scan across all assignment submissions (Instructors/Admins only)"""
    res_asg = await db.execute(select(Assignment).where(Assignment.id == assignment_id))
    assignment = res_asg.scalar_one_or_none()
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
        )

    _, is_instructor_or_admin = await verify_course_assignment_access(assignment.course_id, current_user, db)
    if not is_instructor_or_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only instructors and administrators can run bulk plagiarism scans."
        )

    q_subs = select(AssignmentSubmission).where(AssignmentSubmission.assignment_id == assignment_id)
    res_subs = await db.execute(q_subs)
    submissions = res_subs.scalars().all()

    flagged = 0
    suspicious = 0
    clean = 0

    for sub in submissions:
        target_text = (sub.text_content or "").strip()
        max_similarity = 0.0
        matched_sources = []

        if target_text:
            for peer in submissions:
                if peer.id == sub.id:
                    continue
                peer_text = (peer.text_content or "").strip()
                if not peer_text:
                    continue
                sim = calculate_jaccard_similarity(target_text, peer_text)
                pct = round(sim * 100.0, 2)
                if pct > 5.0:
                    matched_sources.append({
                        "source_submission_id": peer.id,
                        "source_student_id": peer.student_id,
                        "matched_percentage": pct,
                    })
                    if pct > max_similarity:
                        max_similarity = pct

        if max_similarity > 30.0:
            flag = "flagged"
            flagged += 1
        elif max_similarity >= 15.0:
            flag = "suspicious"
            suspicious += 1
        else:
            flag = "clean"
            clean += 1

        sub.originality_score = round(max(0.0, 100.0 - max_similarity), 2)
        sub.originality_report_url = f"/api/submissions/{sub.id}/plagiarism-report"

        # Update or create report
        rep_res = await db.execute(
            select(PlagiarismScanReport).where(PlagiarismScanReport.submission_id == sub.id)
        )
        rep = rep_res.scalar_one_or_none()
        content_hash = hashlib.sha256(target_text.encode()).hexdigest() if target_text else None

        if rep:
            rep.similarity_score = max_similarity
            rep.status = "completed"
            rep.integrity_flag = flag
            rep.matched_sources = matched_sources
            rep.scanned_content_hash = content_hash
        else:
            rep = PlagiarismScanReport(
                submission_id=sub.id,
                assignment_id=assignment_id,
                student_id=sub.student_id,
                similarity_score=max_similarity,
                status="completed",
                integrity_flag=flag,
                matched_sources=matched_sources,
                scanned_content_hash=content_hash,
            )
            db.add(rep)

    await db.commit()

    return PlagiarismBulkScanResult(
        assignment_id=assignment_id,
        submissions_scanned=len(submissions),
        flagged_count=flagged,
        suspicious_count=suspicious,
        clean_count=clean,
    )


@router.get("/api/submissions/{submission_id}/plagiarism-report", response_model=PlagiarismReportOut)
async def get_plagiarism_report(
    submission_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve originality scan results, matched sources, and integrity flags"""
    res_sub = await db.execute(
        select(AssignmentSubmission)
        .where(AssignmentSubmission.id == submission_id)
        .options(
            selectinload(AssignmentSubmission.student),
            selectinload(AssignmentSubmission.assignment).selectinload(Assignment.course)
        )
    )
    submission = res_sub.scalar_one_or_none()
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found"
        )

    # Authorization
    role_val = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    is_admin = role_val in {UserRole.ADMIN.value, UserRole.DEAN.value}
    is_owner = bool(submission.student and submission.student.user_id == current_user.id)

    if not (is_admin or is_owner):
        is_instructor = bool(
            submission.assignment and submission.assignment.course and
            getattr(current_user, "lecturer", None) and
            submission.assignment.course.lecturer_id == current_user.lecturer.id
        )
        if not is_instructor:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You cannot view this plagiarism report."
            )

    res_rep = await db.execute(
        select(PlagiarismScanReport).where(PlagiarismScanReport.submission_id == submission_id)
    )
    report = res_rep.scalar_one_or_none()
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plagiarism report not found. A scan has not yet been executed on this submission."
        )

    return serialize_plagiarism_report(report)


@router.post("/api/plagiarism-reports/{report_id}/review", response_model=PlagiarismReportOut)
async def review_plagiarism_report(
    report_id: int,
    payload: PlagiarismReportReview,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Instructor/Admin manual review, resolution, and citation verification override"""
    res_rep = await db.execute(
        select(PlagiarismScanReport)
        .where(PlagiarismScanReport.id == report_id)
        .options(selectinload(PlagiarismScanReport.assignment).selectinload(Assignment.course))
    )
    report = res_rep.scalar_one_or_none()
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plagiarism report not found"
        )

    course_id = report.assignment.course_id if report.assignment else 0
    _, is_instructor_or_admin = await verify_course_assignment_access(course_id, current_user, db)
    if not is_instructor_or_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only instructors and administrators can review plagiarism reports."
        )

    report.integrity_flag = payload.integrity_flag.lower().strip()
    report.instructor_notes = sanitize_rich_content(payload.instructor_notes) if payload.instructor_notes else None
    report.reviewed_by_id = current_user.id
    report.reviewed_at = datetime.utcnow()

    await db.commit()
    await db.refresh(report)

    return serialize_plagiarism_report(report)
