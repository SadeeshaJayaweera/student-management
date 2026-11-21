"""
NSBM EduSphere — All Pydantic Schemas
"""
from datetime import date, datetime
from typing import Optional, List, Any, Dict
from pydantic import BaseModel, EmailStr, Field, validator


# ─── Token & MFA Schemas ──────────────────────────────────────────────────────

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    refresh_token: Optional[str] = None
    expires_in: int = 900
    role: str
    user_id: int
    full_name: str

class TokenPair(Token):
    refresh_token: str

class LoginResponse(BaseModel):
    mfa_required: bool = False
    mfa_token: Optional[str] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_type: Optional[str] = "bearer"
    expires_in: Optional[int] = 900
    role: Optional[str] = None
    user_id: Optional[int] = None
    full_name: Optional[str] = None

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class MFASetupResponse(BaseModel):
    secret: str
    provisioning_uri: str

class MFAEnableRequest(BaseModel):
    code: str

class MFAEnableResponse(BaseModel):
    message: str
    backup_codes: List[str]

class MFAVerifyRequest(BaseModel):
    mfa_token: str
    code: str

class MFADisableRequest(BaseModel):
    password: str
    code: str


# ─── RBAC Schemas ─────────────────────────────────────────────────────────────

class PermissionOut(BaseModel):
    id: int
    code: str
    name: str
    description: Optional[str] = None
    module: str

    class Config:
        from_attributes = True

class RoleOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    is_system: bool
    permissions: List[str] = []

    class Config:
        from_attributes = True

class RoleCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=50)
    description: Optional[str] = None
    permission_codes: List[str] = []

class RolePermissionUpdateRequest(BaseModel):
    permission_codes: List[str]

class UserPermissionsResponse(BaseModel):
    user_id: int
    role: str
    permissions: List[str]


# ─── Multi-Tenant Institution Schemas ─────────────────────────────────────────

class InstitutionOut(BaseModel):
    id: int
    code: str
    name: str
    subdomain: Optional[str] = None
    domain: Optional[str] = None
    is_active: bool
    settings: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True

class InstitutionCreate(BaseModel):
    code: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=2, max_length=255)
    subdomain: Optional[str] = None
    domain: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None

class InstitutionUpdate(BaseModel):
    name: Optional[str] = None
    subdomain: Optional[str] = None
    domain: Optional[str] = None
    is_active: Optional[bool] = None
    settings: Optional[Dict[str, Any]] = None


# ─── Campus, Faculty, Department Schemas ──────────────────────────────────────

class CampusCreate(BaseModel):
    code: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=2, max_length=255)
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: str = "Sri Lanka"
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = None
    is_active: bool = True

class CampusUpdate(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = None
    is_active: Optional[bool] = None

class CampusOut(BaseModel):
    id: int
    institution_id: int
    code: str
    name: str
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: str
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class FacultyCreate(BaseModel):
    code: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=2, max_length=255)
    campus_id: Optional[int] = None
    description: Optional[str] = None
    dean_name: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    is_active: bool = True

