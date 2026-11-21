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

class LessonProgressUpdate(BaseModel):
    status: str = "completed"
    time_spent_seconds: int = 0

class LessonProgressOut(BaseModel):
    id: int
    student_id: int
    lesson_id: int
    status: str
    time_spent_seconds: int
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ModuleProgressSummary(BaseModel):
    module_id: int
    module_title: str
    status: str
    completed_items_count: int
    total_items_count: int
    progress_percentage: float
    is_locked: bool
    completed_at: Optional[datetime] = None

class CourseProgressReport(BaseModel):
    course_id: int
    student_id: int
    student_name: str
    overall_progress_percentage: float
    completed_lessons_count: int
    total_lessons_count: int
    total_time_spent_seconds: int
    is_course_completed: bool
    modules: List[ModuleProgressSummary]

class StudentProgressRosterItem(BaseModel):
    student_id: int
    student_name: str
    student_code: str
    enrollment_status: str
    progress_percentage: float
    completed_lessons_count: int
    total_lessons_count: int
    is_completed: bool

class CourseAnnouncementCreate(BaseModel):
    title: str = Field(..., min_length=2, max_length=255)
    content: str = Field(..., min_length=1)
    priority: str = "normal"
    is_pinned: bool = False
    cohort_id: Optional[int] = None
    published_at: Optional[datetime] = None
    requires_acknowledgement: bool = False

class CourseAnnouncementUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    priority: Optional[str] = None
    is_pinned: Optional[bool] = None
    requires_acknowledgement: Optional[bool] = None

class CourseAnnouncementOut(BaseModel):
    id: int
    course_id: int
    author_id: Optional[int] = None
    author_name: Optional[str] = None
    cohort_id: Optional[int] = None
    title: str
    content: str
    priority: str
    is_pinned: bool
    requires_acknowledgement: bool
    is_acknowledged: Optional[bool] = False
    acknowledgements_count: int = 0
    published_at: datetime
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class AnnouncementAcknowledgeOut(BaseModel):
    id: int
    announcement_id: int
    student_id: int
    acknowledged_at: datetime

    class Config:
        from_attributes = True


# ─── Course Forum Schemas ─────────────────────────────────────────────────────

class CourseForumCategoryCreate(BaseModel):
    title: str = Field(..., min_length=2, max_length=150)
    description: Optional[str] = None
    is_locked: bool = False
    display_order: int = 0

class CourseForumCategoryUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    is_locked: Optional[bool] = None
    display_order: Optional[int] = None

class CourseForumCategoryOut(BaseModel):
    id: int
    course_id: int
    title: str
    description: Optional[str] = None
    is_locked: bool
    display_order: int
    thread_count: int = 0
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ForumThreadCreate(BaseModel):
    category_id: int
    title: str = Field(..., min_length=3, max_length=255)
    content: str = Field(..., min_length=1)
    is_pinned: bool = False

class ForumThreadUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    is_pinned: Optional[bool] = None
    is_locked: Optional[bool] = None
    category_id: Optional[int] = None

class ForumPostReactionOut(BaseModel):
    id: int
    post_id: int
    user_id: int
    reaction_type: str
    created_at: datetime

    class Config:
        from_attributes = True

class ForumPostOut(BaseModel):
    id: int
    thread_id: int
    author_id: int
    author_name: Optional[str] = None
    parent_post_id: Optional[int] = None
    content: str
    is_endorsed_by_instructor: bool
    is_solution: bool
    upvotes: int
    user_has_reacted: Optional[bool] = False
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ForumPostCreate(BaseModel):
    content: str = Field(..., min_length=1)
    parent_post_id: Optional[int] = None

class ForumPostUpdate(BaseModel):
    content: str = Field(..., min_length=1)

class ForumThreadSummaryOut(BaseModel):
    id: int
    course_id: int
    category_id: int
    category_title: Optional[str] = None
    author_id: int
    author_name: Optional[str] = None
    title: str
    is_pinned: bool
    is_locked: bool
    view_count: int
    reply_count: int
    has_solution: bool = False
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ForumThreadDetailOut(BaseModel):
    id: int
    course_id: int
    category_id: int
    category_title: Optional[str] = None
    author_id: int
    author_name: Optional[str] = None
    title: str
    content: str
    is_pinned: bool
    is_locked: bool
    view_count: int
    reply_count: int
    posts: List[ForumPostOut] = []
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ─── Virtual Classroom & Live Session Schemas ─────────────────────────────────

class VirtualClassroomSessionCreate(BaseModel):
    title: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = None
    provider: str = "zoom"  # zoom, google_meet, microsoft_teams, bigbluebutton, custom_hls
    meeting_id: Optional[str] = None
    join_url: str = Field(..., min_length=5, max_length=1024)
    host_url: Optional[str] = None
    passcode: Optional[str] = None
    start_time: datetime
    end_time: datetime
    is_recorded: bool = True
    max_participants: Optional[int] = 100
    session_settings: Optional[Dict[str, Any]] = None

class VirtualClassroomSessionUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    provider: Optional[str] = None
    meeting_id: Optional[str] = None
    join_url: Optional[str] = None
    host_url: Optional[str] = None
    passcode: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    status: Optional[str] = None  # scheduled, live, concluded, cancelled
    recording_url: Optional[str] = None
    recording_duration_minutes: Optional[int] = None
    is_recorded: Optional[bool] = None
    max_participants: Optional[int] = None
    session_settings: Optional[Dict[str, Any]] = None

class VirtualClassroomSessionOut(BaseModel):
    id: int
    course_id: int
    host_id: Optional[int] = None
    host_name: Optional[str] = None
    title: str
    description: Optional[str] = None
    provider: str
    meeting_id: Optional[str] = None
    join_url: str
    host_url: Optional[str] = None  # Only exposed to hosts/admins
    passcode: Optional[str] = None
    start_time: datetime
    end_time: datetime
    status: str
    recording_url: Optional[str] = None
    recording_duration_minutes: Optional[int] = None
    is_recorded: bool
    max_participants: Optional[int] = 100
    session_settings: Optional[Dict[str, Any]] = None
    participants_count: int = 0
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class VirtualClassroomAttendanceRecord(BaseModel):
    id: int
    session_id: int
    user_id: int
    student_id: Optional[int] = None
    participant_name: Optional[str] = None
    joined_at: datetime
    left_at: Optional[datetime] = None
    duration_minutes: int = 0
    device_type: Optional[str] = "browser"
    attendance_status: str = "present"
    created_at: datetime

    class Config:
        from_attributes = True

class VirtualClassroomJoinResponse(BaseModel):
    session_id: int
    join_url: str
    passcode: Optional[str] = None
    provider: str
    status: str
    attendance_id: int
    joined_at: datetime

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
    upcoming_live_sessions: Optional[List[Dict[str, Any]]] = None

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
    module_id: Optional[int] = None
    title: str = Field(..., min_length=2, max_length=300)
    description: Optional[str] = None
    due_date: datetime
    available_from: Optional[datetime] = None
    cutoff_date: Optional[datetime] = None
    max_marks: float = Field(100.0, gt=0)
    weightage_percentage: float = Field(10.0, ge=0, le=100)
    assignment_type: str = "assignment"  # assignment, quiz, project, lab, essay
    grading_type: str = "points"  # points, percentage, letter_grade, rubric
    status: str = "published"  # draft, published, open, closed, grading, graded, archived
    allow_late_submissions: bool = True
    late_penalty_percentage_per_day: float = Field(0.0, ge=0, le=100)
    submission_types: Optional[List[str]] = ["file", "text"]
    allowed_file_extensions: Optional[List[str]] = [".pdf", ".zip", ".docx"]
    max_file_size_mb: int = Field(50, gt=0, le=500)
    max_attempts: int = Field(1, ge=-1)
    anonymous_grading: bool = False
    peer_review_enabled: bool = False
    group_assignment: bool = False
    file_url: Optional[str] = None
    rubric_id: Optional[int] = None

class AssignmentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    module_id: Optional[int] = None
    due_date: Optional[datetime] = None
    available_from: Optional[datetime] = None
    cutoff_date: Optional[datetime] = None
    max_marks: Optional[float] = None
    weightage_percentage: Optional[float] = None
    assignment_type: Optional[str] = None
    grading_type: Optional[str] = None
    status: Optional[str] = None
    allow_late_submissions: Optional[bool] = None
    late_penalty_percentage_per_day: Optional[float] = None
    submission_types: Optional[List[str]] = None
    allowed_file_extensions: Optional[List[str]] = None
    max_file_size_mb: Optional[int] = None
    max_attempts: Optional[int] = None
    anonymous_grading: Optional[bool] = None
    peer_review_enabled: Optional[bool] = None
    group_assignment: Optional[bool] = None
    file_url: Optional[str] = None
    rubric_id: Optional[int] = None

class AssignmentOut(BaseModel):
    id: int
    course_id: int
    creator_id: Optional[int] = None
    module_id: Optional[int] = None
    title: str
    description: Optional[str] = None
    due_date: datetime
    available_from: Optional[datetime] = None
    cutoff_date: Optional[datetime] = None
    max_marks: float
    weightage_percentage: float
    assignment_type: str
    grading_type: str
    status: str
    allow_late_submissions: bool
    late_penalty_percentage_per_day: float
    submission_types: Optional[List[str]] = None
    allowed_file_extensions: Optional[List[str]] = None
    max_file_size_mb: int
    max_attempts: int
    anonymous_grading: bool
    peer_review_enabled: bool
    group_assignment: bool
    file_url: Optional[str] = None
    published_at: Optional[datetime] = None
    rubric_id: Optional[int] = None
    grades_released: bool = True
    grades_released_at: Optional[datetime] = None
    submissions_count: int = 0
    is_available: bool = True
    is_past_due: bool = False
    is_past_cutoff: bool = False
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# ─── Rubric Schemas ──────────────────────────────────────────────────────────

class RubricLevelCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=150)
    description: Optional[str] = None
    point_value: float = Field(..., ge=0)
    order_index: int = 0

class RubricLevelOut(BaseModel):
    id: int
    criterion_id: int
    title: str
    description: Optional[str] = None
    point_value: float
    order_index: int

    class Config:
        from_attributes = True

class RubricCriterionCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    max_points: float = Field(..., gt=0)
    weight: float = Field(1.0, ge=0)
    order_index: int = 0
    levels: Optional[List[RubricLevelCreate]] = []

class RubricCriterionOut(BaseModel):
    id: int
    rubric_id: int
    title: str
    description: Optional[str] = None
    max_points: float
    weight: float
    order_index: int
    levels: List[RubricLevelOut] = []

    class Config:
        from_attributes = True

class RubricCreate(BaseModel):
    title: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = None
    scoring_strategy: str = "analytic"  # analytic, holistic, percentage
    is_template: bool = False
    total_points: float = Field(100.0, gt=0)
    criteria: Optional[List[RubricCriterionCreate]] = []

class RubricUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    scoring_strategy: Optional[str] = None
    is_template: Optional[bool] = None
    total_points: Optional[float] = None

class RubricOut(BaseModel):
    id: int
    course_id: Optional[int] = None
    creator_id: Optional[int] = None
    title: str
    description: Optional[str] = None
    scoring_strategy: str
    is_template: bool
    total_points: float
    created_at: datetime
    updated_at: Optional[datetime] = None
    criteria: List[RubricCriterionOut] = []

    class Config:
        from_attributes = True

class CriterionEvaluationScore(BaseModel):
    criterion_id: int
    level_id: Optional[int] = None
    points: float = Field(..., ge=0)
    comment: Optional[str] = None

class RubricEvaluationCreate(BaseModel):
    submission_id: Optional[int] = None
    feedback: Optional[str] = None
    criteria_scores: List[CriterionEvaluationScore]

class RubricEvaluationOut(BaseModel):
    id: int
    rubric_id: int
    assignment_id: int
    submission_id: Optional[int] = None
    grader_id: Optional[int] = None
    total_score: float
    max_possible_score: float
    percentage: float
    feedback: Optional[str] = None
    criteria_scores: Optional[List[dict]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class SubmissionVersionOut(BaseModel):
    id: int
    submission_id: int
    version_number: int
    file_url: Optional[str] = None
    text_content: Optional[str] = None
    attachments: Optional[List[dict]] = None
    submission_receipt: str
    is_late: bool
    days_late: float
    submitted_at: datetime

    class Config:
        from_attributes = True

class SubmissionCreate(BaseModel):
    assignment_id: Optional[int] = None
    text_content: Optional[str] = None
    file_url: Optional[str] = None
    attachments: Optional[List[dict]] = None

class SubmissionOut(BaseModel):
    id: int
    assignment_id: int
    student_id: int
    attempt_number: int
    submission_receipt: Optional[str] = None
    file_url: Optional[str] = None
    text_content: Optional[str] = None
    attachments: Optional[List[dict]] = None
    is_late: bool
    days_late: float
    late_penalty_applied: float
    originality_score: Optional[float] = None
    originality_report_url: Optional[str] = None
    marks: Optional[float] = None
    feedback: Optional[str] = None
    status: str
    graded_by_id: Optional[int] = None
    graded_at: Optional[datetime] = None
    submitted_at: datetime
    updated_at: Optional[datetime] = None
    versions: List[SubmissionVersionOut] = []

    class Config:
        from_attributes = True

class SubmissionReceiptOut(BaseModel):
    submission_receipt: str
    submission_id: int
    assignment_id: int
    assignment_title: str
    course_code: str
    course_title: str
    student_id: int
    student_name: str
    attempt_number: int
    is_late: bool
    days_late: float
    submitted_at: datetime
    verification_hash: str

# ─── Question Bank Schemas ───────────────────────────────────────────────────

class QuestionCategoryCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=200)
    description: Optional[str] = None
    parent_id: Optional[int] = None
    display_order: int = 0

class QuestionCategoryOut(BaseModel):
    id: int
    course_id: Optional[int] = None
    parent_id: Optional[int] = None
    name: str
    description: Optional[str] = None
    display_order: int
    questions_count: int = 0
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class QuestionOption(BaseModel):
    id: str
    text: str
    is_correct: bool = False
    feedback: Optional[str] = None

class QuestionBankItemCreate(BaseModel):
    category_id: Optional[int] = None
    rubric_id: Optional[int] = None
    title: str = Field(..., min_length=2, max_length=255)
    prompt: str = Field(..., min_length=2)
    question_type: str = "single_choice"  # single_choice, multiple_choice, true_false, short_answer, essay, code_snippet, numerical
    difficulty_level: str = "intermediate"  # beginner, intermediate, advanced, expert
    default_points: float = Field(1.0, gt=0)
    explanation: Optional[str] = None
    tags: Optional[List[str]] = []
    options: Optional[List[QuestionOption]] = None
    answer_key: Optional[dict] = None
    is_active: bool = True

