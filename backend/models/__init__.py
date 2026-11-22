"""
NSBM EduSphere — All Database Models
"""
import enum
from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Text,
    ForeignKey, Enum, Date, JSON, BigInteger, UniqueConstraint
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
    cohorts = relationship("Cohort", back_populates="institution", cascade="all, delete-orphan")


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
    notification_preferences = relationship("NotificationPreference", uselist=False, back_populates="user", cascade="all, delete-orphan")
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
    lesson_progress = relationship("StudentLessonProgress", back_populates="student", cascade="all, delete-orphan")
    module_progress = relationship("StudentModuleProgress", back_populates="student", cascade="all, delete-orphan")


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
    syllabus_data = Column(JSON, nullable=True)
    workspace_settings = Column(JSON, nullable=True)
    banner_url = Column(String(500), nullable=True)
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
    documents = relationship("CourseDocument", back_populates="course", cascade="all, delete-orphan")
    videos = relationship("CourseVideo", back_populates="course", cascade="all, delete-orphan")
    announcements = relationship("CourseAnnouncement", back_populates="course", cascade="all, delete-orphan", order_by="desc(CourseAnnouncement.is_pinned), desc(CourseAnnouncement.published_at)")
    forum_categories = relationship("CourseForumCategory", back_populates="course", cascade="all, delete-orphan", order_by="CourseForumCategory.display_order")
    live_sessions = relationship("VirtualClassroomSession", back_populates="course", cascade="all, delete-orphan", order_by="VirtualClassroomSession.start_time")
    rubrics = relationship("Rubric", back_populates="course", cascade="all, delete-orphan")
    question_categories = relationship("QuestionCategory", back_populates="course", cascade="all, delete-orphan", order_by="QuestionCategory.display_order")
    question_bank_items = relationship("QuestionBankItem", back_populates="course", cascade="all, delete-orphan")
    quizzes = relationship("Quiz", back_populates="course", cascade="all, delete-orphan")
    gradebook_categories = relationship("GradebookCategory", back_populates="course", cascade="all, delete-orphan", order_by="GradebookCategory.id")
    grade_scales = relationship("GradeScale", back_populates="course", cascade="all, delete-orphan")
    timetable_slots = relationship("TimetableSlot", back_populates="course", cascade="all, delete-orphan", order_by="TimetableSlot.day_of_week, TimetableSlot.start_time")
    attendance_sessions = relationship("AttendanceSession", back_populates="course", cascade="all, delete-orphan", order_by="desc(AttendanceSession.session_date)")


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
    status = Column(String(50), default="published", nullable=False) # draft, published, archived
    unlock_at = Column(DateTime, nullable=True)
    prerequisite_module_id = Column(Integer, ForeignKey("course_modules.id", ondelete="SET NULL"), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    course = relationship("Course", back_populates="modules")
    prerequisite = relationship("CourseModule", remote_side=[id])
    lessons = relationship("CourseLesson", back_populates="module", cascade="all, delete-orphan", order_by="CourseLesson.order_index")
    documents = relationship("CourseDocument", back_populates="module")
    videos = relationship("CourseVideo", back_populates="module")
    progress_records = relationship("StudentModuleProgress", back_populates="module", cascade="all, delete-orphan")


class CourseLesson(Base):
    __tablename__ = "course_lessons"

    id = Column(Integer, primary_key=True, index=True)
    module_id = Column(Integer, ForeignKey("course_modules.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    lesson_type = Column(String(50), default="reading", nullable=False) # reading, video, assignment, quiz, external_link, file_resource, interactive
    content = Column(Text, nullable=True)
    resource_url = Column(String(1024), nullable=True)
    estimated_minutes = Column(Integer, default=15, nullable=False)
    order_index = Column(Integer, default=1, nullable=False)
    is_required = Column(Boolean, default=True, nullable=False)
    is_published = Column(Boolean, default=True, nullable=False)
    unlock_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    module = relationship("CourseModule", back_populates="lessons")
    content_versions = relationship("LessonContentVersion", back_populates="lesson", cascade="all, delete-orphan", order_by="desc(LessonContentVersion.version_number)")
    documents = relationship("CourseDocument", back_populates="lesson")
    videos = relationship("CourseVideo", back_populates="lesson")
    progress_records = relationship("StudentLessonProgress", back_populates="lesson", cascade="all, delete-orphan")


class LessonContentVersion(Base):
    __tablename__ = "lesson_content_versions"

    id = Column(Integer, primary_key=True, index=True)
    lesson_id = Column(Integer, ForeignKey("course_lessons.id", ondelete="CASCADE"), nullable=False, index=True)
    version_number = Column(Integer, default=1, nullable=False, index=True)
    content_format = Column(String(50), default="markdown", nullable=False) # markdown, html, interactive_block
    raw_content = Column(Text, nullable=False)
    rendered_content = Column(Text, nullable=False)
    widget_configs = Column(JSON, nullable=True)
    author_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    change_summary = Column(String(255), nullable=True)
    is_current = Column(Boolean, default=True, nullable=False, index=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    lesson = relationship("CourseLesson", back_populates="content_versions")
    author = relationship("User")


class CourseDocument(Base):
    __tablename__ = "course_documents"

    id = Column(Integer, primary_key=True, index=True)
    institution_id = Column(Integer, ForeignKey("institutions.id", ondelete="CASCADE"), nullable=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    module_id = Column(Integer, ForeignKey("course_modules.id", ondelete="SET NULL"), nullable=True, index=True)
    lesson_id = Column(Integer, ForeignKey("course_lessons.id", ondelete="SET NULL"), nullable=True, index=True)
    title = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    storage_path = Column(String(512), nullable=False)
    mime_type = Column(String(100), nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    sha256_hash = Column(String(64), nullable=False)
    uploader_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    is_published = Column(Boolean, default=True, nullable=False)
    download_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    course = relationship("Course", back_populates="documents")
    module = relationship("CourseModule", back_populates="documents")
    lesson = relationship("CourseLesson", back_populates="documents")
    uploader = relationship("User")


class CourseVideo(Base):
    __tablename__ = "course_videos"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    module_id = Column(Integer, ForeignKey("course_modules.id", ondelete="SET NULL"), nullable=True, index=True)
    lesson_id = Column(Integer, ForeignKey("course_lessons.id", ondelete="SET NULL"), nullable=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    provider = Column(String(50), default="self_hosted", nullable=False)  # self_hosted, youtube, vimeo, hls, custom_embed
    video_url = Column(String(1024), nullable=False)
    duration_seconds = Column(Integer, default=0, nullable=False)
    thumbnail_url = Column(String(1024), nullable=True)
    captions_track = Column(JSON, nullable=True)  # [{"label": "English", "srclang": "en", "src": "..."}]
    chapters = Column(JSON, nullable=True)  # [{"timestamp_seconds": 0, "title": "Intro"}]
    is_published = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    course = relationship("Course", back_populates="videos")
    module = relationship("CourseModule", back_populates="videos")
    lesson = relationship("CourseLesson", back_populates="videos")
    playback_records = relationship("VideoPlaybackProgress", back_populates="video", cascade="all, delete-orphan")


class VideoPlaybackProgress(Base):
    __tablename__ = "video_playback_progress"

    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, ForeignKey("course_videos.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    last_position_seconds = Column(Integer, default=0, nullable=False)
    max_watched_seconds = Column(Integer, default=0, nullable=False)
    watch_percentage = Column(Float, default=0.0, nullable=False)
    is_completed = Column(Boolean, default=False, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    bookmarks = Column(JSON, nullable=True)  # [{"timestamp_seconds": 45, "title": "Key point"}]
    notes = Column(JSON, nullable=True)  # [{"timestamp_seconds": 120, "note": "Study for quiz"}]
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    video = relationship("CourseVideo", back_populates="playback_records")
    student = relationship("Student")


class StudentLessonProgress(Base):
    __tablename__ = "student_lesson_progress"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    lesson_id = Column(Integer, ForeignKey("course_lessons.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(30), default="in_progress", nullable=False) # in_progress, completed
    time_spent_seconds = Column(Integer, default=0, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    student = relationship("Student", back_populates="lesson_progress")
    lesson = relationship("CourseLesson", back_populates="progress_records")


class StudentModuleProgress(Base):
    __tablename__ = "student_module_progress"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    module_id = Column(Integer, ForeignKey("course_modules.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(30), default="in_progress", nullable=False) # in_progress, completed
    completed_items_count = Column(Integer, default=0, nullable=False)
    total_items_count = Column(Integer, default=0, nullable=False)
    progress_percentage = Column(Float, default=0.0, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    student = relationship("Student", back_populates="module_progress")
    module = relationship("CourseModule", back_populates="progress_records")


class CourseAnnouncement(Base):
    __tablename__ = "course_announcements"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    author_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    cohort_id = Column(Integer, ForeignKey("cohorts.id", ondelete="SET NULL"), nullable=True, index=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    priority = Column(String(20), default="normal", nullable=False)  # normal, important, urgent
    is_pinned = Column(Boolean, default=False, nullable=False)
    requires_acknowledgement = Column(Boolean, default=False, nullable=False)
    published_at = Column(DateTime, default=func.now(), nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    course = relationship("Course", back_populates="announcements")
    author = relationship("User")
    cohort = relationship("Cohort")
    acknowledgements = relationship("AnnouncementAcknowledgement", back_populates="announcement", cascade="all, delete-orphan")


class AnnouncementAcknowledgement(Base):
    __tablename__ = "announcement_acknowledgements"

    id = Column(Integer, primary_key=True, index=True)
    announcement_id = Column(Integer, ForeignKey("course_announcements.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    acknowledged_at = Column(DateTime, default=func.now(), nullable=False)

    announcement = relationship("CourseAnnouncement", back_populates="acknowledgements")
    student = relationship("Student")


class CourseForumCategory(Base):
    __tablename__ = "course_forum_categories"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)
    is_locked = Column(Boolean, default=False, nullable=False)
    display_order = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    course = relationship("Course", back_populates="forum_categories")
    threads = relationship("ForumThread", back_populates="category", cascade="all, delete-orphan", order_by="desc(ForumThread.is_pinned), desc(ForumThread.created_at)")


class ForumThread(Base):
    __tablename__ = "forum_threads"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    category_id = Column(Integer, ForeignKey("course_forum_categories.id", ondelete="CASCADE"), nullable=False, index=True)
    author_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    is_pinned = Column(Boolean, default=False, nullable=False)
    is_locked = Column(Boolean, default=False, nullable=False)
    view_count = Column(Integer, default=0, nullable=False)
    reply_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    course = relationship("Course")
    category = relationship("CourseForumCategory", back_populates="threads")
    author = relationship("User")
    posts = relationship("ForumPost", back_populates="thread", cascade="all, delete-orphan", order_by="ForumPost.created_at")


class ForumPost(Base):
    __tablename__ = "forum_posts"

    id = Column(Integer, primary_key=True, index=True)
    thread_id = Column(Integer, ForeignKey("forum_threads.id", ondelete="CASCADE"), nullable=False, index=True)
    author_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    parent_post_id = Column(Integer, ForeignKey("forum_posts.id", ondelete="SET NULL"), nullable=True, index=True)
    content = Column(Text, nullable=False)
    is_endorsed_by_instructor = Column(Boolean, default=False, nullable=False)
    is_solution = Column(Boolean, default=False, nullable=False)
    upvotes = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    thread = relationship("ForumThread", back_populates="posts")
    author = relationship("User")
    reactions = relationship("ForumPostReaction", back_populates="post", cascade="all, delete-orphan")


class ForumPostReaction(Base):
    __tablename__ = "forum_post_reactions"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("forum_posts.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    reaction_type = Column(String(50), default="like", nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    __table_args__ = (UniqueConstraint("post_id", "user_id", "reaction_type", name="uq_post_user_reaction"),)

    post = relationship("ForumPost", back_populates="reactions")
    user = relationship("User")


class VirtualClassroomSession(Base):
    __tablename__ = "virtual_classroom_sessions"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    host_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    provider = Column(String(50), default="zoom", nullable=False)  # zoom, google_meet, microsoft_teams, bigbluebutton, custom_hls
    meeting_id = Column(String(255), nullable=True)
    join_url = Column(String(1024), nullable=False)
    host_url = Column(String(1024), nullable=True)
    passcode = Column(String(100), nullable=True)
    start_time = Column(DateTime, nullable=False, index=True)
    end_time = Column(DateTime, nullable=False)
    status = Column(String(30), default="scheduled", nullable=False)  # scheduled, live, concluded, cancelled
    recording_url = Column(String(1024), nullable=True)
    recording_duration_minutes = Column(Integer, nullable=True)
    is_recorded = Column(Boolean, default=True, nullable=False)
    max_participants = Column(Integer, default=100, nullable=True)
    session_settings = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    course = relationship("Course", back_populates="live_sessions")
    host = relationship("User")
    attendances = relationship("VirtualClassroomAttendance", back_populates="session", cascade="all, delete-orphan")


class VirtualClassroomAttendance(Base):
    __tablename__ = "virtual_classroom_attendance"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("virtual_classroom_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=True, index=True)
    joined_at = Column(DateTime, default=func.now(), nullable=False)
    left_at = Column(DateTime, nullable=True)
    duration_minutes = Column(Integer, default=0, nullable=False)
    device_type = Column(String(100), default="browser", nullable=True)
    attendance_status = Column(String(30), default="present", nullable=False)  # present, late, partial, left_early
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    __table_args__ = (UniqueConstraint("session_id", "user_id", name="uq_session_user_attendance"),)

    session = relationship("VirtualClassroomSession", back_populates="attendances")
    user = relationship("User")
    student = relationship("Student")


class Enrollment(Base):
    __tablename__ = "enrollments"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    institution_id = Column(Integer, ForeignKey("institutions.id", ondelete="CASCADE"), nullable=True, index=True)
    semester_id = Column(Integer, ForeignKey("semesters.id", ondelete="SET NULL"), nullable=True, index=True)
    enrolled_at = Column(DateTime, default=func.now(), nullable=False)
    status = Column(String(30), default="active", nullable=False)  # active, requested, waitlisted, dropped, withdrawn, rejected, completed
    waitlist_position = Column(Integer, nullable=True)
    registration_type = Column(String(30), default="regular", nullable=False)  # regular, audit, repeat
    approved_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    dropped_at = Column(DateTime, nullable=True)
    rejection_reason = Column(Text, nullable=True)
    remarks = Column(Text, nullable=True)

    # Relationships
    student = relationship("Student", back_populates="enrollments")
    course = relationship("Course", back_populates="enrollments")
    semester = relationship("Semester")
    approved_by = relationship("User", foreign_keys=[approved_by_id])
    institution = relationship("Institution")


# ─── Cohort & Group Management Models ──────────────────────────────────────────

class Cohort(Base):
    __tablename__ = "cohorts"

    id = Column(Integer, primary_key=True, index=True)
    institution_id = Column(Integer, ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False, index=True)
    program_id = Column(Integer, ForeignKey("programs.id", ondelete="SET NULL"), nullable=True, index=True)
    academic_year_id = Column(Integer, ForeignKey("academic_years.id", ondelete="SET NULL"), nullable=True, index=True)
    code = Column(String(50), nullable=False, index=True)
    name = Column(String(150), nullable=False)
    year_of_study = Column(Integer, default=1, nullable=False)
    semester_number = Column(Integer, default=1, nullable=False)
    max_capacity = Column(Integer, default=60, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    institution = relationship("Institution", back_populates="cohorts")
    program = relationship("Program")
    academic_year = relationship("AcademicYear")
    members = relationship("CohortMember", back_populates="cohort", cascade="all, delete-orphan")
    groups = relationship("StudentGroup", back_populates="cohort", cascade="all, delete-orphan")


class CohortMember(Base):
    __tablename__ = "cohort_members"

    id = Column(Integer, primary_key=True, index=True)
    cohort_id = Column(Integer, ForeignKey("cohorts.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(30), default="student", nullable=False)  # student, class_representative, vice_representative
    joined_at = Column(DateTime, default=func.now(), nullable=False)
    status = Column(String(20), default="active", nullable=False)  # active, transferred, inactive

    # Relationships
    cohort = relationship("Cohort", back_populates="members")
    student = relationship("Student")


class StudentGroup(Base):
    __tablename__ = "student_groups"

    id = Column(Integer, primary_key=True, index=True)
    institution_id = Column(Integer, ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False, index=True)
    cohort_id = Column(Integer, ForeignKey("cohorts.id", ondelete="CASCADE"), nullable=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=True, index=True)
    group_type = Column(String(50), default="tutorial", nullable=False)  # tutorial, lab, project_team, discussion
    name = Column(String(100), nullable=False)
    max_capacity = Column(Integer, default=30, nullable=False)
    mentor_lecturer_id = Column(Integer, ForeignKey("lecturers.id", ondelete="SET NULL"), nullable=True)
    schedule_info = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    # Relationships
    cohort = relationship("Cohort", back_populates="groups")
    course = relationship("Course")
    mentor_lecturer = relationship("Lecturer")
    members = relationship("StudentGroupMember", back_populates="group", cascade="all, delete-orphan")


class StudentGroupMember(Base):
    __tablename__ = "student_group_members"

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("student_groups.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    group_role = Column(String(30), default="member", nullable=False)  # leader, member
    joined_at = Column(DateTime, default=func.now(), nullable=False)

    # Relationships
    group = relationship("StudentGroup", back_populates="members")
    student = relationship("Student")


# ─── Academic Advising and Student Support Models ──────────────────────────────

class AcademicAdvisorAssignment(Base):
    __tablename__ = "academic_advisor_assignments"

    id = Column(Integer, primary_key=True, index=True)
    institution_id = Column(Integer, ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    lecturer_id = Column(Integer, ForeignKey("lecturers.id", ondelete="CASCADE"), nullable=False, index=True)
    assigned_date = Column(Date, default=func.current_date(), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    advising_type = Column(String(50), default="academic", nullable=False)  # academic, career, pastoral, research_supervisor
    created_at = Column(DateTime, default=func.now(), nullable=False)

    # Relationships
    institution = relationship("Institution")
    student = relationship("Student")
    lecturer = relationship("Lecturer")


class AdvisingSession(Base):
    __tablename__ = "advising_sessions"

    id = Column(Integer, primary_key=True, index=True)
    institution_id = Column(Integer, ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    lecturer_id = Column(Integer, ForeignKey("lecturers.id", ondelete="CASCADE"), nullable=False, index=True)
    scheduled_at = Column(DateTime, nullable=False)
    duration_minutes = Column(Integer, default=30, nullable=False)
    session_type = Column(String(50), default="one_on_one", nullable=False)  # one_on_one, group, online, urgent_intervention
    status = Column(String(30), default="scheduled", nullable=False)  # scheduled, completed, cancelled, no_show
    topic = Column(String(200), nullable=False)
    student_notes = Column(Text, nullable=True)  # notes/goals visible to student
    confidential_notes = Column(Text, nullable=True)  # strictly private to advisor/dean/admin
    action_items = Column(JSON, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    # Relationships
    student = relationship("Student")
    lecturer = relationship("Lecturer")


class StudentSupportCase(Base):
    __tablename__ = "student_support_cases"

    id = Column(Integer, primary_key=True, index=True)
    institution_id = Column(Integer, ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    assigned_staff_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    case_number = Column(String(50), unique=True, index=True, nullable=False)
    category = Column(String(50), default="academic_probation", nullable=False)  # academic_probation, attendance_warning, financial_hardship, well_being, disciplinary
    priority = Column(String(20), default="medium", nullable=False)  # low, medium, high, critical
    status = Column(String(30), default="open", nullable=False)  # open, in_progress, escalated, resolved, closed
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    resolution_summary = Column(Text, nullable=True)
    created_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    student = relationship("Student")
    assigned_staff = relationship("User", foreign_keys=[assigned_staff_id])
    created_by = relationship("User", foreign_keys=[created_by_id])
    notes = relationship("SupportCaseNote", back_populates="support_case", cascade="all, delete-orphan")


class SupportCaseNote(Base):
    __tablename__ = "support_case_notes"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("student_support_cases.id", ondelete="CASCADE"), nullable=False, index=True)
    author_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    is_confidential = Column(Boolean, default=False, nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    # Relationships
    support_case = relationship("StudentSupportCase", back_populates="notes")
    author = relationship("User")


class Grade(Base):
    __tablename__ = "grades"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False, index=True)
    semester_id = Column(Integer, ForeignKey("semesters.id", ondelete="SET NULL"), nullable=True, index=True)
    midterm = Column(Float, nullable=True)
    final = Column(Float, nullable=True)
    assignments_avg = Column(Float, nullable=True)
    total = Column(Float, nullable=True)
    letter_grade = Column(String(5), nullable=True)
    grade_points = Column(Float, nullable=True)
    credits_earned = Column(Integer, default=0, nullable=False)
    is_final = Column(Boolean, default=False, nullable=False)
    remarks = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    student = relationship("Student", back_populates="grades")
    course = relationship("Course", back_populates="grades")
    semester = relationship("Semester")


class AcademicTermRecord(Base):
    __tablename__ = "academic_term_records"

    id = Column(Integer, primary_key=True, index=True)
    institution_id = Column(Integer, ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    semester_id = Column(Integer, ForeignKey("semesters.id", ondelete="CASCADE"), nullable=False, index=True)
    term_gpa = Column(Float, default=0.0, nullable=False)
    cgpa = Column(Float, default=0.0, nullable=False)
    credits_attempted = Column(Integer, default=0, nullable=False)
    credits_earned = Column(Integer, default=0, nullable=False)
    cumulative_credits_attempted = Column(Integer, default=0, nullable=False)
    cumulative_credits_earned = Column(Integer, default=0, nullable=False)
    academic_standing = Column(String(50), default="good_standing", nullable=False)
    is_finalized = Column(Boolean, default=False, nullable=False)
    finalized_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    institution = relationship("Institution")
    student = relationship("Student")
    semester = relationship("Semester")


class OfficialTranscript(Base):
    __tablename__ = "official_transcripts"

    id = Column(Integer, primary_key=True, index=True)
    institution_id = Column(Integer, ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    verification_code = Column(String(64), unique=True, index=True, nullable=False)
    digital_signature_hash = Column(String(128), nullable=False)
    issue_type = Column(String(30), default="official", nullable=False)
    status = Column(String(20), default="valid", nullable=False)
    issued_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    issued_at = Column(DateTime, default=func.now(), nullable=False)
    recipient_name = Column(String(200), nullable=True)
    recipient_email = Column(String(255), nullable=True)
    data_snapshot = Column(JSON, nullable=False)

    institution = relationship("Institution")
    student = relationship("Student")
    issued_by = relationship("User")


class Attendance(Base):
    __tablename__ = "attendance"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    session_id = Column(Integer, ForeignKey("attendance_sessions.id", ondelete="SET NULL"), nullable=True, index=True)
    date = Column(Date, nullable=False)
    status = Column(Enum(AttendanceStatus), default=AttendanceStatus.PRESENT)
    checkin_method = Column(String(50), default="manual", nullable=False)
    checked_in_at = Column(DateTime, nullable=True)
    participation_score = Column(Float, default=0.0, nullable=False)
    notes = Column(String(200), nullable=True)
    remarks = Column(Text, nullable=True)

    student = relationship("Student", back_populates="attendances")
    course = relationship("Course", back_populates="attendances")
    session = relationship("AttendanceSession", back_populates="attendances")


class Assignment(Base):
    __tablename__ = "assignments"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    creator_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    module_id = Column(Integer, ForeignKey("course_modules.id", ondelete="SET NULL"), nullable=True, index=True)
    title = Column(String(300), nullable=False)
    description = Column(Text, nullable=True)
    due_date = Column(DateTime, nullable=False)
    available_from = Column(DateTime, nullable=True)
    cutoff_date = Column(DateTime, nullable=True)
    max_marks = Column(Float, default=100.0, nullable=False)
    weightage_percentage = Column(Float, default=10.0, nullable=False)
    assignment_type = Column(String(50), default="assignment", nullable=False)  # assignment, quiz, project, lab, essay
    grading_type = Column(String(30), default="points", nullable=False)  # points, percentage, letter_grade, rubric
    status = Column(String(30), default="published", nullable=False)  # draft, published, open, closed, grading, graded, archived
    allow_late_submissions = Column(Boolean, default=True, nullable=False)
    late_penalty_percentage_per_day = Column(Float, default=0.0, nullable=False)
    submission_types = Column(JSON, nullable=True)  # ["file", "text", "url"]
    allowed_file_extensions = Column(JSON, nullable=True)  # [".pdf", ".zip", ".docx"]
    max_file_size_mb = Column(Integer, default=50, nullable=False)
    max_attempts = Column(Integer, default=1, nullable=False)
    anonymous_grading = Column(Boolean, default=False, nullable=False)
    peer_review_enabled = Column(Boolean, default=False, nullable=False)
    group_assignment = Column(Boolean, default=False, nullable=False)
    file_url = Column(String(500), nullable=True)
    published_at = Column(DateTime, nullable=True)
    rubric_id = Column(Integer, ForeignKey("rubrics.id", ondelete="SET NULL"), nullable=True, index=True)
    category_id = Column(Integer, ForeignKey("gradebook_categories.id", ondelete="SET NULL"), nullable=True, index=True)
    grades_released = Column(Boolean, default=True, nullable=False)
    grades_released_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    course = relationship("Course", back_populates="assignments")
    creator = relationship("User", foreign_keys=[creator_id])
    module = relationship("CourseModule")
    rubric = relationship("Rubric", foreign_keys=[rubric_id])
    category = relationship("GradebookCategory", foreign_keys=[category_id])
    submissions = relationship("AssignmentSubmission", back_populates="assignment", cascade="all, delete-orphan")
    rubric_evaluations = relationship("RubricEvaluation", back_populates="assignment", cascade="all, delete-orphan")
    appeals = relationship("GradeAppeal", back_populates="assignment", cascade="all, delete-orphan")


class AssignmentSubmission(Base):
    __tablename__ = "assignment_submissions"

    id = Column(Integer, primary_key=True, index=True)
    assignment_id = Column(Integer, ForeignKey("assignments.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    attempt_number = Column(Integer, default=1, nullable=False)
    submission_receipt = Column(String(100), unique=True, index=True, nullable=True)
    file_url = Column(String(500), nullable=True)
    text_content = Column(Text, nullable=True)
    attachments = Column(JSON, nullable=True)  # [{"filename": "...", "url": "...", "size_bytes": 123}]
    is_late = Column(Boolean, default=False, nullable=False)
    days_late = Column(Float, default=0.0, nullable=False)
    late_penalty_applied = Column(Float, default=0.0, nullable=False)
    originality_score = Column(Float, nullable=True)
    originality_report_url = Column(String(500), nullable=True)
    marks = Column(Float, nullable=True)
    feedback = Column(Text, nullable=True)
    status = Column(Enum(AssignmentStatus), default=AssignmentStatus.SUBMITTED, nullable=False)
    graded_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    graded_at = Column(DateTime, nullable=True)
    submitted_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    assignment = relationship("Assignment", back_populates="submissions")
    student = relationship("Student", back_populates="assignments")
    grader = relationship("User", foreign_keys=[graded_by_id])
    rubric_evaluation = relationship("RubricEvaluation", back_populates="submission", uselist=False, cascade="all, delete-orphan")
    versions = relationship("AssignmentSubmissionVersion", back_populates="submission", cascade="all, delete-orphan", order_by="AssignmentSubmissionVersion.version_number")
    plagiarism_report = relationship("PlagiarismScanReport", back_populates="submission", uselist=False, cascade="all, delete-orphan")
    annotations = relationship("SubmissionAnnotation", back_populates="submission", cascade="all, delete-orphan", order_by="SubmissionAnnotation.created_at")
    appeals = relationship("GradeAppeal", back_populates="submission", cascade="all, delete-orphan", order_by="desc(GradeAppeal.created_at)")


class AssignmentSubmissionVersion(Base):
    __tablename__ = "assignment_submission_versions"

    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(Integer, ForeignKey("assignment_submissions.id", ondelete="CASCADE"), nullable=False, index=True)
    version_number = Column(Integer, nullable=False)
    file_url = Column(String(500), nullable=True)
    text_content = Column(Text, nullable=True)
    attachments = Column(JSON, nullable=True)
    submission_receipt = Column(String(100), nullable=False)
    is_late = Column(Boolean, default=False, nullable=False)
    days_late = Column(Float, default=0.0, nullable=False)
    submitted_at = Column(DateTime, default=func.now(), nullable=False)

    submission = relationship("AssignmentSubmission", back_populates="versions")


# ─── Grading Workflows & Feedback Delivery Models ─────────────────────────────

class SubmissionAnnotation(Base):
    __tablename__ = "submission_annotations"

    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(Integer, ForeignKey("assignment_submissions.id", ondelete="CASCADE"), nullable=False, index=True)
    page_number = Column(Integer, nullable=True)
    coordinates = Column(JSON, nullable=True)  # {"x": 100, "y": 200, "width": 50, "height": 20}
    comment_text = Column(Text, nullable=False)
    author_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    submission = relationship("AssignmentSubmission", back_populates="annotations")
    author = relationship("User", foreign_keys=[author_id])


class GradeAppeal(Base):
    __tablename__ = "grade_appeals"

    id = Column(Integer, primary_key=True, index=True)
    assignment_id = Column(Integer, ForeignKey("assignments.id", ondelete="CASCADE"), nullable=False, index=True)
    submission_id = Column(Integer, ForeignKey("assignment_submissions.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    reason = Column(Text, nullable=False)
    requested_marks = Column(Float, nullable=True)
    status = Column(String(30), default="pending", nullable=False)  # pending, in_review, approved, rejected
    resolution_notes = Column(Text, nullable=True)
    resolved_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    assignment = relationship("Assignment", back_populates="appeals")
    submission = relationship("AssignmentSubmission", back_populates="appeals")
    student = relationship("Student")
    resolver = relationship("User", foreign_keys=[resolved_by_id])


# ─── Academic Integrity and Plagiarism Check Models ───────────────────────────

class PlagiarismScanReport(Base):
    __tablename__ = "plagiarism_scan_reports"

    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(Integer, ForeignKey("assignment_submissions.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    assignment_id = Column(Integer, ForeignKey("assignments.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    similarity_score = Column(Float, nullable=False, default=0.0)  # 0.0 to 100.0
    status = Column(String(30), default="completed", nullable=False)  # pending, scanning, completed, failed
    integrity_flag = Column(String(30), default="clean", nullable=False)  # clean, suspicious, flagged, resolved
    matched_sources = Column(JSON, nullable=True)  # [{"source_submission_id": 1, "matched_percentage": 50.0, "matched_words": 120}]
    scanned_content_hash = Column(String(64), nullable=True)
    instructor_notes = Column(Text, nullable=True)
    reviewed_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    submission = relationship("AssignmentSubmission", back_populates="plagiarism_report")
    assignment = relationship("Assignment")
    student = relationship("Student")
    reviewer = relationship("User", foreign_keys=[reviewed_by_id])


# ─── Rubric-Based Assessment Models ──────────────────────────────────────────

class Rubric(Base):
    __tablename__ = "rubrics"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=True, index=True)
    creator_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    scoring_strategy = Column(String(50), default="analytic", nullable=False)  # analytic, holistic, percentage
    is_template = Column(Boolean, default=False, nullable=False)
    total_points = Column(Float, default=100.0, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    course = relationship("Course", back_populates="rubrics")
    creator = relationship("User", foreign_keys=[creator_id])
    criteria = relationship("RubricCriterion", back_populates="rubric", cascade="all, delete-orphan", order_by="RubricCriterion.order_index")
    evaluations = relationship("RubricEvaluation", back_populates="rubric", cascade="all, delete-orphan")


class RubricCriterion(Base):
    __tablename__ = "rubric_criteria"

    id = Column(Integer, primary_key=True, index=True)
    rubric_id = Column(Integer, ForeignKey("rubrics.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    max_points = Column(Float, nullable=False, default=10.0)
    weight = Column(Float, nullable=False, default=1.0)
    order_index = Column(Integer, nullable=False, default=0)

    rubric = relationship("Rubric", back_populates="criteria")
    levels = relationship("RubricLevel", back_populates="criterion", cascade="all, delete-orphan", order_by="RubricLevel.order_index")


class RubricLevel(Base):
    __tablename__ = "rubric_levels"

    id = Column(Integer, primary_key=True, index=True)
    criterion_id = Column(Integer, ForeignKey("rubric_criteria.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)
    point_value = Column(Float, nullable=False, default=0.0)
    order_index = Column(Integer, nullable=False, default=0)

    criterion = relationship("RubricCriterion", back_populates="levels")


class RubricEvaluation(Base):
    __tablename__ = "rubric_evaluations"

    id = Column(Integer, primary_key=True, index=True)
    rubric_id = Column(Integer, ForeignKey("rubrics.id", ondelete="CASCADE"), nullable=False, index=True)
    assignment_id = Column(Integer, ForeignKey("assignments.id", ondelete="CASCADE"), nullable=False, index=True)
    submission_id = Column(Integer, ForeignKey("assignment_submissions.id", ondelete="CASCADE"), nullable=True, index=True)
    grader_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    total_score = Column(Float, nullable=False, default=0.0)
    max_possible_score = Column(Float, nullable=False, default=100.0)
    percentage = Column(Float, nullable=False, default=0.0)
    feedback = Column(Text, nullable=True)
    criteria_scores = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    rubric = relationship("Rubric", back_populates="evaluations")
    assignment = relationship("Assignment", back_populates="rubric_evaluations")
    submission = relationship("AssignmentSubmission", back_populates="rubric_evaluation")
    grader = relationship("User", foreign_keys=[grader_id])


# ─── Question Bank & Assessment Questions Models ──────────────────────────────

class QuestionCategory(Base):
    __tablename__ = "question_categories"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=True, index=True)
    parent_id = Column(Integer, ForeignKey("question_categories.id", ondelete="CASCADE"), nullable=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    display_order = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    course = relationship("Course", back_populates="question_categories")
    questions = relationship("QuestionBankItem", back_populates="category", cascade="all, delete-orphan")


class QuestionBankItem(Base):
    __tablename__ = "question_bank_items"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=True, index=True)
    category_id = Column(Integer, ForeignKey("question_categories.id", ondelete="SET NULL"), nullable=True, index=True)
    creator_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    rubric_id = Column(Integer, ForeignKey("rubrics.id", ondelete="SET NULL"), nullable=True, index=True)
    title = Column(String(255), nullable=False)
    prompt = Column(Text, nullable=False)
    question_type = Column(String(50), nullable=False)  # single_choice, multiple_choice, true_false, short_answer, essay, code_snippet, numerical
    difficulty_level = Column(String(20), default="intermediate", nullable=False)  # beginner, intermediate, advanced, expert
    default_points = Column(Float, default=1.0, nullable=False)
    explanation = Column(Text, nullable=True)
    tags = Column(JSON, nullable=True)  # ["trees", "recursion"]
    options = Column(JSON, nullable=True)  # [{"id": "opt_1", "text": "...", "is_correct": True, "feedback": "..."}]
    answer_key = Column(JSON, nullable=True)  # {"expected_text": "...", "tolerance": 0.05, "regex": "..."}
    is_active = Column(Boolean, default=True, nullable=False)
    usage_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    course = relationship("Course", back_populates="question_bank_items")
    category = relationship("QuestionCategory", back_populates="questions")
    creator = relationship("User", foreign_keys=[creator_id])
    rubric = relationship("Rubric", foreign_keys=[rubric_id])


# ─── Automated Quiz & Assessment Engine Models ────────────────────────────────

class Quiz(Base):
    __tablename__ = "quizzes"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    module_id = Column(Integer, ForeignKey("course_modules.id", ondelete="SET NULL"), nullable=True, index=True)
    creator_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    instructions = Column(Text, nullable=True)
    time_limit_minutes = Column(Integer, nullable=True)
    passing_score_percentage = Column(Float, default=50.0, nullable=False)
    max_attempts = Column(Integer, default=1, nullable=False)
    shuffle_questions = Column(Boolean, default=True, nullable=False)
    shuffle_options = Column(Boolean, default=True, nullable=False)
    show_correct_answers = Column(Boolean, default=True, nullable=False)
    allow_backtracking = Column(Boolean, default=True, nullable=False)
    total_points = Column(Float, default=0.0, nullable=False)
    category_id = Column(Integer, ForeignKey("gradebook_categories.id", ondelete="SET NULL"), nullable=True, index=True)
    status = Column(String(30), default="published", nullable=False)  # draft, published, closed
    available_from = Column(DateTime, nullable=True)
    due_date = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    course = relationship("Course", back_populates="quizzes")
    module = relationship("CourseModule")
    creator = relationship("User", foreign_keys=[creator_id])
    category = relationship("GradebookCategory", foreign_keys=[category_id])
    questions = relationship("QuizQuestion", back_populates="quiz", cascade="all, delete-orphan", order_by="QuizQuestion.order_index")
    attempts = relationship("QuizAttempt", back_populates="quiz", cascade="all, delete-orphan")
    proctoring_sessions = relationship("ExamProctoringSession", back_populates="quiz", cascade="all, delete-orphan")


class QuizQuestion(Base):
    __tablename__ = "quiz_questions"

    id = Column(Integer, primary_key=True, index=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False, index=True)
    question_item_id = Column(Integer, ForeignKey("question_bank_items.id", ondelete="CASCADE"), nullable=False, index=True)
    order_index = Column(Integer, default=0, nullable=False)
    points = Column(Float, default=1.0, nullable=False)

    quiz = relationship("Quiz", back_populates="questions")
    question_item = relationship("QuestionBankItem")


class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"

    id = Column(Integer, primary_key=True, index=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    attempt_number = Column(Integer, default=1, nullable=False)
    started_at = Column(DateTime, default=func.now(), nullable=False)
    submitted_at = Column(DateTime, nullable=True)
    total_score = Column(Float, default=0.0, nullable=False)
    max_score = Column(Float, default=0.0, nullable=False)
    percentage = Column(Float, default=0.0, nullable=False)
    is_passed = Column(Boolean, default=False, nullable=False)
    status = Column(String(30), default="in_progress", nullable=False)  # in_progress, submitted, graded, abandoned
    answers = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    quiz = relationship("Quiz", back_populates="attempts")
    student = relationship("Student")
    proctoring_session = relationship("ExamProctoringSession", back_populates="attempt", uselist=False, cascade="all, delete-orphan")


# ─── Timed Examinations and Proctoring Controls Models ────────────────────────

class ExamProctoringSession(Base):
    __tablename__ = "exam_proctoring_sessions"

    id = Column(Integer, primary_key=True, index=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    attempt_id = Column(Integer, ForeignKey("quiz_attempts.id", ondelete="CASCADE"), nullable=True, index=True)
    session_token = Column(String(100), unique=True, index=True, nullable=False)
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(255), nullable=True)
    started_at = Column(DateTime, default=func.now(), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    last_heartbeat_at = Column(DateTime, default=func.now(), nullable=False)
    status = Column(String(30), default="active", nullable=False)  # active, completed, terminated, flagged
    tab_switch_count = Column(Integer, default=0, nullable=False)
    fullscreen_exit_count = Column(Integer, default=0, nullable=False)
    copy_paste_attempt_count = Column(Integer, default=0, nullable=False)
    is_flagged = Column(Boolean, default=False, nullable=False)
    flag_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    quiz = relationship("Quiz", back_populates="proctoring_sessions")
    student = relationship("Student")
    attempt = relationship("QuizAttempt", back_populates="proctoring_session")
    events = relationship("ExamProctoringEvent", back_populates="session", cascade="all, delete-orphan", order_by="desc(ExamProctoringEvent.timestamp)")


class ExamProctoringEvent(Base):
    __tablename__ = "exam_proctoring_events"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("exam_proctoring_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type = Column(String(50), nullable=False)  # tab_switch, window_blur, fullscreen_exit, copy_paste_blocked, devtools_opened, auto_submitted
    severity = Column(String(20), default="low", nullable=False)  # low, medium, high, critical
    details = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=func.now(), nullable=False)

    session = relationship("ExamProctoringSession", back_populates="events")


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
    renewals_count = Column(Integer, default=0, nullable=False)
    renewed_at = Column(DateTime, nullable=True)
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
    priority_number = Column(Integer, default=1, nullable=False)
    reserved_at = Column(DateTime, default=func.now())
    expires_at = Column(DateTime, nullable=False)
    notified_at = Column(DateTime, nullable=True)
    status = Column(String(20), default="active")  # active, fulfilled, cancelled

    book = relationship("Book", back_populates="reservations")
    student = relationship("Student")


class LibraryFineRecord(Base):
    __tablename__ = "library_fine_records"

    id = Column(Integer, primary_key=True, index=True)
    borrow_id = Column(Integer, ForeignKey("borrow_records.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    amount = Column(Float, nullable=False)
    overdue_days = Column(Integer, default=0, nullable=False)
    status = Column(String(30), default="unpaid", nullable=False)  # unpaid, paid, waived
    waived_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    waiver_reason = Column(Text, nullable=True)
    paid_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    borrow = relationship("BorrowRecord")
    student = relationship("Student")
    waived_by = relationship("User")



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
    status = Column(String(30), default="published", nullable=False)  # draft, submitted, published, archived
    editorial_notes = Column(Text, nullable=True)
    likes_count = Column(Integer, default=0, nullable=False)
    target_audience = Column(String(30), default="all", nullable=False)  # all, students, faculty, public
    published_at = Column(DateTime, default=func.now())
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    author = relationship("User")
    comments = relationship("NewsComment", back_populates="news", cascade="all, delete-orphan")
    gallery = relationship("MediaGalleryItem", back_populates="news", cascade="all, delete-orphan", order_by="MediaGalleryItem.sort_order.asc()")
    reactions = relationship("NewsReaction", back_populates="news", cascade="all, delete-orphan")


class NewsComment(Base):
    __tablename__ = "news_comments"

    id = Column(Integer, primary_key=True, index=True)
    news_id = Column(Integer, ForeignKey("news.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=func.now())

    news = relationship("News", back_populates="comments")
    user = relationship("User")


class MediaGalleryItem(Base):
    __tablename__ = "media_gallery_items"

    id = Column(Integer, primary_key=True, index=True)
    news_id = Column(Integer, ForeignKey("news.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    media_type = Column(String(30), default="image", nullable=False)  # image, video, audio
    media_url = Column(String(500), nullable=False)
    caption = Column(String(300), nullable=True)
    sort_order = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    news = relationship("News", back_populates="gallery")


class NewsReaction(Base):
    __tablename__ = "news_reactions"

    id = Column(Integer, primary_key=True, index=True)
    news_id = Column(Integer, ForeignKey("news.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    reaction_type = Column(String(30), default="like", nullable=False)  # like, applause, insightful
    created_at = Column(DateTime, default=func.now(), nullable=False)

    news = relationship("News", back_populates="reactions")
    user = relationship("User")


# ─── Communication Models ─────────────────────────────────────────────────────

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(300), nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(String(50), default="info")  # info, warning, success, error
    category = Column(String(50), default="general", nullable=False, index=True)  # academic, deadline, announcement, system, finance, social
    priority = Column(String(20), default="normal", nullable=False)  # urgent, high, normal, low
    link = Column(String(500), nullable=True)
    is_read = Column(Boolean, default=False, nullable=False, index=True)
    read_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    extra_data = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    user = relationship("User", back_populates="notifications")


class NotificationPreference(Base):
    __tablename__ = "notification_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    email_enabled = Column(Boolean, default=True, nullable=False)
    in_app_enabled = Column(Boolean, default=True, nullable=False)
    push_enabled = Column(Boolean, default=True, nullable=False)
    sms_enabled = Column(Boolean, default=False, nullable=False)
    notify_academic = Column(Boolean, default=True, nullable=False)
    notify_deadlines = Column(Boolean, default=True, nullable=False)
    notify_announcements = Column(Boolean, default=True, nullable=False)
    notify_messages = Column(Boolean, default=True, nullable=False)
    notify_grades = Column(Boolean, default=True, nullable=False)
    quiet_hours_enabled = Column(Boolean, default=False, nullable=False)
    quiet_hours_start = Column(String(10), nullable=True)  # "22:00"
    quiet_hours_end = Column(String(10), nullable=True)  # "07:00"
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="notification_preferences")


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    subject = Column(String(255), nullable=True)
    thread_type = Column(String(50), default="direct", nullable=False)  # direct, course_inquiry, advising, group
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="SET NULL"), nullable=True, index=True)
    created_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    last_message_at = Column(DateTime, default=func.now(), nullable=False)
    status = Column(String(30), default="active", nullable=False)  # active, archived
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    course = relationship("Course")
    created_by = relationship("User", foreign_keys=[created_by_id])
    participants = relationship("ConversationParticipant", back_populates="conversation", cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan", order_by="Message.sent_at")


class ConversationParticipant(Base):
    __tablename__ = "conversation_participants"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    last_read_at = Column(DateTime, nullable=True)
    is_muted = Column(Boolean, default=False, nullable=False)
    joined_at = Column(DateTime, default=func.now(), nullable=False)

    conversation = relationship("Conversation", back_populates="participants")
    user = relationship("User")


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=True, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    receiver_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    subject = Column(String(255), nullable=True)
    content = Column(Text, nullable=False)
    attachment_url = Column(String(500), nullable=True)
    attachment_name = Column(String(200), nullable=True)
    is_read = Column(Boolean, default=False, nullable=False)
    read_at = Column(DateTime, nullable=True)
    is_moderated = Column(Boolean, default=False, nullable=False)
    moderation_flag = Column(String(50), nullable=True)
    sent_at = Column(DateTime, default=func.now(), nullable=False)

    sender = relationship("User", foreign_keys=[sender_id], back_populates="messages")
    receiver = relationship("User", foreign_keys=[receiver_id])
    conversation = relationship("Conversation", back_populates="messages")



# ─── Gradebook and Calculation Engine Models ──────────────────────────────────

class GradebookCategory(Base):
    __tablename__ = "gradebook_categories"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)  # e.g., Assignments, Quizzes, Midterm, Final
    weight_percentage = Column(Float, default=25.0, nullable=False)
    drop_lowest_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    course = relationship("Course", back_populates="gradebook_categories")


class GradeScale(Base):
    __tablename__ = "grade_scales"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=True, index=True)
    name = Column(String(100), default="Standard Letter Scale", nullable=False)
    is_default = Column(Boolean, default=False, nullable=False)
    scale_brackets = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    course = relationship("Course", back_populates="grade_scales")


class GradebookOverride(Base):
    __tablename__ = "gradebook_overrides"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    overridden_percentage = Column(Float, nullable=True)
    overridden_letter_grade = Column(String(10), nullable=True)
    overridden_gpa_points = Column(Float, nullable=True)
    override_reason = Column(Text, nullable=False)
    overridden_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    course = relationship("Course")
    student = relationship("Student")
    overridden_by = relationship("User", foreign_keys=[overridden_by_id])


class TimetableSlot(Base):
    __tablename__ = "timetable_slots"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=True, index=True)
    lecturer_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    day_of_week = Column(Integer, nullable=False, index=True)  # 0=Monday, 1=Tuesday, ..., 6=Sunday
    start_time = Column(String(10), nullable=False)  # HH:MM
    end_time = Column(String(10), nullable=False)    # HH:MM
    title = Column(String(200), nullable=False)
    slot_type = Column(String(50), default="lecture", nullable=False)  # lecture, lab, tutorial, exam, workshop
    room = Column(String(100), nullable=False)
    building = Column(String(100), nullable=True)
    recurrence_pattern = Column(String(50), default="weekly", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    color = Column(String(20), default="#4F46E5", nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    course = relationship("Course", back_populates="timetable_slots")
    lecturer = relationship("User", foreign_keys=[lecturer_id])


class AttendanceSession(Base):
    __tablename__ = "attendance_sessions"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    timetable_slot_id = Column(Integer, ForeignKey("timetable_slots.id", ondelete="SET NULL"), nullable=True, index=True)
    session_title = Column(String(200), nullable=False)
    session_date = Column(Date, nullable=False)
    start_time = Column(String(10), nullable=False)
    end_time = Column(String(10), nullable=False)
    checkin_code = Column(String(10), nullable=True)
    code_expires_at = Column(DateTime, nullable=True)
    status = Column(String(30), default="open", nullable=False)  # open, closed, archived
    allow_self_checkin = Column(Boolean, default=True, nullable=False)
    created_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    course = relationship("Course", back_populates="attendance_sessions")
    timetable_slot = relationship("TimetableSlot")
    created_by = relationship("User", foreign_keys=[created_by_id])
    attendances = relationship("Attendance", back_populates="session", cascade="all, delete-orphan")


class AttendanceCorrectionRequest(Base):
    __tablename__ = "attendance_correction_requests"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    session_id = Column(Integer, ForeignKey("attendance_sessions.id", ondelete="SET NULL"), nullable=True, index=True)
    attendance_date = Column(Date, nullable=False)
    requested_status = Column(String(30), default="excused", nullable=False)  # excused, present
    reason = Column(Text, nullable=False)
    supporting_document_url = Column(String(500), nullable=True)
    status = Column(String(30), default="pending", nullable=False)  # pending, approved, rejected
    reviewed_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    review_comment = Column(Text, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    student = relationship("Student")
    course = relationship("Course")
    session = relationship("AttendanceSession")
    reviewed_by = relationship("User", foreign_keys=[reviewed_by_id])


class StudentTask(Base):
    __tablename__ = "student_tasks"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="SET NULL"), nullable=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    due_date = Column(DateTime, nullable=True, index=True)
    priority = Column(String(20), default="medium", nullable=False)  # urgent, high, medium, low
    status = Column(String(20), default="todo", nullable=False)      # todo, in_progress, completed, cancelled
    category = Column(String(50), default="study", nullable=False)   # study, assignment, revision, exam_prep, personal, admin
    estimated_minutes = Column(Integer, default=60, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    reminder_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    student = relationship("Student")
    course = relationship("Course")


class CalendarEvent(Base):
    __tablename__ = "calendar_events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    event_type = Column(String(50), default="personal", nullable=False)  # academic, exam, assignment_due, lecture, holiday, campus, personal
    start_time = Column(DateTime, nullable=False, index=True)
    end_time = Column(DateTime, nullable=False, index=True)
    all_day = Column(Boolean, default=False, nullable=False)
    location = Column(String(200), nullable=True)
    color = Column(String(20), default="#4F46E5", nullable=False)
    is_system_generated = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    user = relationship("User")
    course = relationship("Course")


class CollaborationWorkspace(Base):
    __tablename__ = "collaboration_workspaces"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="SET NULL"), nullable=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    topic = Column(String(150), nullable=True)
    visibility = Column(String(30), default="course_public", nullable=False)  # private, course_public, invite_only
    owner_student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    join_code = Column(String(12), unique=True, index=True, nullable=False)
    shared_whiteboard_data = Column(JSON, nullable=True)
    meeting_link = Column(String(500), nullable=True)
    status = Column(String(30), default="active", nullable=False)  # active, archived
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    course = relationship("Course")
    owner = relationship("Student", foreign_keys=[owner_student_id])
    members = relationship("CollaborationWorkspaceMember", back_populates="workspace", cascade="all, delete-orphan")
    assets = relationship("CollaborationWorkspaceAsset", back_populates="workspace", cascade="all, delete-orphan", order_by="desc(CollaborationWorkspaceAsset.created_at)")
    messages = relationship("CollaborationWorkspaceMessage", back_populates="workspace", cascade="all, delete-orphan", order_by="CollaborationWorkspaceMessage.created_at")


class CollaborationWorkspaceMember(Base):
    __tablename__ = "collaboration_workspace_members"

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, ForeignKey("collaboration_workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(30), default="collaborator", nullable=False)  # owner, admin, collaborator, viewer
    joined_at = Column(DateTime, default=func.now(), nullable=False)

    workspace = relationship("CollaborationWorkspace", back_populates="members")
    student = relationship("Student")


class CollaborationWorkspaceAsset(Base):
    __tablename__ = "collaboration_workspace_assets"

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, ForeignKey("collaboration_workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    created_by_student_id = Column(Integer, ForeignKey("students.id", ondelete="SET NULL"), nullable=True, index=True)
    title = Column(String(255), nullable=False)
    asset_type = Column(String(50), default="note", nullable=False)  # document, link, code_snippet, note
    content = Column(Text, nullable=False)
    version = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    workspace = relationship("CollaborationWorkspace", back_populates="assets")
    created_by = relationship("Student", foreign_keys=[created_by_student_id])


class CollaborationWorkspaceMessage(Base):
    __tablename__ = "collaboration_workspace_messages"

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, ForeignKey("collaboration_workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    sender_student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    content = Column(Text, nullable=False)
    pinned = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    workspace = relationship("CollaborationWorkspace", back_populates="messages")
    sender = relationship("Student", foreign_keys=[sender_student_id])


# ─── Student Feedback and Course Evaluation Models ─────────────────────────────

class CourseEvaluationSurvey(Base):
    __tablename__ = "course_evaluation_surveys"

    id = Column(Integer, primary_key=True, index=True)
    institution_id = Column(Integer, ForeignKey("institutions.id", ondelete="SET NULL"), nullable=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    is_published = Column(Boolean, default=False, nullable=False)
    is_anonymous = Column(Boolean, default=True, nullable=False)
    created_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    course = relationship("Course")
    created_by = relationship("User", foreign_keys=[created_by_id])
    questions = relationship("SurveyQuestion", back_populates="survey", cascade="all, delete-orphan", order_by="SurveyQuestion.display_order")
    responses = relationship("SurveyResponse", back_populates="survey", cascade="all, delete-orphan")


class SurveyQuestion(Base):
    __tablename__ = "survey_questions"

    id = Column(Integer, primary_key=True, index=True)
    survey_id = Column(Integer, ForeignKey("course_evaluation_surveys.id", ondelete="CASCADE"), nullable=False, index=True)
    question_text = Column(Text, nullable=False)
    question_type = Column(String(50), default="rating_scale_5", nullable=False)  # rating_scale_5, rating_scale_10, text, single_choice, multiple_choice
    category = Column(String(50), default="instructor_effectiveness", nullable=False)  # instructor_effectiveness, course_content, facilities, assessment_fairness, overall
    is_required = Column(Boolean, default=True, nullable=False)
    options_json = Column(JSON, nullable=True)
    display_order = Column(Integer, default=0, nullable=False)

    survey = relationship("CourseEvaluationSurvey", back_populates="questions")
    answers = relationship("SurveyAnswer", back_populates="question", cascade="all, delete-orphan")


class SurveyResponse(Base):
    __tablename__ = "survey_responses"

    id = Column(Integer, primary_key=True, index=True)
    survey_id = Column(Integer, ForeignKey("course_evaluation_surveys.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="SET NULL"), nullable=True, index=True)
    student_hash = Column(String(64), nullable=True, index=True)
    submitted_at = Column(DateTime, default=func.now(), nullable=False)

    survey = relationship("CourseEvaluationSurvey", back_populates="responses")
    answers = relationship("SurveyAnswer", back_populates="response", cascade="all, delete-orphan")


class SurveyAnswer(Base):
    __tablename__ = "survey_answers"

    id = Column(Integer, primary_key=True, index=True)
    response_id = Column(Integer, ForeignKey("survey_responses.id", ondelete="CASCADE"), nullable=False, index=True)
    question_id = Column(Integer, ForeignKey("survey_questions.id", ondelete="CASCADE"), nullable=False, index=True)
    numeric_rating = Column(Float, nullable=True)
    text_response = Column(Text, nullable=True)
    selected_options_json = Column(JSON, nullable=True)

    response = relationship("SurveyResponse", back_populates="answers")
    question = relationship("SurveyQuestion", back_populates="answers")


# ─── Student Wellbeing and Support Models ──────────────────────────────────────

class WellbeingSupportRequest(Base):
    __tablename__ = "wellbeing_support_requests"

    id = Column(Integer, primary_key=True, index=True)
    institution_id = Column(Integer, ForeignKey("institutions.id", ondelete="SET NULL"), nullable=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    request_type = Column(String(50), default="counseling", nullable=False)  # academic_stress, mental_health, counseling, accessibility_accommodation, financial_emergency, peer_support
    subject = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    urgency = Column(String(30), default="normal", nullable=False)  # low, normal, high, crisis
    status = Column(String(30), default="submitted", nullable=False)  # submitted, assigned, in_progress, scheduled, resolved, closed
    assigned_counselor_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    is_confidential = Column(Boolean, default=True, nullable=False)
    resolution_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    student = relationship("Student")
    assigned_counselor = relationship("User", foreign_keys=[assigned_counselor_id])
    appointments = relationship("WellbeingAppointment", back_populates="request", cascade="all, delete-orphan")


class WellbeingAppointment(Base):
    __tablename__ = "wellbeing_appointments"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(Integer, ForeignKey("wellbeing_support_requests.id", ondelete="CASCADE"), nullable=False, index=True)
    counselor_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    appointment_type = Column(String(30), default="virtual", nullable=False)  # virtual, in_person
    scheduled_at = Column(DateTime, nullable=False)
    duration_minutes = Column(Integer, default=45, nullable=False)
    location_or_link = Column(String(500), nullable=True)
    status = Column(String(30), default="scheduled", nullable=False)  # scheduled, completed, cancelled, rescheduled
    meeting_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    request = relationship("WellbeingSupportRequest", back_populates="appointments")
    counselor = relationship("User", foreign_keys=[counselor_id])
    student = relationship("Student", foreign_keys=[student_id])


class WellbeingResource(Base):
    __tablename__ = "wellbeing_resources"

    id = Column(Integer, primary_key=True, index=True)
    institution_id = Column(Integer, ForeignKey("institutions.id", ondelete="SET NULL"), nullable=True, index=True)
    title = Column(String(255), nullable=False)
    category = Column(String(50), default="mental_health", nullable=False)  # mental_health, stress_management, mindfulness, crisis_hotline, study_habits, accessibility
    description = Column(Text, nullable=False)
    content_url = Column(String(500), nullable=True)
    emergency_phone = Column(String(50), nullable=True)
    is_crisis_resource = Column(Boolean, default=False, nullable=False)
    is_featured = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)


# ─── Student Billing and Fee Management Models ────────────────────────────────

class FeeStructure(Base):
    __tablename__ = "fee_structures"

    id = Column(Integer, primary_key=True, index=True)
    institution_id = Column(Integer, ForeignKey("institutions.id", ondelete="SET NULL"), nullable=True, index=True)
    program_id = Column(Integer, ForeignKey("programs.id", ondelete="SET NULL"), nullable=True, index=True)
    name = Column(String(255), nullable=False)
    term_type = Column(String(50), default="semester", nullable=False)  # semester, annual, modular
    total_amount = Column(Float, nullable=False)
    currency = Column(String(10), default="LKR", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    program = relationship("Program")
    components = relationship("FeeComponent", back_populates="fee_structure", cascade="all, delete-orphan")


class FeeComponent(Base):
    __tablename__ = "fee_components"

    id = Column(Integer, primary_key=True, index=True)
    fee_structure_id = Column(Integer, ForeignKey("fee_structures.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    amount = Column(Float, nullable=False)
    is_optional = Column(Boolean, default=False, nullable=False)
    description = Column(Text, nullable=True)

    fee_structure = relationship("FeeStructure", back_populates="components")


class StudentInvoice(Base):
    __tablename__ = "student_invoices"

    id = Column(Integer, primary_key=True, index=True)
    invoice_number = Column(String(50), unique=True, index=True, nullable=False)
    institution_id = Column(Integer, ForeignKey("institutions.id", ondelete="SET NULL"), nullable=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    fee_structure_id = Column(Integer, ForeignKey("fee_structures.id", ondelete="SET NULL"), nullable=True, index=True)
    academic_term = Column(String(50), nullable=False)
    total_amount = Column(Float, nullable=False)
    discount_amount = Column(Float, default=0.0, nullable=False)
    paid_amount = Column(Float, default=0.0, nullable=False)
    balance_due = Column(Float, nullable=False)
    currency = Column(String(10), default="LKR", nullable=False)
    issue_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=False)
    status = Column(String(30), default="unpaid", nullable=False)  # unpaid, partially_paid, paid, overdue, cancelled
    payment_plan_type = Column(String(30), default="full", nullable=False)  # full, installment_2, installment_3
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    student = relationship("Student")
    fee_structure = relationship("FeeStructure")
    items = relationship("InvoiceItem", back_populates="invoice", cascade="all, delete-orphan")
    installments = relationship("InvoicePaymentInstallment", back_populates="invoice", cascade="all, delete-orphan")


class InvoiceItem(Base):
    __tablename__ = "invoice_items"

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("student_invoices.id", ondelete="CASCADE"), nullable=False, index=True)
    component_name = Column(String(255), nullable=False)
    amount = Column(Float, nullable=False)

    invoice = relationship("StudentInvoice", back_populates="items")


class InvoicePaymentInstallment(Base):
    __tablename__ = "invoice_payment_installments"

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("student_invoices.id", ondelete="CASCADE"), nullable=False, index=True)
    installment_number = Column(Integer, nullable=False)
    amount = Column(Float, nullable=False)
    due_date = Column(Date, nullable=False)
    status = Column(String(30), default="pending", nullable=False)  # pending, paid, overdue
    paid_at = Column(DateTime, nullable=True)

    invoice = relationship("StudentInvoice", back_populates="installments")


# ─── Payment Gateway & Financial Auditing Models ─────────────────────────────

class PaymentTransaction(Base):
    __tablename__ = "payment_transactions"

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("student_invoices.id", ondelete="CASCADE"), nullable=False, index=True)
    installment_id = Column(Integer, ForeignKey("invoice_payment_installments.id", ondelete="SET NULL"), nullable=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    transaction_ref = Column(String(100), unique=True, index=True, nullable=False)
    gateway = Column(String(50), default="payhere", nullable=False)  # payhere, stripe, bank_transfer, cash
    gateway_reference = Column(String(150), nullable=True, index=True)
    amount = Column(Float, nullable=False)
    currency = Column(String(10), default="LKR", nullable=False)
    status = Column(String(30), default="pending", nullable=False)  # pending, completed, failed, refunded
    payment_method = Column(String(50), default="credit_card", nullable=False)  # credit_card, debit_card, bank_transfer, cash
    idempotency_key = Column(String(120), unique=True, nullable=True, index=True)
    payer_email = Column(String(255), nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    invoice = relationship("StudentInvoice")
    installment = relationship("InvoicePaymentInstallment")
    student = relationship("Student")
    receipt = relationship("PaymentReceipt", back_populates="transaction", uselist=False, cascade="all, delete-orphan")
    audit_logs = relationship("FinancialAuditLog", back_populates="transaction", cascade="all, delete-orphan")


class PaymentReceipt(Base):
    __tablename__ = "payment_receipts"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(Integer, ForeignKey("payment_transactions.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    invoice_id = Column(Integer, ForeignKey("student_invoices.id", ondelete="CASCADE"), nullable=False, index=True)
    receipt_number = Column(String(60), unique=True, index=True, nullable=False)
    receipt_url = Column(String(500), nullable=True)
    amount_paid = Column(Float, nullable=False)
    currency = Column(String(10), default="LKR", nullable=False)
    payment_method = Column(String(50), nullable=False)
    issued_at = Column(DateTime, default=func.now(), nullable=False)
    generated_by = Column(String(100), default="system", nullable=False)

    transaction = relationship("PaymentTransaction", back_populates="receipt")
    invoice = relationship("StudentInvoice")


class FinancialAuditLog(Base):
    __tablename__ = "financial_audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(Integer, ForeignKey("payment_transactions.id", ondelete="SET NULL"), nullable=True, index=True)
    invoice_id = Column(Integer, ForeignKey("student_invoices.id", ondelete="CASCADE"), nullable=True, index=True)
    actor_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action = Column(String(60), nullable=False)  # checkout_initiated, webhook_verified, receipt_issued, manual_payment_recorded, payment_failed, refund_processed
    old_status = Column(String(30), nullable=True)
    new_status = Column(String(30), nullable=True)
    amount = Column(Float, nullable=True)
    ip_address = Column(String(60), nullable=True)
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    transaction = relationship("PaymentTransaction", back_populates="audit_logs")
    invoice = relationship("StudentInvoice")
    actor = relationship("User")


# ─── Modern Digital Library System Models ────────────────────────────────────

class LibrarySubjectCollection(Base):
    __tablename__ = "library_subject_collections"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    slug = Column(String(200), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    icon = Column(String(50), default="📚", nullable=False)
    is_featured = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    resources = relationship("DigitalLibraryResource", back_populates="collection")


class DigitalLibraryResource(Base):
    __tablename__ = "digital_library_resources"

    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, ForeignKey("books.id", ondelete="SET NULL"), nullable=True, index=True)
    title = Column(String(350), nullable=False, index=True)
    author = Column(String(300), nullable=False, index=True)
    resource_type = Column(String(50), default="ebook", nullable=False)  # ebook, research_paper, journal_article, thesis, video_lecture, audio_resource
    doi_or_issn = Column(String(100), nullable=True, index=True)
    subject_category = Column(String(100), default="General", nullable=False, index=True)
    file_format = Column(String(20), default="pdf", nullable=False)  # pdf, epub, mp4, mp3, html
    file_url = Column(String(500), nullable=False)
    cover_url = Column(String(500), nullable=True)
    file_size_bytes = Column(Integer, default=0, nullable=False)
    download_count = Column(Integer, default=0, nullable=False)
    view_count = Column(Integer, default=0, nullable=False)
    abstract = Column(Text, nullable=True)
    keywords = Column(String(300), nullable=True)
    is_open_access = Column(Boolean, default=True, nullable=False)
    published_year = Column(Integer, nullable=True)
    publisher = Column(String(200), nullable=True)
    collection_id = Column(Integer, ForeignKey("library_subject_collections.id", ondelete="SET NULL"), nullable=True, index=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    book = relationship("Book")
    collection = relationship("LibrarySubjectCollection", back_populates="resources")
    bookmarks = relationship("LibraryResourceBookmark", back_populates="resource", cascade="all, delete-orphan")


class LibraryResourceBookmark(Base):
    __tablename__ = "library_resource_bookmarks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    resource_id = Column(Integer, ForeignKey("digital_library_resources.id", ondelete="CASCADE"), nullable=False, index=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    user = relationship("User")
    resource = relationship("DigitalLibraryResource", back_populates="bookmarks")


# ─── Sports and Athletic Management Models ───────────────────────────────────

class AthleticTeam(Base):
    __tablename__ = "athletic_teams"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    sport_type = Column(String(60), nullable=False, index=True)  # cricket, rugby, football, swimming, badminton, basketball, esports
    coach_name = Column(String(200), nullable=True)
    captain_name = Column(String(200), nullable=True)
    division = Column(String(60), default="Division 1", nullable=False)
    home_venue = Column(String(200), nullable=True)
    logo_url = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    roster = relationship("AthleteProfile", back_populates="team", cascade="all, delete-orphan")
    fixtures = relationship("SportsFixture", back_populates="team", cascade="all, delete-orphan")


class AthleteProfile(Base):
    __tablename__ = "athlete_profiles"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    team_id = Column(Integer, ForeignKey("athletic_teams.id", ondelete="CASCADE"), nullable=False, index=True)
    jersey_number = Column(Integer, nullable=True)
    position_or_role = Column(String(100), nullable=False)
    fitness_status = Column(String(30), default="fit", nullable=False)  # fit, injured, resting, convalescing
    matches_played = Column(Integer, default=0, nullable=False)
    points_or_goals = Column(Integer, default=0, nullable=False)
    mvp_awards = Column(Integer, default=0, nullable=False)
    joined_date = Column(Date, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    student = relationship("Student")
    team = relationship("AthleticTeam", back_populates="roster")


class SportsFixture(Base):
    __tablename__ = "sports_fixtures"

    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("athletic_teams.id", ondelete="CASCADE"), nullable=False, index=True)
    tournament_name = Column(String(255), nullable=False, index=True)
    opponent_name = Column(String(255), nullable=False)
    scheduled_time = Column(DateTime, nullable=False, index=True)
    venue = Column(String(200), nullable=False)
    fixture_type = Column(String(50), default="tournament", nullable=False)  # tournament, friendly, league, qualifier
    status = Column(String(30), default="upcoming", nullable=False)  # upcoming, ongoing, completed, postponed, cancelled
    our_score = Column(String(50), nullable=True)
    opponent_score = Column(String(50), nullable=True)
    match_result = Column(String(30), nullable=True)  # won, lost, drawn, abandoned
    highlights = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    team = relationship("AthleticTeam", back_populates="fixtures")


class SportsFacilityBooking(Base):
    __tablename__ = "sports_facility_bookings"

    id = Column(Integer, primary_key=True, index=True)
    facility_name = Column(String(150), nullable=False, index=True)
    booked_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    team_id = Column(Integer, ForeignKey("athletic_teams.id", ondelete="SET NULL"), nullable=True, index=True)
    start_time = Column(DateTime, nullable=False, index=True)
    end_time = Column(DateTime, nullable=False)
    purpose = Column(String(255), nullable=False)
    status = Column(String(30), default="confirmed", nullable=False)  # pending, confirmed, cancelled
    created_at = Column(DateTime, default=func.now(), nullable=False)

    booked_by = relationship("User")
    team = relationship("AthleticTeam")


# ─── Hostel and Accommodation Management ────────────────────────────────────

class HostelBuilding(Base):
    __tablename__ = "hostel_buildings"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False, unique=True, index=True)
    code = Column(String(50), nullable=False, unique=True, index=True)
    gender_type = Column(String(20), default="mixed", nullable=False)  # male, female, mixed
    total_floors = Column(Integer, default=4, nullable=False)
    warden_name = Column(String(150), nullable=False)
    warden_contact = Column(String(100), nullable=False)
    campus_location = Column(String(200), nullable=False)
    amenities = Column(JSON, nullable=True)  # list of strings (wifi, laundry, study_room, gym, cafeteria)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    rooms = relationship("HostelRoom", back_populates="building", cascade="all, delete-orphan")


class HostelRoom(Base):
    __tablename__ = "hostel_rooms"

    id = Column(Integer, primary_key=True, index=True)
    building_id = Column(Integer, ForeignKey("hostel_buildings.id", ondelete="CASCADE"), nullable=False, index=True)
    room_number = Column(String(50), nullable=False, index=True)
    floor = Column(Integer, default=1, nullable=False)
    room_type = Column(String(30), default="double", nullable=False)  # single, double, triple, quad
    capacity = Column(Integer, default=2, nullable=False)
    occupied_count = Column(Integer, default=0, nullable=False)
    monthly_fee = Column(Float, default=15000.0, nullable=False)
    status = Column(String(30), default="available", nullable=False)  # available, full, maintenance
    created_at = Column(DateTime, default=func.now(), nullable=False)

    building = relationship("HostelBuilding", back_populates="rooms")
    allocations = relationship("HostelAllocation", back_populates="room", cascade="all, delete-orphan")
    maintenance_requests = relationship("HostelMaintenanceRequest", back_populates="room", cascade="all, delete-orphan")


class HostelAllocation(Base):
    __tablename__ = "hostel_allocations"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    room_id = Column(Integer, ForeignKey("hostel_rooms.id", ondelete="CASCADE"), nullable=False, index=True)
    academic_year = Column(String(30), nullable=False)
    semester = Column(Integer, default=1, nullable=False)
    check_in_date = Column(Date, nullable=False)
    check_out_date = Column(Date, nullable=True)
    status = Column(String(30), default="active", nullable=False)  # pending, active, checked_out, cancelled
    deposit_paid = Column(Float, default=0.0, nullable=False)
    emergency_contact = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    student = relationship("Student")
    room = relationship("HostelRoom", back_populates="allocations")


class HostelMaintenanceRequest(Base):
    __tablename__ = "hostel_maintenance_requests"

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("hostel_rooms.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    issue_type = Column(String(50), nullable=False)  # plumbing, electrical, furniture, cleanliness, hvac, other
    description = Column(Text, nullable=False)
    priority = Column(String(20), default="medium", nullable=False)  # low, medium, high, urgent
    status = Column(String(30), default="reported", nullable=False)  # reported, in_progress, resolved, cancelled
    resolution_notes = Column(Text, nullable=True)
    reported_at = Column(DateTime, default=func.now(), nullable=False)
    resolved_at = Column(DateTime, nullable=True)

    room = relationship("HostelRoom", back_populates="maintenance_requests")
    student = relationship("Student")











