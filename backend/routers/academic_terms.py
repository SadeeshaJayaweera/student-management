"""
NSBM EduSphere — Academic Year & Semester Management Router
Manages academic calendars, semesters, census dates, and course registration periods.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from backend.database import get_db
from backend.models import Institution, AcademicYear, Semester, User, UserRole
from backend.schemas import (
    AcademicYearCreate, AcademicYearUpdate, AcademicYearOut,
    SemesterCreate, SemesterUpdate, SemesterOut,
)
from backend.core.dependencies import get_current_user

router = APIRouter(tags=["Academic Calendar & Terms"])


def check_academic_admin_access(current_user: User, institution_id: int):
    """Enforces admin privileges within the institution or platform superadmin access"""
    role_val = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    if role_val != UserRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrative privileges required to manage academic terms and calendars."
        )
    if current_user.institution_id is not None and current_user.institution_id != institution_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Cannot manage academic terms for another institution."
        )


# ─── Academic Year Endpoints ──────────────────────────────────────────────────

@router.get("/api/institutions/{institution_id}/academic-years", response_model=List[AcademicYearOut])
async def list_academic_years(
    institution_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all academic years for an institution"""
    inst_res = await db.execute(select(Institution).where(Institution.id == institution_id))
    if not inst_res.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Institution not found")

    res = await db.execute(
        select(AcademicYear)
        .where(AcademicYear.institution_id == institution_id)
        .order_by(AcademicYear.start_date.desc())
    )
    return list(res.scalars().all())


