"""
NSBM EduSphere — Academic Program & Curriculum Management Router
Manages degree qualifications, programs of study, majors, and specializations.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.database import get_db
from backend.models import Institution, Program, Specialization, Faculty, Department, User, UserRole
from backend.schemas import (
    ProgramCreate, ProgramUpdate, ProgramOut,
    SpecializationCreate, SpecializationUpdate, SpecializationOut,
)
from backend.core.dependencies import get_current_user

router = APIRouter(tags=["Academic Programs & Curriculum"])


def check_program_admin_access(current_user: User, institution_id: int):
    """Enforces admin privileges within the institution or platform superadmin access"""
    role_val = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    if role_val != UserRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrative privileges required to manage programs and curriculum."
        )
    if current_user.institution_id is not None and current_user.institution_id != institution_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Cannot manage academic programs for another institution."
        )


# ─── Program Endpoints ────────────────────────────────────────────────────────

@router.get("/api/institutions/{institution_id}/programs", response_model=List[ProgramOut])
async def list_institution_programs(
    institution_id: int,
    faculty_id: Optional[int] = Query(None, description="Optional faculty filter"),
    department_id: Optional[int] = Query(None, description="Optional department filter"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all degree programs offered by an institution"""
    inst_res = await db.execute(select(Institution).where(Institution.id == institution_id))
    if not inst_res.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Institution not found")

    q = select(Program).where(Program.institution_id == institution_id)
    if faculty_id is not None:
        q = q.where(Program.faculty_id == faculty_id)
    if department_id is not None:
        q = q.where(Program.department_id == department_id)

    res = await db.execute(q.order_by(Program.name))
    return list(res.scalars().all())


@router.post("/api/institutions/{institution_id}/programs", response_model=ProgramOut, status_code=201)
async def create_program(
    institution_id: int,
    payload: ProgramCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new degree program under an institution"""
    check_program_admin_access(current_user, institution_id)

    inst_res = await db.execute(select(Institution).where(Institution.id == institution_id))
    if not inst_res.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Institution not found")

    # Validate faculty and department if provided
    if payload.faculty_id is not None:
        fac_res = await db.execute(
            select(Faculty).where(Faculty.id == payload.faculty_id, Faculty.institution_id == institution_id)
        )
        if not fac_res.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid faculty ID for this institution.")

    if payload.department_id is not None:
        dept_res = await db.execute(
            select(Department).where(Department.id == payload.department_id, Department.institution_id == institution_id)
        )
        if not dept_res.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid department ID for this institution.")

    code_upper = payload.code.strip().upper()
    existing = await db.execute(
        select(Program).where(Program.institution_id == institution_id, Program.code == code_upper)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Program with code '{code_upper}' already exists in this institution."
        )

    prog = Program(
        institution_id=institution_id,
        faculty_id=payload.faculty_id,
        department_id=payload.department_id,
        code=code_upper,
        name=payload.name.strip(),
        qualification=payload.qualification.strip(),
        duration_years=payload.duration_years,
        total_credits=payload.total_credits,
        description=payload.description,
        is_active=payload.is_active,
    )
    db.add(prog)
    await db.commit()
    await db.refresh(prog)
    return prog


@router.get("/api/programs/{program_id}", response_model=ProgramOut)
async def get_program(
    program_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve details of a single degree program"""
    res = await db.execute(select(Program).where(Program.id == program_id))
    prog = res.scalar_one_or_none()
    if not prog:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Program not found")
    return prog


@router.put("/api/programs/{program_id}", response_model=ProgramOut)
async def update_program(
    program_id: int,
    payload: ProgramUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update details of an existing degree program"""
    res = await db.execute(select(Program).where(Program.id == program_id))
    prog = res.scalar_one_or_none()
    if not prog:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Program not found")

    check_program_admin_access(current_user, prog.institution_id)

    update_data = payload.model_dump(exclude_unset=True)
    if "code" in update_data and update_data["code"]:
        update_data["code"] = update_data["code"].strip().upper()

    for field, val in update_data.items():
        setattr(prog, field, val)

    await db.commit()
    await db.refresh(prog)
    return prog


@router.delete("/api/programs/{program_id}", status_code=204)
async def delete_program(
    program_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Remove a degree program"""
    res = await db.execute(select(Program).where(Program.id == program_id))
    prog = res.scalar_one_or_none()
    if not prog:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Program not found")

    check_program_admin_access(current_user, prog.institution_id)

    await db.delete(prog)
    await db.commit()
    return None


# ─── Specialization Endpoints ─────────────────────────────────────────────────

@router.get("/api/programs/{program_id}/specializations", response_model=List[SpecializationOut])
async def list_program_specializations(
    program_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all specialization tracks under a program"""
    prog_res = await db.execute(select(Program).where(Program.id == program_id))
    if not prog_res.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Program not found")

    res = await db.execute(
        select(Specialization)
        .where(Specialization.program_id == program_id)
        .order_by(Specialization.name)
    )
    return list(res.scalars().all())


@router.post("/api/programs/{program_id}/specializations", response_model=SpecializationOut, status_code=201)
async def create_specialization(
    program_id: int,
    payload: SpecializationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Register a new specialization track for a program"""
    prog_res = await db.execute(select(Program).where(Program.id == program_id))
    prog = prog_res.scalar_one_or_none()
    if not prog:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Program not found")

    check_program_admin_access(current_user, prog.institution_id)

    code_upper = payload.code.strip().upper()
    existing = await db.execute(
        select(Specialization).where(
            Specialization.program_id == program_id,
            Specialization.code == code_upper
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Specialization with code '{code_upper}' already exists in this program."
        )

    spec = Specialization(
        institution_id=prog.institution_id,
        program_id=program_id,
        code=code_upper,
        name=payload.name.strip(),
        description=payload.description,
        required_credits=payload.required_credits,
        is_active=payload.is_active,
    )
    db.add(spec)
    await db.commit()
    await db.refresh(spec)
    return spec


@router.get("/api/specializations/{specialization_id}", response_model=SpecializationOut)
async def get_specialization(
    specialization_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve details of a single specialization"""
    res = await db.execute(select(Specialization).where(Specialization.id == specialization_id))
    spec = res.scalar_one_or_none()
    if not spec:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Specialization not found")
    return spec


@router.put("/api/specializations/{specialization_id}", response_model=SpecializationOut)
async def update_specialization(
    specialization_id: int,
    payload: SpecializationUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update details of an existing specialization"""
    res = await db.execute(select(Specialization).where(Specialization.id == specialization_id))
    spec = res.scalar_one_or_none()
    if not spec:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Specialization not found")

    check_program_admin_access(current_user, spec.institution_id)

    update_data = payload.model_dump(exclude_unset=True)
    if "code" in update_data and update_data["code"]:
        update_data["code"] = update_data["code"].strip().upper()

    for field, val in update_data.items():
        setattr(spec, field, val)

    await db.commit()
    await db.refresh(spec)
    return spec


@router.delete("/api/specializations/{specialization_id}", status_code=204)
async def delete_specialization(
    specialization_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Remove a specialization"""
    res = await db.execute(select(Specialization).where(Specialization.id == specialization_id))
    spec = res.scalar_one_or_none()
    if not spec:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Specialization not found")

    check_program_admin_access(current_user, spec.institution_id)

    await db.delete(spec)
    await db.commit()
    return None