class QuestionBankItemUpdate(BaseModel):
    category_id: Optional[int] = None
    rubric_id: Optional[int] = None
    title: Optional[str] = None
    prompt: Optional[str] = None
    question_type: Optional[str] = None
    difficulty_level: Optional[str] = None
    default_points: Optional[float] = None
    explanation: Optional[str] = None
    tags: Optional[List[str]] = None
    options: Optional[List[QuestionOption]] = None
    answer_key: Optional[dict] = None
    is_active: Optional[bool] = None

class QuestionBankItemOut(BaseModel):
    id: int
    course_id: Optional[int] = None
    category_id: Optional[int] = None
    creator_id: Optional[int] = None
    rubric_id: Optional[int] = None
    title: str
    prompt: str
    question_type: str
    difficulty_level: str
    default_points: float
    explanation: Optional[str] = None
    tags: Optional[List[str]] = None
    options: Optional[List[dict]] = None
    answer_key: Optional[dict] = None
    is_active: bool
    usage_count: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# ─── Automated Quiz Schemas ──────────────────────────────────────────────────

class QuizCreate(BaseModel):
    module_id: Optional[int] = None
    title: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = None
    instructions: Optional[str] = None
    time_limit_minutes: Optional[int] = Field(None, gt=0)
    passing_score_percentage: float = Field(50.0, ge=0, le=100)
    max_attempts: int = Field(1, ge=-1)
    shuffle_questions: bool = True
    shuffle_options: bool = True
    show_correct_answers: bool = True
    allow_backtracking: bool = True
    status: str = "published"
    available_from: Optional[datetime] = None
    due_date: datetime

class QuizUpdate(BaseModel):
    module_id: Optional[int] = None
    title: Optional[str] = None
    description: Optional[str] = None
    instructions: Optional[str] = None
    time_limit_minutes: Optional[int] = None
    passing_score_percentage: Optional[float] = None
    max_attempts: Optional[int] = None
    shuffle_questions: Optional[bool] = None
    shuffle_options: Optional[bool] = None
    show_correct_answers: Optional[bool] = None
    allow_backtracking: Optional[bool] = None
    status: Optional[str] = None
    available_from: Optional[datetime] = None
    due_date: Optional[datetime] = None

class QuizQuestionAdd(BaseModel):
    question_item_id: int
    points: float = Field(1.0, gt=0)
    order_index: Optional[int] = None

class QuizQuestionOut(BaseModel):
    id: int
    quiz_id: int
    question_item_id: int
    order_index: int
    points: float
    question_item: Optional[QuestionBankItemOut] = None

    class Config:
        from_attributes = True

class QuizOut(BaseModel):
    id: int
    course_id: int
    module_id: Optional[int] = None
    creator_id: Optional[int] = None
    title: str
    description: Optional[str] = None
    instructions: Optional[str] = None
    time_limit_minutes: Optional[int] = None
    passing_score_percentage: float
    max_attempts: int
    shuffle_questions: bool
    shuffle_options: bool
    show_correct_answers: bool
    allow_backtracking: bool
    total_points: float
    status: str
    available_from: Optional[datetime] = None
    due_date: datetime
    questions_count: int = 0
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class StudentQuizQuestionOut(BaseModel):
    id: int
    order_index: int
    points: float
    title: str
    prompt: str
    question_type: str
    options: Optional[List[dict]] = None

class QuizStartOut(BaseModel):
    attempt_id: int
    quiz_id: int
    attempt_number: int
    time_limit_minutes: Optional[int] = None
    started_at: datetime
    questions: List[StudentQuizQuestionOut]

class QuizAnswerItem(BaseModel):
    question_id: int
    selected_option_ids: Optional[List[str]] = None
    text_answer: Optional[str] = None
    numerical_answer: Optional[float] = None

class QuizAutosavePayload(BaseModel):
    answers: List[QuizAnswerItem]

class QuizSubmitPayload(BaseModel):
    answers: List[QuizAnswerItem]

class QuizAttemptOut(BaseModel):
    id: int
    quiz_id: int
    student_id: int
    attempt_number: int
    started_at: datetime
    submitted_at: Optional[datetime] = None
    total_score: float
    max_score: float
    percentage: float
    is_passed: bool
    status: str
    results: Optional[List[dict]] = None
    created_at: datetime

    class Config:
        from_attributes = True

# ─── Timed Examinations and Proctoring Controls Schemas ───────────────────────

class ProctoringSessionStart(BaseModel):
    attempt_id: Optional[int] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

class ProctoringEventCreate(BaseModel):
    event_type: str  # tab_switch, window_blur, fullscreen_exit, copy_paste_blocked, devtools_opened
    severity: str = "medium"
    details: Optional[dict] = None

