// ── Core Types ───────────────────────────────────────────────

export interface User {
  id: number;
  email: string;
  username: string;
  full_name: string;
  role: 'admin' | 'student' | 'lecturer' | 'alumni' | 'librarian';
  avatar_url?: string;
  phone?: string;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  role: string;
  user_id: number;
  full_name: string;
}

// ── Student ───────────────────────────────────────────────────

export interface StudentDashboard {
  student_id: string;
  full_name: string;
  faculty: string;
  department: string;
  program: string;
  year_of_study: number;
  semester: number;
  gpa: number;
  credits_earned: number;
  enrolled_courses: number;
  pending_assignments: number;
  unread_notifications: number;
  borrowed_books: number;
  attendance_rate: number;
  recent_grades: GradeSummary[];
  upcoming_events: EventSummary[];
}

export interface GradeSummary {
  course: string;
  course_code: string;
  total: number;
  letter: string;
  grade_points: number;
}

export interface GradeRecord {
  id: number;
  course_code: string;
  course_title: string;
  credits: number;
  midterm: number | null;
  final: number | null;
  assignments_avg: number | null;
  total: number | null;
  letter_grade: string | null;
  grade_points: number | null;
  remarks: string | null;
}

export interface AttendanceRecord {
  id: number;
  course: string;
  course_code: string;
  date: string;
  status: 'present' | 'absent' | 'late' | 'excused';
}

export interface CourseEnrollment {
  id: number;
  course_code: string;
  title: string;
  description: string;
  credits: number;
  semester: number;
  year: number;
  schedule: { day: string; time: string; room: string } | null;
  lecturer: string | null;
  enrollment_status: string;
  enrolled_count?: number;
  max_students?: number;
}

export interface AssignmentItem {
  id: number;
  title: string;
  description: string;
  course: string;
  course_code: string;
  due_date: string;
  max_marks: number;
  type: string;
  is_submitted: boolean;
  is_overdue: boolean;
  submission: {
    marks: number | null;
    feedback: string | null;
    submitted_at: string;
  } | null;
}

// ── Lecturer ──────────────────────────────────────────────────

export interface LecturerDashboard {
  lecturer_id: string;
  full_name: string;
  faculty: string;
  department: string;
  specialization: string;
  office_location: string;
  office_hours: Record<string, string>;
  total_courses: number;
  total_students: number;
  pending_submissions: number;
  recent_submissions: RecentSubmission[];
}

export interface RecentSubmission {
  student: string;
  assignment: string;
  course: string;
  submitted_at: string;
  graded: boolean;
}

// ── Alumni ────────────────────────────────────────────────────

export interface AlumniMember {
  id: number;
  alumni_id: string;
  full_name: string;
  graduation_year: number;
  degree: string;
  current_position: string;
  current_company: string;
  industry: string;
  location: string;
  willing_to_mentor: boolean;
  linkedin_url: string;
}

export interface AlumniExperience {
  id: number;
  title: string;
  content: string;
  category: string;
  tags: string[];
  likes: number;
  author: string;
  graduation_year: number;
  company: string;
  created_at: string;
}

// ── Library ───────────────────────────────────────────────────

export interface Book {
  id: number;
  isbn: string;
  title: string;
  author: string;
  publisher: string;
  year: number;
  category: string;
  subject: string;
  description: string;
  cover_url: string | null;
  total_copies: number;
  available_copies: number;
  status: 'available' | 'borrowed' | 'reserved' | 'maintenance';
  is_ebook: boolean;
  location: string;
}

export interface BorrowRecord {
  id: number;
  book: string;
  author: string;
  isbn: string;
  borrowed_at: string;
  due_date: string;
  returned_at: string | null;
  status: 'active' | 'returned' | 'overdue';
  fine: number;
  days_remaining: number;
}

// ── Sports ────────────────────────────────────────────────────

export interface Club {
  id: number;
  name: string;
  description: string;
  category: string;
  logo_url: string | null;
  cover_url: string | null;
  president_name: string;
  achievements: string;
  meeting_schedule: Record<string, string> | null;
  member_count: number;
  max_members: number;
}

export interface ClubEvent {
  id: number;
  title: string;
  description: string;
  club: string;
  club_category: string;
  event_date: string;
  location: string;
  max_participants: number | null;
  registration_required: boolean;
  image_url: string | null;
}

// ── News ──────────────────────────────────────────────────────

export interface NewsArticle {
  id: number;
  title: string;
  slug: string;
  summary: string;
  content?: string;
  category: string;
  author: string;
  cover_image_url: string | null;
  tags: string[];
  views: number;
  is_featured: boolean;
  published_at: string;
  comments?: NewsComment[];
}

export interface NewsComment {
  id: number;
  user: { full_name: string };
  content: string;
  created_at: string;
}

// ── Admin ─────────────────────────────────────────────────────

export interface AdminDashboard {
  total_students: number;
  total_lecturers: number;
  total_alumni: number;
  total_courses: number;
  total_books: number;
  total_clubs: number;
  total_news: number;
  active_borrows: number;
  recent_registrations: UserRow[];
}

export interface UserRow {
  id: number;
  full_name: string;
  email: string;
  username: string;
  role: string;
  is_active: boolean;
  created_at: string;
}

// ── Notifications ─────────────────────────────────────────────

export interface Notification {
  id: number;
  title: string;
  message: string;
  notification_type: 'info' | 'success' | 'warning' | 'error';
  link: string | null;
  is_read: boolean;
  created_at: string;
}

// ── AI ────────────────────────────────────────────────────────

export interface AIMessage {
  role: 'user' | 'ai';
  content: string;
  timestamp: Date;
}

// ── Pagination ────────────────────────────────────────────────

export interface Paginated<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

// ── Misc ──────────────────────────────────────────────────────

export interface EventSummary {
  title: string;
  date: string;
  location: string;
}