class FacultyUpdate(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    campus_id: Optional[int] = None
    description: Optional[str] = None
    dean_name: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    is_active: Optional[bool] = None

class FacultyOut(BaseModel):
    id: int
    institution_id: int
    campus_id: Optional[int] = None
    code: str
    name: str
    description: Optional[str] = None
    dean_name: Optional[str] = None
    contact_email: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DepartmentCreate(BaseModel):
    code: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = None
    head_of_department: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    is_active: bool = True

class DepartmentUpdate(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    head_of_department: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    is_active: Optional[bool] = None

class DepartmentOut(BaseModel):
    id: int
    institution_id: int
    faculty_id: int
    code: str
    name: str
    description: Optional[str] = None
    head_of_department: Optional[str] = None
    contact_email: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ─── Academic Year & Semester Schemas ─────────────────────────────────────────

class AcademicYearCreate(BaseModel):
    code: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=2, max_length=100)
    start_date: date
    end_date: date
    is_current: bool = False
    is_active: bool = True

class AcademicYearUpdate(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_current: Optional[bool] = None
    is_active: Optional[bool] = None

class AcademicYearOut(BaseModel):
    id: int
    institution_id: int
    code: str
    name: str
    start_date: date
    end_date: date
    is_current: bool
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SemesterCreate(BaseModel):
    code: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=2, max_length=100)
    term_number: int = Field(default=1, ge=1, le=10)
    start_date: date
    end_date: date
    census_date: Optional[date] = None
    registration_start_date: Optional[date] = None
    registration_end_date: Optional[date] = None
    add_drop_deadline: Optional[date] = None
    exam_start_date: Optional[date] = None
    exam_end_date: Optional[date] = None
    is_current: bool = False
    is_active: bool = True

class SemesterUpdate(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    term_number: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    census_date: Optional[date] = None
    registration_start_date: Optional[date] = None
    registration_end_date: Optional[date] = None
    add_drop_deadline: Optional[date] = None
    exam_start_date: Optional[date] = None
    exam_end_date: Optional[date] = None
    is_current: Optional[bool] = None
    is_active: Optional[bool] = None

class SemesterOut(BaseModel):
    id: int
    institution_id: int
    academic_year_id: int
    code: str
    name: str
    term_number: int
    start_date: date
    end_date: date
    census_date: Optional[date] = None
    registration_start_date: Optional[date] = None
    registration_end_date: Optional[date] = None
    add_drop_deadline: Optional[date] = None
    exam_start_date: Optional[date] = None
    exam_end_date: Optional[date] = None
    is_current: bool
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ─── Program & Specialization Schemas ─────────────────────────────────────────

class ProgramCreate(BaseModel):
    code: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=2, max_length=255)
    qualification: str = Field(default="BSc", min_length=2, max_length=50)
    duration_years: float = Field(default=4.0, ge=0.5, le=10.0)
    total_credits: int = Field(default=120, ge=1, le=500)
    faculty_id: Optional[int] = None
    department_id: Optional[int] = None
    description: Optional[str] = None
    is_active: bool = True

class ProgramUpdate(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    qualification: Optional[str] = None
    duration_years: Optional[float] = None
    total_credits: Optional[int] = None
    faculty_id: Optional[int] = None
    department_id: Optional[int] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

class ProgramOut(BaseModel):
    id: int
    institution_id: int
    faculty_id: Optional[int] = None
    department_id: Optional[int] = None
    code: str
    name: str
    qualification: str
    duration_years: float
    total_credits: int
    description: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SpecializationCreate(BaseModel):
    code: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = None
    required_credits: int = Field(default=30, ge=1, le=200)
    is_active: bool = True

class SpecializationUpdate(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    required_credits: Optional[int] = None
    is_active: Optional[bool] = None

class SpecializationOut(BaseModel):
    id: int
    institution_id: int
    program_id: int
    code: str
    name: str
    description: Optional[str] = None
    required_credits: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserSessionOut(BaseModel):
    id: int
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    is_active: bool
    created_at: datetime
    expires_at: datetime
    last_activity_at: Optional[datetime] = None
    is_current: bool = False

    class Config:
        from_attributes = True

class TokenData(BaseModel):
    user_id: Optional[int] = None
    role: Optional[str] = None


# ─── User Schemas ─────────────────────────────────────────────────────────────

class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    full_name: str = Field(..., min_length=2, max_length=100)
    phone: Optional[str] = None

class UserCreate(UserBase):
    password: str = Field(..., min_length=6)
    role: str = "student"

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    avatar_url: Optional[str] = None

class UserOut(UserBase):
    id: int
    role: str
    avatar_url: Optional[str] = None
    is_active: bool
    is_verified: bool
    account_status: str = "active"
    institution_id: Optional[int] = None
    created_at: datetime
    class Config:
        from_attributes = True


# ─── Account Lifecycle Schemas ────────────────────────────────────────────────

class InvitationCreateRequest(BaseModel):
    email: EmailStr
    role: str = "student"
    institution_id: Optional[int] = None

class InvitationOut(BaseModel):
    id: int
    email: str
    role: str
    institution_id: Optional[int] = None
    status: str
    created_at: datetime
    expires_at: datetime
    invitation_token: Optional[str] = None

    class Config:
        from_attributes = True

class AcceptInvitationRequest(BaseModel):
    token: str
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=2, max_length=100)

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)

class SuspendAccountRequest(BaseModel):
    reason: str = Field(..., min_length=3, max_length=255)


# ─── Audit Trail Schemas ──────────────────────────────────────────────────────

class AuditLogOut(BaseModel):
    id: int
    timestamp: datetime
    event_type: str
    severity: str
    user_id: Optional[int] = None
    username: Optional[str] = None
    institution_id: Optional[int] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    correlation_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    username: str
    password: str


# ─── Student Schemas ──────────────────────────────────────────────────────────

class StudentCreate(BaseModel):
    user_id: int
    student_id: str
    faculty: Optional[str] = "Computing"
    department: Optional[str] = "Software Engineering"
    program: Optional[str] = "BSc in Software Engineering"
    year_of_study: int = 1
    semester: int = 1
    campus_id: Optional[int] = None
    program_id: Optional[int] = None
    faculty_id: Optional[int] = None
    department_id: Optional[int] = None
    enrollment_date: Optional[date] = None
    expected_graduation: Optional[date] = None
    address: Optional[str] = None
    emergency_contact: Optional[str] = None
    national_id: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    academic_standing: str = "good_standing"
    enrollment_status: str = "enrolled"
    scholarship: bool = False

class StudentUpdate(BaseModel):
    address: Optional[str] = None
    emergency_contact: Optional[str] = None
    year_of_study: Optional[int] = None
    semester: Optional[int] = None
    campus_id: Optional[int] = None
    program_id: Optional[int] = None
    academic_standing: Optional[str] = None
    enrollment_status: Optional[str] = None
    expected_graduation: Optional[date] = None
    scholarship: Optional[bool] = None

class StudentStatusUpdate(BaseModel):
    enrollment_status: Optional[str] = None  # enrolled, on_leave, suspended, graduated, withdrawn, deferred
    academic_standing: Optional[str] = None  # good_standing, academic_probation, deans_list, suspended, graduated
    remarks: Optional[str] = None

class StudentOut(BaseModel):
    id: int
    student_id: str
    faculty: str
    department: str
    program: str
    year_of_study: int
    semester: int
    gpa: float
    credits_earned: int
    address: Optional[str] = None
    emergency_contact: Optional[str] = None
    institution_id: Optional[int] = None
    campus_id: Optional[int] = None
    program_id: Optional[int] = None
    faculty_id: Optional[int] = None
    department_id: Optional[int] = None
    enrollment_date: Optional[date] = None
    expected_graduation: Optional[date] = None
    academic_standing: Optional[str] = "good_standing"
    enrollment_status: Optional[str] = "enrolled"
    national_id: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    scholarship: Optional[bool] = False
    user: UserOut
    class Config:
        from_attributes = True


# ─── Lecturer Schemas ─────────────────────────────────────────────────────────

class LecturerCreate(BaseModel):
    user_id: int
    lecturer_id: str
    faculty: str = "Computing"
    department: str = "Software Engineering"
    specialization: Optional[str] = None
    qualification: Optional[str] = None
    designation: str = "Lecturer"
    employment_status: str = "full_time"
    campus_id: Optional[int] = None
    faculty_id: Optional[int] = None
    department_id: Optional[int] = None
    office_location: Optional[str] = None
    office_hours: Optional[Dict[str, Any]] = None
    research_interests: Optional[str] = None
    bio: Optional[str] = None
    max_teaching_load_hours: int = 15
    joined_date: Optional[date] = None

class LecturerUpdate(BaseModel):
    faculty: Optional[str] = None
    department: Optional[str] = None
    specialization: Optional[str] = None
    qualification: Optional[str] = None
    office_location: Optional[str] = None
    office_hours: Optional[Dict[str, Any]] = None
    research_interests: Optional[str] = None
    bio: Optional[str] = None
    publications: Optional[int] = None
    campus_id: Optional[int] = None
    faculty_id: Optional[int] = None
    department_id: Optional[int] = None
    employment_status: Optional[str] = None
    designation: Optional[str] = None
    max_teaching_load_hours: Optional[int] = None

class LecturerWorkloadSummary(BaseModel):
    lecturer_id: str
    full_name: str
    designation: str
    employment_status: str
    max_teaching_load_hours: int
    current_teaching_load_hours: int
    assigned_courses_count: int
    total_enrolled_students: int
    courses: List[Dict[str, Any]]

class LecturerOut(BaseModel):
    id: int
    lecturer_id: str
    faculty: str
    department: str
    specialization: Optional[str] = None
    qualification: Optional[str] = None
    office_location: Optional[str] = None
    office_hours: Optional[Dict[str, Any]] = None
    bio: Optional[str] = None
    research_interests: Optional[str] = None
    publications: int = 0
    institution_id: Optional[int] = None
    campus_id: Optional[int] = None
    faculty_id: Optional[int] = None
    department_id: Optional[int] = None
    employment_status: str = "full_time"
    designation: str = "Lecturer"
    max_teaching_load_hours: int = 15
    current_teaching_load_hours: int = 0
    joined_date: Optional[date] = None
    user: UserOut
    class Config:
        from_attributes = True


# ─── Alumni Schemas ───────────────────────────────────────────────────────────

class AlumniOut(BaseModel):
    id: int
    alumni_id: str
    graduation_year: int
    degree: str
    current_position: Optional[str] = None
    current_company: Optional[str] = None
    industry: Optional[str] = None
    willing_to_mentor: bool
    location: Optional[str] = None
    bio: Optional[str] = None
    user: UserOut
    class Config:
        from_attributes = True

class AlumniExperienceCreate(BaseModel):
    title: str = Field(..., min_length=5, max_length=300)
    content: str = Field(..., min_length=20)
    category: str = "career"
    tags: Optional[List[str]] = None

class AlumniExperienceOut(AlumniExperienceCreate):
    id: int
    alumni_id: int
    likes: int
    is_published: bool
    image_url: Optional[str] = None
    created_at: datetime
    class Config:
        from_attributes = True


# ─── Course Schemas ───────────────────────────────────────────────────────────

class CourseCreate(BaseModel):
    course_code: str = Field(..., min_length=2, max_length=50)
    title: str = Field(..., min_length=2, max_length=200)
    description: Optional[str] = None
    credits: int = Field(default=3, ge=1, le=30)
    faculty: Optional[str] = "Computing"
    department: Optional[str] = "Software Engineering"
    semester: int = Field(default=1, ge=1, le=10)
    year: int = Field(default=1, ge=1, le=10)
    max_students: int = Field(default=60, ge=1, le=1000)
    lecturer_id: Optional[int] = None
    program_id: Optional[int] = None
    faculty_id: Optional[int] = None
    department_id: Optional[int] = None
    delivery_method: str = "in_person"
    learning_outcomes: Optional[List[str]] = None
    schedule: Optional[Dict[str, Any]] = None

class CourseUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    credits: Optional[int] = None
    faculty: Optional[str] = None
    department: Optional[str] = None
    semester: Optional[int] = None
    year: Optional[int] = None
    max_students: Optional[int] = None
    lecturer_id: Optional[int] = None
    program_id: Optional[int] = None
    faculty_id: Optional[int] = None
    department_id: Optional[int] = None
    delivery_method: Optional[str] = None
    learning_outcomes: Optional[List[str]] = None
    schedule: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None

class CoursePrerequisiteCreate(BaseModel):
    prerequisite_course_id: int
    is_mandatory: bool = True
    minimum_grade: str = "C"

class CoursePrerequisiteOut(BaseModel):
    id: int
    course_id: int
    prerequisite_course_id: int
    is_mandatory: bool
    minimum_grade: str
    created_at: datetime
    prerequisite_course_code: Optional[str] = None
    prerequisite_title: Optional[str] = None

    class Config:
        from_attributes = True

class CourseLessonBase(BaseModel):
    title: str = Field(..., min_length=2, max_length=255)
    lesson_type: str = "reading"
    content: Optional[str] = None
    resource_url: Optional[str] = None
    estimated_minutes: int = 15
    order_index: int = 1
    is_required: bool = True
    is_published: bool = True
    unlock_at: Optional[datetime] = None

class CourseLessonCreate(CourseLessonBase):
    pass

class CourseLessonUpdate(BaseModel):
    title: Optional[str] = None
    lesson_type: Optional[str] = None
    content: Optional[str] = None
    resource_url: Optional[str] = None
    estimated_minutes: Optional[int] = None
    order_index: Optional[int] = None
    is_required: Optional[bool] = None
    is_published: Optional[bool] = None
    unlock_at: Optional[datetime] = None

class CourseLessonOut(CourseLessonBase):
    id: int
    module_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class LessonContentCreate(BaseModel):
    raw_content: str = Field(..., min_length=1)
    content_format: str = "markdown"
    widget_configs: Optional[Dict[str, Any]] = None
    change_summary: Optional[str] = None

class LessonContentOut(BaseModel):
    id: int
    lesson_id: int
    version_number: int
    content_format: str
    raw_content: str
    rendered_content: str
    widget_configs: Optional[Dict[str, Any]] = None
    author_id: Optional[int] = None
    change_summary: Optional[str] = None
    is_current: bool
    created_at: datetime

    class Config:
        from_attributes = True

class LessonContentVersionSummary(BaseModel):
    id: int
    lesson_id: int
    version_number: int
    content_format: str
    change_summary: Optional[str] = None
    author_id: Optional[int] = None
    is_current: bool
    created_at: datetime

    class Config:
        from_attributes = True

class ModuleReorderRequest(BaseModel):
    module_ids: List[int]

class LessonReorderRequest(BaseModel):
    lesson_ids: List[int]

class CourseDocumentOut(BaseModel):
    id: int
    institution_id: Optional[int] = None
    course_id: int
    module_id: Optional[int] = None
    lesson_id: Optional[int] = None
    title: str
    original_filename: str
    mime_type: str
    file_size_bytes: int
    sha256_hash: str
    uploader_id: Optional[int] = None
    is_published: bool
    download_count: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class CourseDocumentUpdate(BaseModel):
    title: Optional[str] = None
    module_id: Optional[int] = None
    lesson_id: Optional[int] = None
    is_published: Optional[bool] = None

class VideoPlaybackProgressUpdate(BaseModel):
    position_seconds: int = Field(..., ge=0)
    watch_percentage: Optional[float] = None
    is_completed: Optional[bool] = None
    add_bookmark: Optional[Dict[str, Any]] = None
    add_note: Optional[Dict[str, Any]] = None

class VideoPlaybackProgressOut(BaseModel):
    id: int
    video_id: int
    student_id: int
    last_position_seconds: int
    max_watched_seconds: int
    watch_percentage: float
    is_completed: bool
    completed_at: Optional[datetime] = None
    bookmarks: Optional[List[Dict[str, Any]]] = None
    notes: Optional[List[Dict[str, Any]]] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class CourseVideoCreate(BaseModel):
    title: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = None
    provider: str = "self_hosted"
    video_url: str = Field(..., min_length=5, max_length=1024)
    duration_seconds: int = 0
    thumbnail_url: Optional[str] = None
    module_id: Optional[int] = None
    lesson_id: Optional[int] = None
    captions_track: Optional[List[Dict[str, Any]]] = None
    chapters: Optional[List[Dict[str, Any]]] = None
    is_published: bool = True

class CourseVideoUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    provider: Optional[str] = None
    video_url: Optional[str] = None
    duration_seconds: Optional[int] = None
    thumbnail_url: Optional[str] = None
    module_id: Optional[int] = None
    lesson_id: Optional[int] = None
    captions_track: Optional[List[Dict[str, Any]]] = None
    chapters: Optional[List[Dict[str, Any]]] = None
    is_published: Optional[bool] = None

class CourseVideoOut(BaseModel):
    id: int
    course_id: int
    module_id: Optional[int] = None
    lesson_id: Optional[int] = None
    title: str
    description: Optional[str] = None
    provider: str
    video_url: str
    duration_seconds: int
    thumbnail_url: Optional[str] = None
    captions_track: Optional[List[Dict[str, Any]]] = None
    chapters: Optional[List[Dict[str, Any]]] = None
    is_published: bool
    playback_progress: Optional[VideoPlaybackProgressOut] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class CourseModuleCreate(BaseModel):
    order_index: int = 1
    title: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = None
    learning_objectives: Optional[List[str]] = None
    estimated_hours: float = 10.0
    status: str = "published"
    unlock_at: Optional[datetime] = None
    prerequisite_module_id: Optional[int] = None
    is_active: bool = True

class CourseModuleUpdate(BaseModel):
    order_index: Optional[int] = None
    title: Optional[str] = None
    description: Optional[str] = None
    learning_objectives: Optional[List[str]] = None
    estimated_hours: Optional[float] = None
    status: Optional[str] = None
    unlock_at: Optional[datetime] = None
    prerequisite_module_id: Optional[int] = None
    is_active: Optional[bool] = None

class CourseModuleOut(BaseModel):
    id: int
    course_id: int
    order_index: int
    title: str
    description: Optional[str] = None
    learning_objectives: Optional[List[str]] = None
    estimated_hours: float
    status: str = "published"
    unlock_at: Optional[datetime] = None
    prerequisite_module_id: Optional[int] = None
    is_active: bool
    is_locked: Optional[bool] = False
    lock_reason: Optional[str] = None
    lessons: List[CourseLessonOut] = []
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class CourseOut(BaseModel):
    id: int
    course_code: str
    title: str
    description: Optional[str] = None
    credits: int
    faculty: Optional[str] = None
    department: Optional[str] = None
    semester: int
    year: int
    max_students: int
    is_active: bool
    institution_id: Optional[int] = None
    program_id: Optional[int] = None
    delivery_method: Optional[str] = "in_person"
    learning_outcomes: Optional[List[str]] = None
    syllabus_data: Optional[Dict[str, Any]] = None
    workspace_settings: Optional[Dict[str, Any]] = None
    banner_url: Optional[str] = None
    lecturer: Optional[LecturerOut] = None
    class Config:
        from_attributes = True

class CourseWorkspaceSettingsUpdate(BaseModel):
    syllabus_data: Optional[Dict[str, Any]] = None
    workspace_settings: Optional[Dict[str, Any]] = None
    banner_url: Optional[str] = None

class CourseWorkspaceOut(BaseModel):
    course_id: int
    course_code: str
    title: str
    description: Optional[str] = None
    credits: int
    delivery_method: str
    learning_outcomes: Optional[List[str]] = None
    schedule: Optional[Dict[str, Any]] = None
    banner_url: Optional[str] = None
    syllabus_data: Optional[Dict[str, Any]] = None
    workspace_settings: Optional[Dict[str, Any]] = None
    lecturer: Optional[Dict[str, Any]] = None
    stats: Dict[str, Any]
    user_context: Dict[str, Any]
    modules: List[Dict[str, Any]]
    recent_announcements: List[Dict[str, Any]]
    active_assignments: List[Dict[str, Any]]

# ─── Enrollment Schemas ───────────────────────────────────────────────────────

class EnrollmentRegisterRequest(BaseModel):
    course_id: int
    semester_id: Optional[int] = None
    registration_type: str = "regular"  # regular, audit, repeat
    remarks: Optional[str] = None

class EnrollmentStatusUpdate(BaseModel):
    status: str  # active, approved, waitlisted, dropped, withdrawn, rejected, completed
    rejection_reason: Optional[str] = None
    remarks: Optional[str] = None

class EnrollmentOut(BaseModel):
    id: int
    student_id: int
    course_id: int
    institution_id: Optional[int] = None
    semester_id: Optional[int] = None
    enrolled_at: datetime
    status: str
    waitlist_position: Optional[int] = None
    registration_type: str
    approved_by_id: Optional[int] = None
    approved_at: Optional[datetime] = None
    dropped_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    remarks: Optional[str] = None
    course: Optional[CourseOut] = None
    class Config:
        from_attributes = True

# ─── Cohort and Group Schemas ─────────────────────────────────────────────────

class CohortCreate(BaseModel):
    code: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=3, max_length=150)
    program_id: Optional[int] = None
    academic_year_id: Optional[int] = None
    year_of_study: int = 1
    semester_number: int = 1
    max_capacity: int = 60