class ProctoringEventOut(BaseModel):
    id: int
    session_id: int
    event_type: str
    severity: str
    details: Optional[dict] = None
    timestamp: datetime

    class Config:
        from_attributes = True

class ProctoringSessionOut(BaseModel):
    id: int
    quiz_id: int
    student_id: int
    attempt_id: Optional[int] = None
    session_token: str
    started_at: datetime
    expires_at: datetime
    last_heartbeat_at: datetime
    status: str
    tab_switch_count: int
    fullscreen_exit_count: int
    copy_paste_attempt_count: int
    is_flagged: bool
    flag_reason: Optional[str] = None
    remaining_seconds: float = 0.0
    created_at: datetime
    events: List[ProctoringEventOut] = []

    class Config:
        from_attributes = True

class ProctoringHeartbeatOut(BaseModel):
    status: str
    remaining_seconds: float
    is_flagged: bool
    tab_switch_count: int
    fullscreen_exit_count: int
    server_time: datetime

# ─── Academic Integrity and Plagiarism Schemas ────────────────────────────────

class PlagiarismReportReview(BaseModel):
    integrity_flag: str  # clean, suspicious, flagged, resolved, false_positive
    instructor_notes: Optional[str] = None

class PlagiarismReportOut(BaseModel):
    id: int
    submission_id: int
    assignment_id: int
    student_id: int
    similarity_score: float
    status: str
    integrity_flag: str
    matched_sources: Optional[List[dict]] = None
    scanned_content_hash: Optional[str] = None
    instructor_notes: Optional[str] = None
    reviewed_by_id: Optional[int] = None
    reviewed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class PlagiarismBulkScanResult(BaseModel):
    assignment_id: int
    submissions_scanned: int
    flagged_count: int
    suspicious_count: int
    clean_count: int

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

# ─── Grading Workflows & Feedback Delivery Schemas ────────────────────────────

class SubmissionGradePayload(BaseModel):
    marks: float = Field(..., ge=0)
    feedback: Optional[str] = None
    rubric_evaluation_id: Optional[int] = None

class SubmissionAnnotationCreate(BaseModel):
    page_number: Optional[int] = None
    coordinates: Optional[dict] = None
    comment_text: str = Field(..., min_length=1)

class SubmissionAnnotationOut(BaseModel):
    id: int
    submission_id: int
    page_number: Optional[int] = None
    coordinates: Optional[dict] = None
    comment_text: str
    author_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class GradeAppealCreate(BaseModel):
    reason: str = Field(..., min_length=10)
    requested_marks: Optional[float] = None

class GradeAppealResolve(BaseModel):
    status: str  # approved, rejected, in_review
    adjusted_marks: Optional[float] = None
    resolution_notes: str = Field(..., min_length=2)

class GradeAppealOut(BaseModel):
    id: int
    assignment_id: int
    submission_id: int
    student_id: int
    reason: str
    requested_marks: Optional[float] = None
    status: str
    resolution_notes: Optional[str] = None
    resolved_by_id: Optional[int] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class AssignmentGradeReleaseOut(BaseModel):
    assignment_id: int
    grades_released: bool
    grades_released_at: datetime
    submissions_graded_count: int


# ─── Gradebook and Calculation Engine Schemas ─────────────────────────────────

class GradeScaleBracket(BaseModel):
    letter_grade: str
    min_percentage: float
    max_percentage: float
    gpa_points: float

class GradeScaleCreate(BaseModel):
    name: str = "Standard Letter Scale"
    is_default: bool = False
    scale_brackets: List[GradeScaleBracket]

class GradeScaleOut(BaseModel):
    id: int
    course_id: Optional[int] = None
    name: str
    is_default: bool
    scale_brackets: List[dict]
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class GradebookCategoryCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    weight_percentage: float = Field(..., ge=0, le=100)
    drop_lowest_count: int = Field(0, ge=0)

class GradebookCategoryOut(BaseModel):
    id: int
    course_id: int
    name: str
    weight_percentage: float
    drop_lowest_count: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class GradebookOverridePayload(BaseModel):
    student_id: int
    overridden_percentage: Optional[float] = Field(None, ge=0, le=100)
    overridden_letter_grade: Optional[str] = None
    overridden_gpa_points: Optional[float] = Field(None, ge=0, le=4.0)
    override_reason: str = Field(..., min_length=5)

class GradebookOverrideOut(BaseModel):
    id: int
    course_id: int
    student_id: int
    overridden_percentage: Optional[float] = None
    overridden_letter_grade: Optional[str] = None
    overridden_gpa_points: Optional[float] = None
    override_reason: str
    overridden_by_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class AssessmentScoreItem(BaseModel):
    item_id: int
    item_title: str
    item_type: str  # "assignment" or "quiz"
    category_id: Optional[int] = None
    category_name: Optional[str] = None
    score: Optional[float] = None
    max_marks: float
    percentage: Optional[float] = None
    is_dropped: bool = False
    status: str