@router.post("/api/institutions/{institution_id}/academic-years", response_model=AcademicYearOut, status_code=201)
async def create_academic_year(
    institution_id: int,
    payload: AcademicYearCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new academic year under an institution"""
    check_academic_admin_access(current_user, institution_id)

    inst_res = await db.execute(select(Institution).where(Institution.id == institution_id))
    if not inst_res.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Institution not found")

    if payload.end_date <= payload.start_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Academic year end_date must be strictly after start_date."
        )

    code_upper = payload.code.strip().upper()
    existing = await db.execute(
        select(AcademicYear).where(AcademicYear.institution_id == institution_id, AcademicYear.code == code_upper)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Academic year with code '{code_upper}' already exists in this institution."
        )

    # If is_current is set, clear current flag on other academic years in this institution
    if payload.is_current:
        await db.execute(
            update(AcademicYear)
            .where(AcademicYear.institution_id == institution_id)
            .values(is_current=False)
        )

    ay = AcademicYear(
        institution_id=institution_id,
        code=code_upper,
        name=payload.name.strip(),
        start_date=payload.start_date,
        end_date=payload.end_date,
        is_current=payload.is_current,
        is_active=payload.is_active,
    )
    db.add(ay)
    await db.commit()
    await db.refresh(ay)
    return ay


@router.get("/api/academic-years/{year_id}", response_model=AcademicYearOut)
async def get_academic_year(
    year_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve details of a single academic year"""
    res = await db.execute(select(AcademicYear).where(AcademicYear.id == year_id))
    ay = res.scalar_one_or_none()
    if not ay:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Academic year not found")
    return ay


@router.put("/api/academic-years/{year_id}", response_model=AcademicYearOut)
async def update_academic_year(
    year_id: int,
    payload: AcademicYearUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update details of an existing academic year"""
    res = await db.execute(select(AcademicYear).where(AcademicYear.id == year_id))
    ay = res.scalar_one_or_none()
    if not ay:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Academic year not found")

    check_academic_admin_access(current_user, ay.institution_id)

    update_data = payload.model_dump(exclude_unset=True)
    if "code" in update_data and update_data["code"]:
        update_data["code"] = update_data["code"].strip().upper()

    if update_data.get("is_current") is True:
        await db.execute(
            update(AcademicYear)
            .where(AcademicYear.institution_id == ay.institution_id)
            .values(is_current=False)
        )

    for field, val in update_data.items():
        setattr(ay, field, val)

    await db.commit()
    await db.refresh(ay)
    return ay


@router.post("/api/academic-years/{year_id}/set-current", response_model=AcademicYearOut)
async def set_current_academic_year(
    year_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Designate an academic year as the active current term for the institution"""
    res = await db.execute(select(AcademicYear).where(AcademicYear.id == year_id))
    ay = res.scalar_one_or_none()
    if not ay:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Academic year not found")

    check_academic_admin_access(current_user, ay.institution_id)

    await db.execute(
        update(AcademicYear)
        .where(AcademicYear.institution_id == ay.institution_id)
        .values(is_current=False)
    )
    ay.is_current = True
    ay.is_active = True
    await db.commit()
    await db.refresh(ay)
    return ay


@router.delete("/api/academic-years/{year_id}", status_code=204)
async def delete_academic_year(
    year_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete an academic year and its associated semesters"""
    res = await db.execute(select(AcademicYear).where(AcademicYear.id == year_id))
    ay = res.scalar_one_or_none()
    if not ay:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Academic year not found")

    check_academic_admin_access(current_user, ay.institution_id)

    await db.delete(ay)
    await db.commit()
    return None


# ─── Semester Endpoints ───────────────────────────────────────────────────────

@router.get("/api/academic-years/{year_id}/semesters", response_model=List[SemesterOut])
async def list_semesters(
    year_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all semesters under an academic year"""
    ay_res = await db.execute(select(AcademicYear).where(AcademicYear.id == year_id))
    if not ay_res.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Academic year not found")

    res = await db.execute(
        select(Semester)
        .where(Semester.academic_year_id == year_id)
        .order_by(Semester.term_number, Semester.start_date)
    )
    return list(res.scalars().all())


@router.post("/api/academic-years/{year_id}/semesters", response_model=SemesterOut, status_code=201)
async def create_semester(
    year_id: int,
    payload: SemesterCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new semester / term under an academic year"""
    ay_res = await db.execute(select(AcademicYear).where(AcademicYear.id == year_id))
    ay = ay_res.scalar_one_or_none()
    if not ay:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Academic year not found")

    check_academic_admin_access(current_user, ay.institution_id)

    if payload.end_date <= payload.start_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Semester end_date must be strictly after start_date."
        )

    code_upper = payload.code.strip().upper()
    existing = await db.execute(
        select(Semester).where(Semester.academic_year_id == year_id, Semester.code == code_upper)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Semester with code '{code_upper}' already exists in this academic year."
        )

    # If is_current is set, clear current flag on other semesters in this institution
    if payload.is_current:
        await db.execute(
            update(Semester)
            .where(Semester.institution_id == ay.institution_id)
            .values(is_current=False)
        )

    semester = Semester(
        institution_id=ay.institution_id,
        academic_year_id=year_id,
        code=code_upper,
        name=payload.name.strip(),
        term_number=payload.term_number,
        start_date=payload.start_date,
        end_date=payload.end_date,
        census_date=payload.census_date,
        registration_start_date=payload.registration_start_date,
        registration_end_date=payload.registration_end_date,
        add_drop_deadline=payload.add_drop_deadline,
        exam_start_date=payload.exam_start_date,
        exam_end_date=payload.exam_end_date,
        is_current=payload.is_current,
        is_active=payload.is_active,
    )
    db.add(semester)
    await db.commit()
    await db.refresh(semester)
    return semester


@router.get("/api/semesters/{semester_id}", response_model=SemesterOut)
async def get_semester(
    semester_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve details of a single semester"""
    res = await db.execute(select(Semester).where(Semester.id == semester_id))
    semester = res.scalar_one_or_none()
    if not semester:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Semester not found")
    return semester


@router.put("/api/semesters/{semester_id}", response_model=SemesterOut)
async def update_semester(
    semester_id: int,
    payload: SemesterUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update details of an existing semester"""
    res = await db.execute(select(Semester).where(Semester.id == semester_id))
    semester = res.scalar_one_or_none()
    if not semester:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Semester not found")

    check_academic_admin_access(current_user, semester.institution_id)

    update_data = payload.model_dump(exclude_unset=True)
    if "code" in update_data and update_data["code"]:
        update_data["code"] = update_data["code"].strip().upper()

    if update_data.get("is_current") is True:
        await db.execute(
            update(Semester)
            .where(Semester.institution_id == semester.institution_id)
            .values(is_current=False)
        )

    for field, val in update_data.items():
        setattr(semester, field, val)

    await db.commit()
    await db.refresh(semester)
    return semester


@router.post("/api/semesters/{semester_id}/set-current", response_model=SemesterOut)
async def set_current_semester(
    semester_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Designate a semester as the current active term for course registrations and teaching"""
    res = await db.execute(select(Semester).where(Semester.id == semester_id))
    semester = res.scalar_one_or_none()
    if not semester:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Semester not found")

    check_academic_admin_access(current_user, semester.institution_id)

    await db.execute(
        update(Semester)
        .where(Semester.institution_id == semester.institution_id)
        .values(is_current=False)
    )
    semester.is_current = True
    semester.is_active = True
    await db.commit()
    await db.refresh(semester)
    return semester


@router.get("/api/institutions/{institution_id}/semesters/current", response_model=Optional[SemesterOut])
async def get_current_institution_semester(
    institution_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve the current active semester for an institution"""
    res = await db.execute(
        select(Semester)
        .where(Semester.institution_id == institution_id, Semester.is_current == True)
    )
    return res.scalar_one_or_none()


@router.delete("/api/semesters/{semester_id}", status_code=204)
async def delete_semester(
    semester_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Remove a semester"""
    res = await db.execute(select(Semester).where(Semester.id == semester_id))
    semester = res.scalar_one_or_none()
    if not semester:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Semester not found")

    check_academic_admin_access(current_user, semester.institution_id)

    await db.delete(semester)
    await db.commit()
    return None
