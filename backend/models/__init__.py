"""
NSBM EduSphere — All Database Models
"""
import enum
from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Text,
    ForeignKey, Enum, Date, JSON, BigInteger
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.database import Base


# ─── Enums ────────────────────────────────────────────────────────────────────

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    STUDENT = "student"
    LECTURER = "lecturer"
    ALUMNI = "alumni"
    LIBRARIAN = "librarian"
    REGISTRAR = "registrar"
    DEAN = "dean"
    GUARDIAN = "guardian"

class BookStatus(str, enum.Enum):
    AVAILABLE = "available"
    BORROWED = "borrowed"
    RESERVED = "reserved"
    MAINTENANCE = "maintenance"

class BorrowStatus(str, enum.Enum):
    ACTIVE = "active"
    RETURNED = "returned"
    OVERDUE = "overdue"

class NewsCategory(str, enum.Enum):
    ACADEMIC = "academic"
    SPORTS = "sports"
    EVENTS = "events"
    ALUMNI = "alumni"
    GENERAL = "general"
    RESEARCH = "research"

class ClubCategory(str, enum.Enum):
    SPORTS = "sports"
    ACADEMIC = "academic"
    CULTURAL = "cultural"
    TECHNICAL = "technical"
    SOCIAL = "social"

class AttendanceStatus(str, enum.Enum):
    PRESENT = "present"
    ABSENT = "absent"
    LATE = "late"
    EXCUSED = "excused"

class AssignmentStatus(str, enum.Enum):
    PENDING = "pending"
    SUBMITTED = "submitted"
    GRADED = "graded"
    LATE = "late"