class CategoryScoreSummary(BaseModel):
    category_id: Optional[int] = None
    category_name: str
    weight_percentage: float
    drop_lowest_count: int
    earned_percentage: Optional[float] = None
    weighted_contribution: Optional[float] = None
    items: List[AssessmentScoreItem] = []

class StudentGradeSummary(BaseModel):
    student_id: int
    student_number: str
    full_name: str
    email: str
    category_scores: List[CategoryScoreSummary] = []
    calculated_percentage: float
    letter_grade: str
    gpa_points: float
    is_overridden: bool = False
    override_details: Optional[GradebookOverrideOut] = None
    final_percentage: float
    final_letter_grade: str
    final_gpa_points: float

class CourseGradebookOut(BaseModel):
    course_id: int
    course_code: str
    course_title: str
    total_enrolled: int
    average_percentage: float
    categories: List[GradebookCategoryOut] = []
    grade_scale: Optional[dict] = None
    students: List[StudentGradeSummary] = []

class GradebookExportOut(BaseModel):
    course_code: str
    exported_at: datetime
    format: str
    records_count: int
    data: List[dict]


# ─── Personalized Student Dashboard Schemas ───────────────────────────────────

class CourseProgressSummary(BaseModel):
    course_id: int
    course_code: str
    course_title: str
    faculty: str
    department: str
    lecturer_name: str
    delivery_method: str
    completed_lessons: int
    total_lessons: int
    progress_percentage: float
    current_grade_percentage: Optional[float] = None
    letter_grade: Optional[str] = None
    attendance_rate: float

class UpcomingDeadlineItem(BaseModel):
    id: int
    item_type: str  # "assignment" or "quiz"
    title: str
    course_id: int
    course_code: str
    course_title: str
    due_date: datetime
    days_remaining: float
    is_overdue: bool
    max_marks: float
    submission_status: str  # "pending", "submitted", "graded", "missed"

class UpcomingClassSession(BaseModel):
    session_id: int
    course_id: int
    course_code: str
    course_title: str
    title: str
    start_time: datetime
    duration_minutes: int
    session_type: str
    join_url: Optional[str] = None
    is_live: bool

class DashboardAnnouncementItem(BaseModel):
    id: int
    course_id: int
    course_code: str
    course_title: str
    title: str
    content: str
    is_pinned: bool
    author_name: str
    published_at: datetime

class PersonalizedRecommendation(BaseModel):
    id: str
    category: str  # "urgent_deadline", "learning_progress", "academic_alert", "study_resource"
    priority: str  # "high", "medium", "low"
    title: str
    description: str
    action_label: str
    action_link: str

class PersonalizedStudentDashboardOut(BaseModel):
    student_id: str
    full_name: str
    email: str
    faculty: str
    department: str
    program: str
    year_of_study: int
    semester: int
    gpa: float
    credits_earned: int
    overall_attendance_rate: float
    enrolled_courses_count: int
    pending_tasks_count: int
    unread_notifications_count: int
    courses_progress: List[CourseProgressSummary]
    upcoming_deadlines: List[UpcomingDeadlineItem]
    upcoming_classes: List[UpcomingClassSession]
    recent_announcements: List[DashboardAnnouncementItem]
    recommendations: List[PersonalizedRecommendation]


# ─── Timetable Schemas ────────────────────────────────────────────────────────

class TimetableSlotBase(BaseModel):
    course_id: Optional[int] = None
    lecturer_id: Optional[int] = None
    day_of_week: int = Field(..., ge=0, le=6)  # 0=Monday, 6=Sunday
    start_time: str = Field(..., pattern=r"^([01]\d|2[0-3]):([0-5]\d)$")
    end_time: str = Field(..., pattern=r"^([01]\d|2[0-3]):([0-5]\d)$")
    title: str
    slot_type: str = "lecture"
    room: str
    building: Optional[str] = None
    recurrence_pattern: str = "weekly"
    is_active: bool = True
    color: str = "#4F46E5"
    notes: Optional[str] = None

class TimetableSlotCreate(TimetableSlotBase):
    allow_conflicts: bool = False

class TimetableSlotUpdate(BaseModel):
    course_id: Optional[int] = None
    lecturer_id: Optional[int] = None
    day_of_week: Optional[int] = Field(None, ge=0, le=6)
    start_time: Optional[str] = Field(None, pattern=r"^([01]\d|2[0-3]):([0-5]\d)$")
    end_time: Optional[str] = Field(None, pattern=r"^([01]\d|2[0-3]):([0-5]\d)$")
    title: Optional[str] = None
    slot_type: Optional[str] = None
    room: Optional[str] = None
    building: Optional[str] = None
    recurrence_pattern: Optional[str] = None
    is_active: Optional[bool] = None
    color: Optional[str] = None
    notes: Optional[str] = None
    allow_conflicts: bool = False

