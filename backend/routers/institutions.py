"""
NSBM EduSphere — Institutional Hierarchy & Campus Management Router
Provides enterprise campus, faculty/school, and department structure management.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.database import get_db
from backend.models import Institution, Campus, Faculty, Department, User, UserRole
from backend.schemas import (
    CampusCreate, CampusUpdate, CampusOut,
    FacultyCreate, FacultyUpdate, FacultyOut,
    DepartmentCreate, DepartmentUpdate, DepartmentOut,
)
from backend.core.dependencies import get_current_user

router = APIRouter(tags=["Institution & Campus Hierarchy"])


def check_institution_admin_access(current_user: User, institution_id: int):
    """Enforces admin privileges within the institution or platform superadmin access"""
    role_val = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    if role_val != UserRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrative privileges required to manage academic hierarchy."
        )
    # If user belongs to a specific institution, ensure they cannot manage another institution
    if current_user.institution_id is not None and current_user.institution_id != institution_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Cannot manage academic structure for another institution."
        )


# ─── Campus Endpoints ──────────────────────────────────────────────────────────

@router.get("/api/institutions/{institution_id}/campuses", response_model=List[CampusOut])
async def list_institution_campuses(
    institution_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all campuses associated with an institution"""
    inst_res = await db.execute(select(Institution).where(Institution.id == institution_id))
    if not inst_res.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Institution not found")

    res = await db.execute(
        select(Campus).where(Campus.institution_id == institution_id).order_by(Campus.name)
    )
    return list(res.scalars().all())


