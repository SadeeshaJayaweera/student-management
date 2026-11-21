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
    faculty: str
    department: str
    program: str
    year_of_study: int = 1
    semester: int = 1

class StudentUpdate(BaseModel):
    address: Optional[str] = None
    emergency_contact: Optional[str] = None
    year_of_study: Optional[int] = None
    semester: Optional[int] = None

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
    user: UserOut
    class Config:
        from_attributes = True


# ─── Lecturer Schemas ─────────────────────────────────────────────────────────

class LecturerOut(BaseModel):
    id: int
    lecturer_id: str
    faculty: str
    department: str
    specialization: Optional[str] = None
    qualification: Optional[str] = None
    office_location: Optional[str] = None
    bio: Optional[str] = None
    research_interests: Optional[str] = None
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
    course_code: str
    title: str
    description: Optional[str] = None
    credits: int = 3
    faculty: str
    department: str
    semester: int
    year: int
    max_students: int = 60
    lecturer_id: Optional[int] = None
    schedule: Optional[Dict[str, Any]] = None

class CourseOut(BaseModel):
    id: int
    course_code: str
    title: str
    description: Optional[str] = None
    credits: int
    faculty: str
    department: str
    semester: int
    year: int
    max_students: int
    is_active: bool
    lecturer: Optional[LecturerOut] = None
    class Config:
        from_attributes = True

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