class TimetableSlotOut(TimetableSlotBase):
    id: int
    course_code: Optional[str] = None
    course_title: Optional[str] = None
    lecturer_name: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ScheduleConflict(BaseModel):
    conflict_type: str  # "room_double_booked", "lecturer_overlap", "student_overlap"
    slot_id: Optional[int] = None
    title: str
    day_of_week: int
    start_time: str
    end_time: str
    room: str
    description: str

class ConflictCheckPayload(BaseModel):
    course_id: Optional[int] = None
    lecturer_id: Optional[int] = None
    room: str
    day_of_week: int
    start_time: str
    end_time: str
    exclude_slot_id: Optional[int] = None

class ConflictCheckResponse(BaseModel):
    has_conflict: bool
    conflicts: List[ScheduleConflict]

class StudentTimetableDay(BaseModel):
    day_of_week: int
    day_name: str
    slots: List[TimetableSlotOut]

class StudentTimetableResponse(BaseModel):
    student_id: str
    student_name: str
    schedule: List[StudentTimetableDay]
    total_slots: int
    conflicts_detected: List[ScheduleConflict]


# ─── Attendance & Participation Schemas ────────────────────────────────────────

class AttendanceSessionCreate(BaseModel):
    course_id: int
    timetable_slot_id: Optional[int] = None
    session_title: str
    session_date: date
    start_time: str = Field(..., pattern=r"^([01]\d|2[0-3]):([0-5]\d)$")
    end_time: str = Field(..., pattern=r"^([01]\d|2[0-3]):([0-5]\d)$")
    allow_self_checkin: bool = True
    code_valid_minutes: int = 120

class AttendanceSessionOut(BaseModel):
    id: int
    course_id: int
    course_code: Optional[str] = None
    course_title: Optional[str] = None
    session_title: str
    session_date: date
    start_time: str
    end_time: str
    checkin_code: Optional[str] = None
    code_expires_at: Optional[datetime] = None
    status: str
    allow_self_checkin: bool
    attendances_count: int = 0
    created_at: datetime

    class Config:
        from_attributes = True

class AttendanceCheckinPayload(BaseModel):
    checkin_code: str

class AttendanceRosterItem(BaseModel):
    student_id: int
    status: str = "present"  # present, absent, late, excused
    participation_score: float = Field(0.0, ge=0.0, le=100.0)
    notes: Optional[str] = None

class AttendanceBatchRosterPayload(BaseModel):
    items: List[AttendanceRosterItem]

class AttendanceRecordDetail(BaseModel):
    id: int
    student_id: int
    student_reg_id: str
    student_name: str
    session_id: Optional[int] = None
    date: date
    status: str
    checkin_method: str
    checked_in_at: Optional[datetime] = None
    participation_score: float
    notes: Optional[str] = None
    remarks: Optional[str] = None

class AttendanceCorrectionCreate(BaseModel):
    course_id: int
    session_id: Optional[int] = None
    attendance_date: date
    requested_status: str = "excused"  # excused, present
    reason: str
    supporting_document_url: Optional[str] = None

class AttendanceCorrectionResolve(BaseModel):
    status: str  # approved, rejected
    review_comment: Optional[str] = None

class AttendanceCorrectionOut(BaseModel):
    id: int
    student_id: int
    student_reg_id: Optional[str] = None
    student_name: str
    course_id: int
    course_code: str
    course_title: str
    session_id: Optional[int] = None
    attendance_date: date
    requested_status: str
    reason: str
    supporting_document_url: Optional[str] = None
    status: str
    review_comment: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True

class CourseAttendanceSummary(BaseModel):
    course_id: int
    course_code: str
    course_title: str
    total_sessions: int
    attended_sessions: int
    present_count: int
    late_count: int
    absent_count: int
    excused_count: int
    attendance_rate: float
    policy_threshold: float = 80.0
    status_level: str  # "good", "warning", "critical"
    avg_participation_score: float


# ─── Student Calendar & Task Schemas ──────────────────────────────────────────

class StudentTaskCreate(BaseModel):
    course_id: Optional[int] = None
    title: str
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    priority: str = "medium"  # urgent, high, medium, low
    category: str = "study"   # study, assignment, revision, exam_prep, personal, admin
    estimated_minutes: int = 60
    reminder_at: Optional[datetime] = None

class StudentTaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    category: Optional[str] = None
    estimated_minutes: Optional[int] = None
    reminder_at: Optional[datetime] = None

class StudentTaskStatusPatch(BaseModel):
    status: str  # todo, in_progress, completed, cancelled

class StudentTaskOut(BaseModel):
    id: int
    student_id: int
    course_id: Optional[int] = None
    course_code: Optional[str] = None
    course_title: Optional[str] = None
    title: str
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    priority: str
    status: str
    category: str
    estimated_minutes: int
    completed_at: Optional[datetime] = None
    reminder_at: Optional[datetime] = None
    is_overdue: bool = False
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class StudentTaskMetrics(BaseModel):
    total_tasks: int
    completed_tasks: int
    pending_tasks: int
    overdue_tasks: int
    completion_rate: float
    due_today_count: int
    urgent_priority_count: int