class CohortUpdate(BaseModel):
    name: Optional[str] = None
    max_capacity: Optional[int] = None
    year_of_study: Optional[int] = None
    semester_number: Optional[int] = None
    is_active: Optional[bool] = None

class CohortMemberAdd(BaseModel):
    student_id: int
    role: str = "student"  # student, class_representative, vice_representative

class CohortMemberOut(BaseModel):
    id: int
    cohort_id: int
    student_id: int
    role: str
    joined_at: datetime
    status: str
    class Config:
        from_attributes = True

class CohortOut(BaseModel):
    id: int
    institution_id: int
    program_id: Optional[int] = None
    academic_year_id: Optional[int] = None
    code: str
    name: str
    year_of_study: int
    semester_number: int
    max_capacity: int
    is_active: bool
    created_at: datetime
    member_count: Optional[int] = 0
    class Config:
        from_attributes = True

class StudentGroupCreate(BaseModel):
    cohort_id: Optional[int] = None
    course_id: Optional[int] = None
    group_type: str = "tutorial"  # tutorial, lab, project_team, discussion
    name: str = Field(..., min_length=2, max_length=100)
    max_capacity: int = 30
    mentor_lecturer_id: Optional[int] = None
    schedule_info: Optional[Dict[str, Any]] = None

class StudentGroupMemberAdd(BaseModel):
    student_id: int
    group_role: str = "member"  # leader, member