class UserAccountStatus(str, enum.Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    PENDING_ACTIVATION = "pending_activation"
    DEACTIVATED = "deactivated"

class InvitationStatus(str, enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REVOKED = "revoked"
    EXPIRED = "expired"

class AuditSeverity(str, enum.Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


# ─── Multi-Tenant Institution Model ──────────────────────────────────────────

class Institution(Base):
    __tablename__ = "institutions"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    subdomain = Column(String(100), unique=True, index=True, nullable=True)
    domain = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    settings = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    users = relationship("User", back_populates="institution")
    students = relationship("Student", back_populates="institution")
    courses = relationship("Course", back_populates="institution")
    campuses = relationship("Campus", back_populates="institution", cascade="all, delete-orphan")
    faculties = relationship("Faculty", back_populates="institution", cascade="all, delete-orphan")
    departments = relationship("Department", back_populates="institution", cascade="all, delete-orphan")
    academic_years = relationship("AcademicYear", back_populates="institution", cascade="all, delete-orphan")
    semesters = relationship("Semester", back_populates="institution", cascade="all, delete-orphan")
    programs = relationship("Program", back_populates="institution", cascade="all, delete-orphan")
    lecturers = relationship("Lecturer", back_populates="institution", cascade="all, delete-orphan")


class Campus(Base):
    __tablename__ = "campuses"

    id = Column(Integer, primary_key=True, index=True)
    institution_id = Column(Integer, ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False, index=True)
    code = Column(String(50), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    address = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    country = Column(String(100), default="Sri Lanka", nullable=False)
    contact_email = Column(String(255), nullable=True)
    contact_phone = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    institution = relationship("Institution", back_populates="campuses")
    faculties = relationship("Faculty", back_populates="campus")


class Faculty(Base):
    __tablename__ = "faculties"

    id = Column(Integer, primary_key=True, index=True)
    institution_id = Column(Integer, ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False, index=True)
    campus_id = Column(Integer, ForeignKey("campuses.id", ondelete="SET NULL"), nullable=True, index=True)
    code = Column(String(50), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    dean_name = Column(String(255), nullable=True)
    contact_email = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    institution = relationship("Institution", back_populates="faculties")
    campus = relationship("Campus", back_populates="faculties")
    departments = relationship("Department", back_populates="faculty", cascade="all, delete-orphan")
    programs = relationship("Program", back_populates="faculty")


class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    institution_id = Column(Integer, ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False, index=True)
    faculty_id = Column(Integer, ForeignKey("faculties.id", ondelete="CASCADE"), nullable=False, index=True)
    code = Column(String(50), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    head_of_department = Column(String(255), nullable=True)
    contact_email = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    institution = relationship("Institution", back_populates="departments")
    faculty = relationship("Faculty", back_populates="departments")
    programs = relationship("Program", back_populates="department")


class AcademicYear(Base):
    __tablename__ = "academic_years"

    id = Column(Integer, primary_key=True, index=True)
    institution_id = Column(Integer, ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False, index=True)
    code = Column(String(50), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    is_current = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    institution = relationship("Institution", back_populates="academic_years")
    semesters = relationship("Semester", back_populates="academic_year", cascade="all, delete-orphan")


class Semester(Base):
    __tablename__ = "semesters"

    id = Column(Integer, primary_key=True, index=True)
    institution_id = Column(Integer, ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False, index=True)
    academic_year_id = Column(Integer, ForeignKey("academic_years.id", ondelete="CASCADE"), nullable=False, index=True)
    code = Column(String(50), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    term_number = Column(Integer, default=1, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    census_date = Column(Date, nullable=True)
    registration_start_date = Column(Date, nullable=True)
    registration_end_date = Column(Date, nullable=True)
    add_drop_deadline = Column(Date, nullable=True)
    exam_start_date = Column(Date, nullable=True)
    exam_end_date = Column(Date, nullable=True)
    is_current = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    institution = relationship("Institution", back_populates="semesters")
    academic_year = relationship("AcademicYear", back_populates="semesters")


class Program(Base):
    __tablename__ = "programs"

    id = Column(Integer, primary_key=True, index=True)
    institution_id = Column(Integer, ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False, index=True)
    faculty_id = Column(Integer, ForeignKey("faculties.id", ondelete="SET NULL"), nullable=True, index=True)
    department_id = Column(Integer, ForeignKey("departments.id", ondelete="SET NULL"), nullable=True, index=True)
    code = Column(String(50), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    qualification = Column(String(50), default="BSc", nullable=False)
    duration_years = Column(Float, default=4.0, nullable=False)
    total_credits = Column(Integer, default=120, nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    institution = relationship("Institution", back_populates="programs")
    faculty = relationship("Faculty", back_populates="programs")
    department = relationship("Department", back_populates="programs")
    specializations = relationship("Specialization", back_populates="program", cascade="all, delete-orphan")


class Specialization(Base):
    __tablename__ = "specializations"

    id = Column(Integer, primary_key=True, index=True)
    institution_id = Column(Integer, ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False, index=True)
    program_id = Column(Integer, ForeignKey("programs.id", ondelete="CASCADE"), nullable=False, index=True)
    code = Column(String(50), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    required_credits = Column(Integer, default=30, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    institution = relationship("Institution")
    program = relationship("Program", back_populates="specializations")


# ─── Core User Model ──────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    institution_id = Column(Integer, ForeignKey("institutions.id", ondelete="SET NULL"), nullable=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.STUDENT)
    avatar_url = Column(String(500), nullable=True)
    phone = Column(String(20), nullable=True)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    last_login = Column(DateTime, nullable=True)
    failed_login_attempts = Column(Integer, default=0, nullable=False)
    locked_until = Column(DateTime, nullable=True)
    password_changed_at = Column(DateTime, default=func.now(), nullable=False)
    is_mfa_enabled = Column(Boolean, default=False, nullable=False)
    mfa_secret = Column(String(255), nullable=True)
    mfa_backup_codes = Column(JSON, nullable=True)
    account_status = Column(Enum(UserAccountStatus), nullable=False, default=UserAccountStatus.ACTIVE)
    suspended_at = Column(DateTime, nullable=True)
    suspended_reason = Column(String(255), nullable=True)
    suspended_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    institution = relationship("Institution", back_populates="users")
    student = relationship("Student", back_populates="user", uselist=False, cascade="all, delete-orphan")
    lecturer = relationship("Lecturer", back_populates="user", uselist=False, cascade="all, delete-orphan")
    alumni = relationship("Alumni", back_populates="user", uselist=False, cascade="all, delete-orphan")
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
    assigned_roles = relationship("UserRoleAssignment", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    messages = relationship("Message", foreign_keys="Message.sender_id", back_populates="sender")


class UserSession(Base):
    __tablename__ = "user_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    session_token = Column(String(255), unique=True, index=True, nullable=False)
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    last_activity_at = Column(DateTime, default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="sessions")
    refresh_tokens = relationship("RefreshToken", back_populates="session", cascade="all, delete-orphan")


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    session_id = Column(Integer, ForeignKey("user_sessions.id", ondelete="CASCADE"), nullable=True, index=True)
    jti = Column(String(64), unique=True, index=True, nullable=False)
    token_hash = Column(String(64), unique=True, index=True, nullable=False)
    family_id = Column(String(64), index=True, nullable=False)
    is_revoked = Column(Boolean, default=False, nullable=False)
    replaced_by = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    expires_at = Column(DateTime, nullable=False)

    user = relationship("User", back_populates="refresh_tokens")
    session = relationship("UserSession", back_populates="refresh_tokens")


# ─── RBAC Models ─────────────────────────────────────────────────────────────

class Permission(Base):
    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(100), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(String(255), nullable=True)
    module = Column(String(50), index=True, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    role_permissions = relationship("RolePermission", back_populates="permission", cascade="all, delete-orphan")


class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, index=True, nullable=False)
    description = Column(String(255), nullable=True)
    is_system = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    role_permissions = relationship("RolePermission", back_populates="role", cascade="all, delete-orphan")
    user_assignments = relationship("UserRoleAssignment", back_populates="role", cascade="all, delete-orphan")


class RolePermission(Base):
    __tablename__ = "role_permissions"

    id = Column(Integer, primary_key=True, index=True)
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False, index=True)
    permission_id = Column(Integer, ForeignKey("permissions.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    role = relationship("Role", back_populates="role_permissions")
    permission = relationship("Permission", back_populates="role_permissions")


class UserRoleAssignment(Base):
    __tablename__ = "user_role_assignments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    user = relationship("User", back_populates="assigned_roles")
    role = relationship("Role", back_populates="user_assignments")


# ─── Account Lifecycle Models ────────────────────────────────────────────────

class UserInvitation(Base):
    __tablename__ = "user_invitations"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), index=True, nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.STUDENT)
    institution_id = Column(Integer, ForeignKey("institutions.id", ondelete="CASCADE"), nullable=True, index=True)
    token_hash = Column(String(64), unique=True, index=True, nullable=False)
    invited_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    status = Column(Enum(InvitationStatus), nullable=False, default=InvitationStatus.PENDING)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    expires_at = Column(DateTime, nullable=False)

    institution = relationship("Institution")
    invited_by = relationship("User", foreign_keys=[invited_by_id])


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash = Column(String(64), unique=True, index=True, nullable=False)
    is_used = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    expires_at = Column(DateTime, nullable=False)

    user = relationship("User")


# ─── Audit Trail Models ──────────────────────────────────────────────────────

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=func.now(), nullable=False, index=True)
    event_type = Column(String(100), nullable=False, index=True)
    severity = Column(Enum(AuditSeverity), nullable=False, default=AuditSeverity.INFO, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    username = Column(String(100), nullable=True, index=True)
    institution_id = Column(Integer, ForeignKey("institutions.id", ondelete="SET NULL"), nullable=True, index=True)
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(500), nullable=True)
    resource_type = Column(String(100), nullable=True, index=True)
    resource_id = Column(String(100), nullable=True, index=True)
    correlation_id = Column(String(100), nullable=True, index=True)
    details = Column(JSON, nullable=True)

    user = relationship("User", foreign_keys=[user_id])
    institution = relationship("Institution", foreign_keys=[institution_id])


# ─── Student Model ────────────────────────────────────────────────────────────

class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    institution_id = Column(Integer, ForeignKey("institutions.id", ondelete="SET NULL"), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    student_id = Column(String(20), unique=True, index=True, nullable=False)
    faculty = Column(String(100), nullable=False)
    department = Column(String(100), nullable=False)
    program = Column(String(150), nullable=False)
    year_of_study = Column(Integer, nullable=False, default=1)
    semester = Column(Integer, nullable=False, default=1)
    gpa = Column(Float, default=0.0)
    credits_earned = Column(Integer, default=0)
    enrollment_date = Column(Date, nullable=True)
    expected_graduation = Column(Date, nullable=True)
    address = Column(Text, nullable=True)
    emergency_contact = Column(String(255), nullable=True)
    scholarship = Column(Boolean, default=False)
    scholarship_details = Column(Text, nullable=True)
    campus_id = Column(Integer, ForeignKey("campuses.id", ondelete="SET NULL"), nullable=True, index=True)
    program_id = Column(Integer, ForeignKey("programs.id", ondelete="SET NULL"), nullable=True, index=True)
    faculty_id = Column(Integer, ForeignKey("faculties.id", ondelete="SET NULL"), nullable=True, index=True)
    department_id = Column(Integer, ForeignKey("departments.id", ondelete="SET NULL"), nullable=True, index=True)
    academic_standing = Column(String(50), default="good_standing", nullable=False)
    enrollment_status = Column(String(50), default="enrolled", nullable=False)
    national_id = Column(String(50), nullable=True)
    date_of_birth = Column(Date, nullable=True)
    gender = Column(String(20), nullable=True)

    # Relationships
    institution = relationship("Institution", back_populates="students")
    user = relationship("User", back_populates="student")
    campus = relationship("Campus")
    program_ref = relationship("Program")
    faculty_ref = relationship("Faculty")
    department_ref = relationship("Department")
    enrollments = relationship("Enrollment", back_populates="student", cascade="all, delete-orphan")
    grades = relationship("Grade", back_populates="student", cascade="all, delete-orphan")
    attendances = relationship("Attendance", back_populates="student", cascade="all, delete-orphan")
    assignments = relationship("AssignmentSubmission", back_populates="student", cascade="all, delete-orphan")
    borrow_records = relationship("BorrowRecord", back_populates="student", cascade="all, delete-orphan")
    club_memberships = relationship("ClubMembership", back_populates="student", cascade="all, delete-orphan")


# ─── Lecturer Model ───────────────────────────────────────────────────────────

class Lecturer(Base):
    __tablename__ = "lecturers"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    lecturer_id = Column(String(20), unique=True, index=True, nullable=False)
    faculty = Column(String(100), nullable=False)
    department = Column(String(100), nullable=False)
    specialization = Column(String(200), nullable=True)
    qualification = Column(String(200), nullable=True)
    office_location = Column(String(100), nullable=True)
    office_hours = Column(JSON, nullable=True)  # {"monday": "9:00-11:00", ...}
    research_interests = Column(Text, nullable=True)
    bio = Column(Text, nullable=True)
    publications = Column(Integer, default=0)
    joined_date = Column(Date, nullable=True)
    institution_id = Column(Integer, ForeignKey("institutions.id", ondelete="CASCADE"), nullable=True, index=True)
    campus_id = Column(Integer, ForeignKey("campuses.id", ondelete="SET NULL"), nullable=True, index=True)
    faculty_id = Column(Integer, ForeignKey("faculties.id", ondelete="SET NULL"), nullable=True, index=True)
    department_id = Column(Integer, ForeignKey("departments.id", ondelete="SET NULL"), nullable=True, index=True)
    employment_status = Column(String(50), default="full_time", nullable=False)
    designation = Column(String(100), default="Lecturer", nullable=False)
    max_teaching_load_hours = Column(Integer, default=15, nullable=False)
    current_teaching_load_hours = Column(Integer, default=0, nullable=False)

    # Relationships
    institution = relationship("Institution", back_populates="lecturers")
    user = relationship("User", back_populates="lecturer")
    campus = relationship("Campus")
    faculty_ref = relationship("Faculty")
    department_ref = relationship("Department")
    courses = relationship("Course", back_populates="lecturer")


# ─── Alumni Model ─────────────────────────────────────────────────────────────

class Alumni(Base):
    __tablename__ = "alumni"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    alumni_id = Column(String(20), unique=True, index=True, nullable=False)
    graduation_year = Column(Integer, nullable=False)
    degree = Column(String(200), nullable=False)
    current_position = Column(String(200), nullable=True)
    current_company = Column(String(200), nullable=True)
    industry = Column(String(100), nullable=True)
    linkedin_url = Column(String(500), nullable=True)
    willing_to_mentor = Column(Boolean, default=False)
    location = Column(String(200), nullable=True)
    bio = Column(Text, nullable=True)

    # Relationships
    user = relationship("User", back_populates="alumni")
    experiences = relationship("AlumniExperience", back_populates="alumni", cascade="all, delete-orphan")
    mentorships = relationship("Mentorship", back_populates="mentor", cascade="all, delete-orphan")


class AlumniExperience(Base):
    __tablename__ = "alumni_experiences"

    id = Column(Integer, primary_key=True, index=True)
    alumni_id = Column(Integer, ForeignKey("alumni.id"), nullable=False)
    title = Column(String(300), nullable=False)
    content = Column(Text, nullable=False)
    category = Column(String(50), default="career")  # career, academic, personal
    tags = Column(JSON, nullable=True)
    likes = Column(Integer, default=0)
    is_published = Column(Boolean, default=True)
    image_url = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=func.now())

    alumni = relationship("Alumni", back_populates="experiences")


class Mentorship(Base):
    __tablename__ = "mentorships"

    id = Column(Integer, primary_key=True, index=True)
    mentor_id = Column(Integer, ForeignKey("alumni.id"), nullable=False)
    mentee_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(String(20), default="pending")  # pending, active, completed
    focus_area = Column(String(200), nullable=True)
    message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())

    mentor = relationship("Alumni", back_populates="mentorships")


# ─── Academic Models ──────────────────────────────────────────────────────────

class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    institution_id = Column(Integer, ForeignKey("institutions.id", ondelete="SET NULL"), nullable=True, index=True)
    course_code = Column(String(20), unique=True, index=True, nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    credits = Column(Integer, nullable=False, default=3)
    faculty = Column(String(100), nullable=False)
    department = Column(String(100), nullable=False)
    semester = Column(Integer, nullable=False)
    year = Column(Integer, nullable=False)
    max_students = Column(Integer, default=60)
    lecturer_id = Column(Integer, ForeignKey("lecturers.id"), nullable=True)
    program_id = Column(Integer, ForeignKey("programs.id", ondelete="SET NULL"), nullable=True, index=True)
    faculty_id = Column(Integer, ForeignKey("faculties.id", ondelete="SET NULL"), nullable=True, index=True)
    department_id = Column(Integer, ForeignKey("departments.id", ondelete="SET NULL"), nullable=True, index=True)
    delivery_method = Column(String(50), default="in_person", nullable=False)
    learning_outcomes = Column(JSON, nullable=True)
    schedule = Column(JSON, nullable=True)  # {"day": "Monday", "time": "9:00", "room": "A101"}
    syllabus_url = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())

    # Relationships
    institution = relationship("Institution", back_populates="courses")
    lecturer = relationship("Lecturer", back_populates="courses")
    program = relationship("Program")
    faculty_ref = relationship("Faculty")
    department_ref = relationship("Department")
    prerequisites = relationship("CoursePrerequisite", foreign_keys="CoursePrerequisite.course_id", back_populates="course", cascade="all, delete-orphan")
    modules = relationship("CourseModule", back_populates="course", cascade="all, delete-orphan")
    enrollments = relationship("Enrollment", back_populates="course", cascade="all, delete-orphan")
    grades = relationship("Grade", back_populates="course", cascade="all, delete-orphan")
    assignments = relationship("Assignment", back_populates="course", cascade="all, delete-orphan")
    attendances = relationship("Attendance", back_populates="course", cascade="all, delete-orphan")
    materials = relationship("CourseMaterial", back_populates="course", cascade="all, delete-orphan")


class CoursePrerequisite(Base):
    __tablename__ = "course_prerequisites"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    prerequisite_course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    is_mandatory = Column(Boolean, default=True, nullable=False)
    minimum_grade = Column(String(5), default="C", nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    course = relationship("Course", foreign_keys=[course_id], back_populates="prerequisites")
    prerequisite_course = relationship("Course", foreign_keys=[prerequisite_course_id])


class CourseModule(Base):
    __tablename__ = "course_modules"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    order_index = Column(Integer, default=1, nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    learning_objectives = Column(JSON, nullable=True)
    estimated_hours = Column(Float, default=10.0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    course = relationship("Course", back_populates="modules")


class Enrollment(Base):
    __tablename__ = "enrollments"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    enrolled_at = Column(DateTime, default=func.now())
    status = Column(String(20), default="active")  # active, dropped, completed

    student = relationship("Student", back_populates="enrollments")
    course = relationship("Course", back_populates="enrollments")


class Grade(Base):
    __tablename__ = "grades"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    midterm = Column(Float, nullable=True)
    final = Column(Float, nullable=True)
    assignments_avg = Column(Float, nullable=True)
    total = Column(Float, nullable=True)
    letter_grade = Column(String(5), nullable=True)
    grade_points = Column(Float, nullable=True)
    remarks = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    student = relationship("Student", back_populates="grades")
    course = relationship("Course", back_populates="grades")


class Attendance(Base):
    __tablename__ = "attendance"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    date = Column(Date, nullable=False)
    status = Column(Enum(AttendanceStatus), default=AttendanceStatus.PRESENT)
    notes = Column(String(200), nullable=True)

    student = relationship("Student", back_populates="attendances")
    course = relationship("Course", back_populates="attendances")


class Assignment(Base):
    __tablename__ = "assignments"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    title = Column(String(300), nullable=False)
    description = Column(Text, nullable=True)
    due_date = Column(DateTime, nullable=False)
    max_marks = Column(Float, default=100.0)
    assignment_type = Column(String(50), default="assignment")  # assignment, quiz, project
    file_url = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=func.now())

    course = relationship("Course", back_populates="assignments")
    submissions = relationship("AssignmentSubmission", back_populates="assignment", cascade="all, delete-orphan")


class AssignmentSubmission(Base):
    __tablename__ = "assignment_submissions"

    id = Column(Integer, primary_key=True, index=True)
    assignment_id = Column(Integer, ForeignKey("assignments.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    file_url = Column(String(500), nullable=True)
    text_content = Column(Text, nullable=True)
    submitted_at = Column(DateTime, default=func.now())
    marks = Column(Float, nullable=True)
    feedback = Column(Text, nullable=True)
    status = Column(Enum(AssignmentStatus), default=AssignmentStatus.SUBMITTED)

    assignment = relationship("Assignment", back_populates="submissions")
    student = relationship("Student", back_populates="assignments")


class CourseMaterial(Base):
    __tablename__ = "course_materials"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    title = Column(String(300), nullable=False)
    description = Column(Text, nullable=True)
    file_url = Column(String(500), nullable=True)
    material_type = Column(String(50), default="lecture_note")  # lecture_note, video, pdf, link
    week_number = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=func.now())

    course = relationship("Course", back_populates="materials")


# ─── Library Models ───────────────────────────────────────────────────────────

class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    isbn = Column(String(20), unique=True, index=True, nullable=True)
    title = Column(String(300), nullable=False)
    author = Column(String(300), nullable=False)
    publisher = Column(String(200), nullable=True)
    year = Column(Integer, nullable=True)
    edition = Column(String(50), nullable=True)
    category = Column(String(100), nullable=False)
    subject = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    cover_url = Column(String(500), nullable=True)
    location = Column(String(100), nullable=True)  # Shelf location
    total_copies = Column(Integer, default=1)
    available_copies = Column(Integer, default=1)
    status = Column(Enum(BookStatus), default=BookStatus.AVAILABLE)
    is_ebook = Column(Boolean, default=False)
    ebook_url = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=func.now())

    borrow_records = relationship("BorrowRecord", back_populates="book")
    reservations = relationship("BookReservation", back_populates="book")


class BorrowRecord(Base):
    __tablename__ = "borrow_records"

    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    borrowed_at = Column(DateTime, default=func.now())
    due_date = Column(DateTime, nullable=False)
    returned_at = Column(DateTime, nullable=True)
    status = Column(Enum(BorrowStatus), default=BorrowStatus.ACTIVE)
    fine_amount = Column(Float, default=0.0)
    fine_paid = Column(Boolean, default=False)
    notes = Column(Text, nullable=True)

    book = relationship("Book", back_populates="borrow_records")
    student = relationship("Student", back_populates="borrow_records")


class BookReservation(Base):
    __tablename__ = "book_reservations"

    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    reserved_at = Column(DateTime, default=func.now())
    expires_at = Column(DateTime, nullable=False)
    status = Column(String(20), default="active")  # active, fulfilled, cancelled

    book = relationship("Book", back_populates="reservations")


# ─── Sports & Clubs Models ────────────────────────────────────────────────────

class Club(Base):
    __tablename__ = "clubs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(Enum(ClubCategory), nullable=False)
    logo_url = Column(String(500), nullable=True)
    cover_url = Column(String(500), nullable=True)
    advisor_id = Column(Integer, ForeignKey("lecturers.id"), nullable=True)
    president_name = Column(String(200), nullable=True)
    meeting_schedule = Column(JSON, nullable=True)
    achievements = Column(Text, nullable=True)
    max_members = Column(Integer, default=100)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())

    memberships = relationship("ClubMembership", back_populates="club", cascade="all, delete-orphan")
    events = relationship("ClubEvent", back_populates="club", cascade="all, delete-orphan")


class ClubMembership(Base):
    __tablename__ = "club_memberships"

    id = Column(Integer, primary_key=True, index=True)
    club_id = Column(Integer, ForeignKey("clubs.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    role = Column(String(50), default="member")  # member, secretary, treasurer, president
    joined_at = Column(DateTime, default=func.now())
    is_active = Column(Boolean, default=True)

    club = relationship("Club", back_populates="memberships")
    student = relationship("Student", back_populates="club_memberships")


class ClubEvent(Base):
    __tablename__ = "club_events"

    id = Column(Integer, primary_key=True, index=True)
    club_id = Column(Integer, ForeignKey("clubs.id"), nullable=False)
    title = Column(String(300), nullable=False)
    description = Column(Text, nullable=True)
    event_date = Column(DateTime, nullable=False)
    location = Column(String(200), nullable=True)
    image_url = Column(String(500), nullable=True)
    max_participants = Column(Integer, nullable=True)
    registration_required = Column(Boolean, default=False)
    is_public = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())

    club = relationship("Club", back_populates="events")
    registrations = relationship("EventRegistration", back_populates="event", cascade="all, delete-orphan")


class EventRegistration(Base):
    __tablename__ = "event_registrations"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("club_events.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    registered_at = Column(DateTime, default=func.now())
    attended = Column(Boolean, default=False)

    event = relationship("ClubEvent", back_populates="registrations")


class SportsResult(Base):
    __tablename__ = "sports_results"

    id = Column(Integer, primary_key=True, index=True)
    club_id = Column(Integer, ForeignKey("clubs.id"), nullable=False)
    event_name = Column(String(300), nullable=False)
    opponent = Column(String(200), nullable=True)
    result = Column(String(50), nullable=True)  # Win / Loss / Draw
    score = Column(String(50), nullable=True)
    event_date = Column(Date, nullable=False)
    location = Column(String(200), nullable=True)
    notes = Column(Text, nullable=True)


# ─── News Portal Models ───────────────────────────────────────────────────────

class News(Base):
    __tablename__ = "news"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(300), nullable=False)
    slug = Column(String(350), unique=True, index=True, nullable=False)
    content = Column(Text, nullable=False)
    summary = Column(Text, nullable=True)
    category = Column(Enum(NewsCategory), nullable=False)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    cover_image_url = Column(String(500), nullable=True)
    tags = Column(JSON, nullable=True)
    views = Column(Integer, default=0)
    is_published = Column(Boolean, default=True)
    is_featured = Column(Boolean, default=False)
    published_at = Column(DateTime, default=func.now())
    created_at = Column(DateTime, default=func.now())

    author = relationship("User")
    comments = relationship("NewsComment", back_populates="news", cascade="all, delete-orphan")


class NewsComment(Base):
    __tablename__ = "news_comments"

    id = Column(Integer, primary_key=True, index=True)
    news_id = Column(Integer, ForeignKey("news.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=func.now())

    news = relationship("News", back_populates="comments")
    user = relationship("User")


# ─── Communication Models ─────────────────────────────────────────────────────

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(300), nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(String(50), default="info")  # info, warning, success, error
    link = Column(String(500), nullable=True)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())

    user = relationship("User", back_populates="notifications")


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    receiver_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    sent_at = Column(DateTime, default=func.now())

    sender = relationship("User", foreign_keys=[sender_id], back_populates="messages")