class CalendarEventCreate(BaseModel):
    course_id: Optional[int] = None
    title: str
    description: Optional[str] = None
    event_type: str = "personal"  # academic, exam, assignment_due, lecture, holiday, campus, personal
    start_time: datetime
    end_time: datetime
    all_day: bool = False
    location: Optional[str] = None
    color: str = "#4F46E5"

class CalendarEventUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    event_type: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    all_day: Optional[bool] = None
    location: Optional[str] = None
    color: Optional[str] = None

class CalendarEventOut(BaseModel):
    id: int
    user_id: Optional[int] = None
    course_id: Optional[int] = None
    course_code: Optional[str] = None
    title: str
    description: Optional[str] = None
    event_type: str
    start_time: datetime
    end_time: datetime
    all_day: bool
    location: Optional[str] = None
    color: str
    is_system_generated: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Student Collaboration Spaces Schemas ─────────────────────────────────────

class CollaborationWorkspaceCreate(BaseModel):
    course_id: Optional[int] = None
    name: str
    description: Optional[str] = None
    topic: Optional[str] = None
    visibility: str = "course_public"  # private, course_public, invite_only
    meeting_link: Optional[str] = None

class CollaborationWorkspaceJoinPayload(BaseModel):
    join_code: str

class CollaborationWorkspaceMemberOut(BaseModel):
    id: int
    student_id: int
    student_name: str
    student_reg_id: Optional[str] = None
    role: str
    joined_at: datetime

    class Config:
        from_attributes = True

class CollaborationWorkspaceAssetCreate(BaseModel):
    title: str
    asset_type: str = "note"  # document, link, code_snippet, note
    content: str

class CollaborationWorkspaceAssetOut(BaseModel):
    id: int
    workspace_id: int
    created_by_student_id: Optional[int] = None
    author_name: str
    title: str
    asset_type: str
    content: str
    version: int
    created_at: datetime

    class Config:
        from_attributes = True

class CollaborationWorkspaceMessageCreate(BaseModel):
    content: str
    pinned: bool = False

class CollaborationWorkspaceMessageOut(BaseModel):
    id: int
    workspace_id: int
    sender_student_id: int
    sender_name: str
    content: str
    pinned: bool
    created_at: datetime

    class Config:
        from_attributes = True

class CollaborationWorkspaceWhiteboardUpdate(BaseModel):
    whiteboard_data: Dict[str, Any]

class CollaborationWorkspaceOut(BaseModel):
    id: int
    course_id: Optional[int] = None
    course_code: Optional[str] = None
    name: str
    description: Optional[str] = None
    topic: Optional[str] = None
    visibility: str
    owner_student_id: int
    owner_name: str
    join_code: str
    shared_whiteboard_data: Optional[Dict[str, Any]] = None
    meeting_link: Optional[str] = None
    status: str
    members_count: int
    assets_count: int
    created_at: datetime

    class Config:
        from_attributes = True

class CollaborationWorkspaceDetailOut(CollaborationWorkspaceOut):
    members: List[CollaborationWorkspaceMemberOut]
    assets: List[CollaborationWorkspaceAssetOut]
    recent_messages: List[CollaborationWorkspaceMessageOut]


# ─── Messaging & Communication Schemas ────────────────────────────────────────

class MessageSendPayload(BaseModel):
    content: str
    attachment_url: Optional[str] = None
    attachment_name: Optional[str] = None

class ConversationCreate(BaseModel):
    recipient_id: int
    subject: Optional[str] = None
    thread_type: str = "direct"  # direct, course_inquiry, advising, group
    course_id: Optional[int] = None
    initial_message: str
    attachment_url: Optional[str] = None
    attachment_name: Optional[str] = None

class ConversationParticipantOut(BaseModel):
    id: int
    user_id: int
    name: str
    role: str
    email: str
    last_read_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class DirectMessageOut(BaseModel):
    id: int
    conversation_id: Optional[int] = None
    sender_id: int
    sender_name: str
    sender_role: str
    receiver_id: Optional[int] = None
    content: str
    attachment_url: Optional[str] = None
    attachment_name: Optional[str] = None
    is_read: bool
    read_at: Optional[datetime] = None
    sent_at: datetime

    class Config:
        from_attributes = True

class ConversationListItemOut(BaseModel):
    id: int
    subject: Optional[str] = None
    thread_type: str
    course_id: Optional[int] = None
    course_code: Optional[str] = None
    participants: List[ConversationParticipantOut]
    last_message_at: datetime
    latest_message_snippet: Optional[str] = None
    unread_count: int = 0

class ConversationDetailOut(BaseModel):
    id: int
    subject: Optional[str] = None
    thread_type: str
    course_id: Optional[int] = None
    course_code: Optional[str] = None
    participants: List[ConversationParticipantOut]
    messages: List[DirectMessageOut]

class MessagingContactOut(BaseModel):
    user_id: int
    name: str
    role: str
    email: str
    context: Optional[str] = None