class StudentGroupMemberOut(BaseModel):
    id: int
    group_id: int
    student_id: int
    group_role: str
    joined_at: datetime
    class Config:
        from_attributes = True

class StudentGroupOut(BaseModel):
    id: int
    institution_id: int
    cohort_id: Optional[int] = None
    course_id: Optional[int] = None
    group_type: str
    name: str
    max_capacity: int
    mentor_lecturer_id: Optional[int] = None
    schedule_info: Optional[Dict[str, Any]] = None
    is_active: bool
    created_at: datetime
    member_count: Optional[int] = 0
    class Config:
        from_attributes = True

# ─── Academic Advising and Student Support Schemas ────────────────────────────

class AdvisorAssignmentCreate(BaseModel):
    student_id: int
    lecturer_id: int
    advising_type: str = "academic"  # academic, career, pastoral, research_supervisor

class AdvisorAssignmentOut(BaseModel):
    id: int
    institution_id: int
    student_id: int
    lecturer_id: int
    assigned_date: date
    is_active: bool
    advising_type: str
    created_at: datetime
    class Config:
        from_attributes = True

class AdvisingSessionCreate(BaseModel):
    student_id: int
    lecturer_id: int
    scheduled_at: datetime
    duration_minutes: int = 30
    session_type: str = "one_on_one"
    topic: str
    student_notes: Optional[str] = None
    confidential_notes: Optional[str] = None
    action_items: Optional[List[Dict[str, Any]]] = None