@router.post("/api/institutions/{institution_id}/campuses", response_model=CampusOut, status_code=201)
async def create_campus(
    institution_id: int,
    payload: CampusCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Register a new campus under an institution (Admin only)"""
    check_institution_admin_access(current_user, institution_id)

    inst_res = await db.execute(select(Institution).where(Institution.id == institution_id))
    if not inst_res.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Institution not found")

    code_upper = payload.code.strip().upper()
    existing = await db.execute(
        select(Campus).where(Campus.institution_id == institution_id, Campus.code == code_upper)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Campus with code '{code_upper}' already exists in this institution."
        )

    campus = Campus(
        institution_id=institution_id,
        code=code_upper,
        name=payload.name.strip(),
        address=payload.address,
        city=payload.city,
        state=payload.state,
        country=payload.country,
        contact_email=payload.contact_email,
        contact_phone=payload.contact_phone,
        is_active=payload.is_active,
    )
    db.add(campus)
    await db.commit()
    await db.refresh(campus)
    return campus


@router.get("/api/campuses/{campus_id}", response_model=CampusOut)
async def get_campus(
    campus_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve details of a single campus"""
    res = await db.execute(select(Campus).where(Campus.id == campus_id))
    campus = res.scalar_one_or_none()
    if not campus:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campus not found")
    return campus


@router.put("/api/campuses/{campus_id}", response_model=CampusOut)
async def update_campus(
    campus_id: int,
    payload: CampusUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update details of an existing campus"""
    res = await db.execute(select(Campus).where(Campus.id == campus_id))
    campus = res.scalar_one_or_none()
    if not campus:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campus not found")

    check_institution_admin_access(current_user, campus.institution_id)

    update_data = payload.model_dump(exclude_unset=True)
    if "code" in update_data and update_data["code"]:
        update_data["code"] = update_data["code"].strip().upper()

    for field, val in update_data.items():
        setattr(campus, field, val)

    await db.commit()
    await db.refresh(campus)
    return campus


@router.delete("/api/campuses/{campus_id}", status_code=204)
async def delete_campus(
    campus_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Deactivate or remove a campus"""
    res = await db.execute(select(Campus).where(Campus.id == campus_id))
    campus = res.scalar_one_or_none()
    if not campus:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campus not found")

    check_institution_admin_access(current_user, campus.institution_id)

    await db.delete(campus)
    await db.commit()
    return None


# ─── Faculty / School Endpoints ───────────────────────────────────────────────

@router.get("/api/institutions/{institution_id}/faculties", response_model=List[FacultyOut])
async def list_institution_faculties(
    institution_id: int,
    campus_id: Optional[int] = Query(None, description="Optional campus filter"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all faculties / schools under an institution"""
    inst_res = await db.execute(select(Institution).where(Institution.id == institution_id))
    if not inst_res.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Institution not found")

    q = select(Faculty).where(Faculty.institution_id == institution_id)
    if campus_id is not None:
        q = q.where(Faculty.campus_id == campus_id)

    res = await db.execute(q.order_by(Faculty.name))
    return list(res.scalars().all())


@router.post("/api/institutions/{institution_id}/faculties", response_model=FacultyOut, status_code=201)
async def create_faculty(
    institution_id: int,
    payload: FacultyCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new faculty or school under an institution"""
    check_institution_admin_access(current_user, institution_id)

    inst_res = await db.execute(select(Institution).where(Institution.id == institution_id))
    if not inst_res.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Institution not found")

    if payload.campus_id is not None:
        camp_res = await db.execute(
            select(Campus).where(Campus.id == payload.campus_id, Campus.institution_id == institution_id)
        )
        if not camp_res.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid campus ID for this institution.")

    code_upper = payload.code.strip().upper()
    existing = await db.execute(
        select(Faculty).where(Faculty.institution_id == institution_id, Faculty.code == code_upper)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Faculty with code '{code_upper}' already exists in this institution."
        )

    faculty = Faculty(
        institution_id=institution_id,
        campus_id=payload.campus_id,
        code=code_upper,
        name=payload.name.strip(),
        description=payload.description,
        dean_name=payload.dean_name,
        contact_email=payload.contact_email,
        is_active=payload.is_active,
    )
    db.add(faculty)
    await db.commit()
    await db.refresh(faculty)
    return faculty


@router.get("/api/faculties/{faculty_id}", response_model=FacultyOut)
async def get_faculty(
    faculty_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve details of a single faculty / school"""
    res = await db.execute(select(Faculty).where(Faculty.id == faculty_id))
    faculty = res.scalar_one_or_none()
    if not faculty:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Faculty not found")
    return faculty


@router.put("/api/faculties/{faculty_id}", response_model=FacultyOut)
async def update_faculty(
    faculty_id: int,
    payload: FacultyUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update details of an existing faculty"""
    res = await db.execute(select(Faculty).where(Faculty.id == faculty_id))
    faculty = res.scalar_one_or_none()
    if not faculty:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Faculty not found")

    check_institution_admin_access(current_user, faculty.institution_id)

    update_data = payload.model_dump(exclude_unset=True)
    if "code" in update_data and update_data["code"]:
        update_data["code"] = update_data["code"].strip().upper()

    for field, val in update_data.items():
        setattr(faculty, field, val)

    await db.commit()
    await db.refresh(faculty)
    return faculty


@router.delete("/api/faculties/{faculty_id}", status_code=204)
async def delete_faculty(
    faculty_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Remove a faculty / school"""
    res = await db.execute(select(Faculty).where(Faculty.id == faculty_id))
    faculty = res.scalar_one_or_none()
    if not faculty:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Faculty not found")

    check_institution_admin_access(current_user, faculty.institution_id)

    await db.delete(faculty)
    await db.commit()
    return None


# ─── Department Endpoints ─────────────────────────────────────────────────────

@router.get("/api/faculties/{faculty_id}/departments", response_model=List[DepartmentOut])
async def list_faculty_departments(
    faculty_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all departments under a faculty"""
    fac_res = await db.execute(select(Faculty).where(Faculty.id == faculty_id))
    if not fac_res.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Faculty not found")

    res = await db.execute(
        select(Department).where(Department.faculty_id == faculty_id).order_by(Department.name)
    )
    return list(res.scalars().all())


@router.post("/api/faculties/{faculty_id}/departments", response_model=DepartmentOut, status_code=201)
async def create_department(
    faculty_id: int,
    payload: DepartmentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Register a new department under a faculty"""
    fac_res = await db.execute(select(Faculty).where(Faculty.id == faculty_id))
    faculty = fac_res.scalar_one_or_none()
    if not faculty:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Faculty not found")

    check_institution_admin_access(current_user, faculty.institution_id)

    code_upper = payload.code.strip().upper()
    existing = await db.execute(
        select(Department).where(Department.faculty_id == faculty_id, Department.code == code_upper)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Department with code '{code_upper}' already exists in this faculty."
        )

    dept = Department(
        institution_id=faculty.institution_id,
        faculty_id=faculty_id,
        code=code_upper,
        name=payload.name.strip(),
        description=payload.description,
        head_of_department=payload.head_of_department,
        contact_email=payload.contact_email,
        is_active=payload.is_active,
    )
    db.add(dept)
    await db.commit()
    await db.refresh(dept)
    return dept


@router.get("/api/departments/{department_id}", response_model=DepartmentOut)
async def get_department(
    department_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve details of a single department"""
    res = await db.execute(select(Department).where(Department.id == department_id))
    dept = res.scalar_one_or_none()
    if not dept:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")
    return dept


@router.put("/api/departments/{department_id}", response_model=DepartmentOut)
async def update_department(
    department_id: int,
    payload: DepartmentUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update details of an existing department"""
    res = await db.execute(select(Department).where(Department.id == department_id))
    dept = res.scalar_one_or_none()
    if not dept:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")

    check_institution_admin_access(current_user, dept.institution_id)

    update_data = payload.model_dump(exclude_unset=True)
    if "code" in update_data and update_data["code"]:
        update_data["code"] = update_data["code"].strip().upper()

    for field, val in update_data.items():
        setattr(dept, field, val)

    await db.commit()
    await db.refresh(dept)
    return dept


@router.delete("/api/departments/{department_id}", status_code=204)
async def delete_department(
    department_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Remove a department"""
    res = await db.execute(select(Department).where(Department.id == department_id))
    dept = res.scalar_one_or_none()
    if not dept:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")

    check_institution_admin_access(current_user, dept.institution_id)

    await db.delete(dept)
    await db.commit()
    return None
