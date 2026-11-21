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

export interface CourseProgressSummary {
  course_id: number;
  course_code: string;
  course_title: string;
  faculty: string;
  department: string;
  lecturer_name: string;
  delivery_method: string;
  completed_lessons: number;
  total_lessons: number;
  progress_percentage: number;
  current_grade_percentage?: number | null;
  letter_grade?: string | null;
  attendance_rate: number;
}

export interface UpcomingDeadlineItem {
  id: number;
  item_type: 'assignment' | 'quiz';
  title: string;
  course_id: number;
  course_code: string;
  course_title: string;
  due_date: string;
  days_remaining: number;
  is_overdue: boolean;
  max_marks: number;
  submission_status: string;
}

export interface UpcomingClassSession {
  session_id: number;
  course_id: number;
  course_code: string;
  course_title: string;
  title: string;
  start_time: string;
  duration_minutes: number;
  session_type: string;
  join_url?: string | null;
  is_live: boolean;
}

export interface DashboardAnnouncementItem {
  id: number;
  course_id: number;
  course_code: string;
  course_title: string;
  title: string;
  content: string;
  is_pinned: boolean;
  author_name: string;
  published_at: string;
}

export interface PersonalizedRecommendation {
  id: string;
  category: 'urgent_deadline' | 'learning_progress' | 'academic_alert' | 'study_resource';
  priority: 'high' | 'medium' | 'low';
  title: string;
  description: string;
  action_label: string;
  action_link: string;
}