class AdvisingSessionUpdate(BaseModel):
    status: Optional[str] = None  # scheduled, completed, cancelled, no_show
    student_notes: Optional[str] = None
    confidential_notes: Optional[str] = None
    action_items: Optional[List[Dict[str, Any]]] = None

class AdvisingSessionOut(BaseModel):
    id: int
    institution_id: int
    student_id: int
    lecturer_id: int
    scheduled_at: datetime
    duration_minutes: int
    session_type: str
    status: str
    topic: str
    student_notes: Optional[str] = None
    confidential_notes: Optional[str] = None
    action_items: Optional[List[Dict[str, Any]]] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    class Config:
        from_attributes = True

class StudentSupportCaseCreate(BaseModel):
    student_id: int
    category: str = "academic_probation"  # academic_probation, attendance_warning, financial_hardship, well_being, disciplinary
    priority: str = "medium"  # low, medium, high, critical
    title: str = Field(..., min_length=3, max_length=255)
    description: str
    assigned_staff_id: Optional[int] = None

class StudentSupportCaseUpdate(BaseModel):
    status: Optional[str] = None  # open, in_progress, escalated, resolved, closed
    priority: Optional[str] = None
    assigned_staff_id: Optional[int] = None
    resolution_summary: Optional[str] = None

class SupportCaseNoteCreate(BaseModel):
    content: str = Field(..., min_length=1)
    is_confidential: bool = False

class SupportCaseNoteOut(BaseModel):
    id: int
    case_id: int
    author_id: Optional[int] = None
    is_confidential: bool
    content: str
    created_at: datetime
    class Config:
        from_attributes = True

class StudentSupportCaseOut(BaseModel):
    id: int
    institution_id: int
    student_id: int
    assigned_staff_id: Optional[int] = None
    case_number: str
    category: str
    priority: str
    status: str
    title: str
    description: str
    resolution_summary: Optional[str] = None
    created_by_id: Optional[int] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    class Config:
        from_attributes = True

# ─── Academic Records and Transcript Schemas ──────────────────────────────────

class GradePostingRequest(BaseModel):
    student_id: int
    course_id: int
    semester_id: Optional[int] = None
    midterm: Optional[float] = None
    final: Optional[float] = None
    assignments_avg: Optional[float] = None
    total: Optional[float] = None
    letter_grade: Optional[str] = None
    grade_points: Optional[float] = None
    is_final: bool = True
    remarks: Optional[str] = None

class TermGPACalculationResult(BaseModel):
    student_id: int
    semester_id: int
    term_gpa: float
    cgpa: float
    credits_attempted: int
    credits_earned: int
    cumulative_credits_attempted: int
    cumulative_credits_earned: int
    academic_standing: str
    course_grades: List[Dict[str, Any]]