export interface PersonalizedStudentDashboard {
  student_id: string;
  full_name: string;
  email: string;
  faculty: string;
  department: string;
  program: string;
  year_of_study: number;
  semester: number;
  gpa: number;
  credits_earned: number;
  overall_attendance_rate: number;
  enrolled_courses_count: number;
  pending_tasks_count: number;
  unread_notifications_count: number;
  courses_progress: CourseProgressSummary[];
  upcoming_deadlines: UpcomingDeadlineItem[];
  upcoming_classes: UpcomingClassSession[];
  recent_announcements: DashboardAnnouncementItem[];
  recommendations: PersonalizedRecommendation[];
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

export interface AttendanceSession {
  id: number;
  course_id: number;
  course_code?: string | null;
  course_title?: string | null;
  session_title: string;
  session_date: string;
  start_time: string;
  end_time: string;
  checkin_code?: string | null;
  code_expires_at?: string | null;
  status: string;
  allow_self_checkin: boolean;
  attendances_count: number;
  created_at: string;
}

export interface AttendanceCorrectionRequest {
  id: number;
  student_id: number;
  student_reg_id?: string | null;
  student_name: string;
  course_id: number;
  course_code: string;
  course_title: string;
  session_id?: number | null;
  attendance_date: string;
  requested_status: string;
  reason: string;
  supporting_document_url?: string | null;
  status: 'pending' | 'approved' | 'rejected';
  review_comment?: string | null;
  reviewed_at?: string | null;
  created_at: string;
}

export interface CourseAttendanceSummary {
  course_id: number;
  course_code: string;
  course_title: string;
  total_sessions: number;
  attended_sessions: number;
  present_count: number;
  late_count: number;
  absent_count: number;
  excused_count: number;
  attendance_rate: number;
  policy_threshold: number;
  status_level: 'good' | 'warning' | 'critical';
  avg_participation_score: number;
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

// ── Timetable ──────────────────────────────────────────────────

export interface TimetableSlot {
  id: number;
  course_id: number | null;
  lecturer_id: number | null;
  day_of_week: number;
  start_time: string;
  end_time: string;
  title: string;
  slot_type: string;
  room: string;
  building: string | null;
  recurrence_pattern: string;
  is_active: boolean;
  color: string;
  notes: string | null;
  course_code?: string | null;
  course_title?: string | null;
  lecturer_name?: string | null;
  created_at: string;
  updated_at?: string | null;
}

export interface TimetableDay {
  day_of_week: number;
  day_name: string;
  slots: TimetableSlot[];
}

export interface TimetableConflict {
  conflict_type: string;
  slot_id?: number | null;
  title: string;
  day_of_week: number;
  start_time: string;
  end_time: string;
  room: string;
  description: string;
}

export interface StudentTimetableData {
  student_id: string;
  student_name: string;
  schedule: TimetableDay[];
  total_slots: number;
  conflicts_detected: TimetableConflict[];
}

// ── Student Tasks & Calendar ──────────────────────────────────

export interface StudentTask {
  id: number;
  student_id: number;
  course_id?: number | null;
  course_code?: string | null;
  course_title?: string | null;
  title: string;
  description?: string | null;
  due_date?: string | null;
  priority: 'urgent' | 'high' | 'medium' | 'low' | string;
  status: 'todo' | 'in_progress' | 'completed' | 'cancelled' | string;
  category: 'study' | 'assignment' | 'revision' | 'exam_prep' | 'personal' | 'admin' | string;
  estimated_minutes: number;
  completed_at?: string | null;
  reminder_at?: string | null;
  is_overdue: boolean;
  created_at: string;
  updated_at?: string | null;
}

export interface StudentTaskMetrics {
  total_tasks: number;
  completed_tasks: number;
  pending_tasks: number;
  overdue_tasks: number;
  completion_rate: number;
  due_today_count: number;
  urgent_priority_count: number;
}

export interface CalendarEvent {
  id: number;
  user_id?: number | null;
  course_id?: number | null;
  course_code?: string | null;
  title: string;
  description?: string | null;
  event_type: 'academic' | 'exam' | 'assignment_due' | 'lecture' | 'holiday' | 'campus' | 'personal' | string;
  start_time: string;
  end_time: string;
  all_day: boolean;
  location?: string | null;
  color: string;
  is_system_generated: boolean;
  created_at: string;
}

// ── Student Collaboration Spaces ──────────────────────────────

export interface CollaborationMember {
  id: number;
  student_id: number;
  student_name: string;
  student_reg_id?: string | null;
  role: string;
  joined_at: string;
}

export interface CollaborationAsset {
  id: number;
  workspace_id: number;
  created_by_student_id?: number | null;
  author_name: string;
  title: string;
  asset_type: string;
  content: string;
  version: number;
  created_at: string;
}

export interface CollaborationMessage {
  id: number;
  workspace_id: number;
  sender_student_id: number;
  sender_name: string;
  content: string;
  pinned: boolean;
  created_at: string;
}

export interface CollaborationWorkspace {
  id: number;
  course_id?: number | null;
  course_code?: string | null;
  name: string;
  description?: string | null;
  topic?: string | null;
  visibility: string;
  owner_student_id: number;
  owner_name: string;
  join_code: string;
  shared_whiteboard_data?: Record<string, any> | null;
  meeting_link?: string | null;
  status: string;
  members_count: number;
  assets_count: number;
  created_at: string;
}

export interface CollaborationWorkspaceDetail extends CollaborationWorkspace {
  members: CollaborationMember[];
  assets: CollaborationAsset[];
  recent_messages: CollaborationMessage[];
}

// ── Messaging & Direct Communication ──────────────────────────

export interface ConversationParticipant {
  id: number;
  user_id: number;
  name: string;
  role: string;
  email: string;
  last_read_at?: string | null;
}

export interface DirectMessage {
  id: number;
  conversation_id?: number | null;
  sender_id: number;
  sender_name: string;
  sender_role: string;
  receiver_id?: number | null;
  content: string;
  attachment_url?: string | null;
  attachment_name?: string | null;
  is_read: boolean;
  read_at?: string | null;
  sent_at: string;
}

export interface ConversationItem {
  id: number;
  subject?: string | null;
  thread_type: string;
  course_id?: number | null;
  course_code?: string | null;
  participants: ConversationParticipant[];
  last_message_at: string;
  latest_message_snippet?: string | null;
  unread_count: number;
}

export interface ConversationDetail {
  id: number;
  subject?: string | null;
  thread_type: string;
  course_id?: number | null;
  course_code?: string | null;
  participants: ConversationParticipant[];
  messages: DirectMessage[];
}

export interface MessagingContact {
  user_id: number;
  name: string;
  role: string;
  email: string;
  context?: string | null;
}