class OfficialTranscriptIssueRequest(BaseModel):
    student_id: int
    recipient_name: Optional[str] = None
    recipient_email: Optional[str] = None
    issue_type: str = "official"  # official, certified, unofficial

class OfficialTranscriptOut(BaseModel):
    id: int
    institution_id: int
    student_id: int
    verification_code: str
    digital_signature_hash: str
    issue_type: str
    status: str
    issued_by_id: Optional[int] = None
    issued_at: datetime
    recipient_name: Optional[str] = None
    recipient_email: Optional[str] = None
    data_snapshot: Dict[str, Any]
    class Config:
        from_attributes = True

class TranscriptVerificationResult(BaseModel):
    is_valid: bool
    verification_code: str
    issue_type: str
    status: str
    issued_at: datetime
    student_name: str
    student_id: str
    institution_name: str
    program_name: str
    cgpa: float
    total_credits_earned: int
    academic_standing: str
    digital_signature_hash: str

class GradeOut(BaseModel):
    id: int
    course_id: int
    midterm: Optional[float] = None
    final: Optional[float] = None
    assignments_avg: Optional[float] = None
    total: Optional[float] = None
    letter_grade: Optional[str] = None
    grade_points: Optional[float] = None
    remarks: Optional[str] = None
    course: CourseOut
    class Config:
        from_attributes = True

class AssignmentCreate(BaseModel):
    course_id: int
    title: str
    description: Optional[str] = None
    due_date: datetime
    max_marks: float = 100.0
    assignment_type: str = "assignment"

class AssignmentOut(AssignmentCreate):
    id: int
    file_url: Optional[str] = None
    created_at: datetime
    class Config:
        from_attributes = True

class SubmissionCreate(BaseModel):
    assignment_id: int
    text_content: Optional[str] = None

class GradeUpdate(BaseModel):
    assignment_id: int
    submission_id: int
    marks: float
    feedback: Optional[str] = None


# ─── Library Schemas ──────────────────────────────────────────────────────────

class BookCreate(BaseModel):
    isbn: Optional[str] = None
    title: str
    author: str
    publisher: Optional[str] = None
    year: Optional[int] = None
    edition: Optional[str] = None
    category: str
    subject: Optional[str] = None
    description: Optional[str] = None
    total_copies: int = 1
    is_ebook: bool = False

class BookOut(BaseModel):
    id: int
    isbn: Optional[str] = None
    title: str
    author: str
    publisher: Optional[str] = None
    year: Optional[int] = None
    category: str
    subject: Optional[str] = None
    description: Optional[str] = None
    cover_url: Optional[str] = None
    total_copies: int
    available_copies: int
    status: str
    is_ebook: bool
    location: Optional[str] = None
    class Config:
        from_attributes = True

class BorrowRecordOut(BaseModel):
    id: int
    book: BookOut
    borrowed_at: datetime
    due_date: datetime
    returned_at: Optional[datetime] = None
    status: str
    fine_amount: float
    fine_paid: bool
    class Config:
        from_attributes = True


# ─── Sports & Clubs Schemas ───────────────────────────────────────────────────

class ClubCreate(BaseModel):
    name: str
    description: Optional[str] = None
    category: str
    max_members: int = 100

class ClubOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    category: str
    logo_url: Optional[str] = None
    cover_url: Optional[str] = None
    president_name: Optional[str] = None
    achievements: Optional[str] = None
    max_members: int
    is_active: bool
    class Config:
        from_attributes = True

class ClubEventCreate(BaseModel):
    club_id: int
    title: str
    description: Optional[str] = None
    event_date: datetime
    location: Optional[str] = None
    max_participants: Optional[int] = None
    registration_required: bool = False
    is_public: bool = True

class ClubEventOut(ClubEventCreate):
    id: int
    image_url: Optional[str] = None
    created_at: datetime
    class Config:
        from_attributes = True


# ─── News Schemas ─────────────────────────────────────────────────────────────

class NewsCreate(BaseModel):
    title: str = Field(..., min_length=5, max_length=300)
    content: str = Field(..., min_length=50)
    summary: Optional[str] = None
    category: str
    tags: Optional[List[str]] = None
    is_featured: bool = False

class NewsOut(BaseModel):
    id: int
    title: str
    slug: str
    summary: Optional[str] = None
    category: str
    author: UserOut
    cover_image_url: Optional[str] = None
    tags: Optional[List[str]] = None
    views: int
    is_published: bool
    is_featured: bool
    published_at: datetime
    class Config:
        from_attributes = True

class NewsDetailOut(NewsOut):
    content: str

class NewsCommentCreate(BaseModel):
    content: str = Field(..., min_length=2)

class NewsCommentOut(NewsCommentCreate):
    id: int
    user: UserOut
    created_at: datetime
    class Config:
        from_attributes = True


# ─── Notification Schemas ─────────────────────────────────────────────────────

class NotificationOut(BaseModel):
    id: int
    title: str
    message: str
    notification_type: str
    link: Optional[str] = None
    is_read: bool
    created_at: datetime
    class Config:
        from_attributes = True


# ─── AI Schemas ───────────────────────────────────────────────────────────────

class AIQuery(BaseModel):
    question: str = Field(..., min_length=2, max_length=2000)
    context: Optional[str] = None  # optional portal context (library, sports, etc.)

class AIResponse(BaseModel):
    answer: str
    sources: Optional[List[str]] = None
    tokens_used: Optional[int] = None


# ─── Pagination Schema ────────────────────────────────────────────────────────

class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    size: int
    pages: int


# ─── Dashboard Summary Schemas ────────────────────────────────────────────────

class StudentDashboard(BaseModel):
    student: StudentOut
    enrolled_courses: int
    gpa: float
    credits_earned: int
    pending_assignments: int
    unread_notifications: int
    borrowed_books: int
    attendance_rate: float
    upcoming_events: List[Dict]
    recent_grades: List[Dict]

class LecturerDashboard(BaseModel):
    lecturer: LecturerOut
    total_courses: int
    total_students: int
    pending_submissions: int
    unread_notifications: int
    upcoming_classes: List[Dict]
    recent_activity: List[Dict]

class AdminDashboard(BaseModel):
    total_students: int
    total_lecturers: int
    total_alumni: int
    total_courses: int
    total_books: int
    total_clubs: int
    total_news: int
    recent_registrations: List[Dict]
    active_borrows: int
