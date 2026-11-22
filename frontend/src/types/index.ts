// ── Core Types ───────────────────────────────────────────────

export interface User {
  id: number;
  email: string;
  username: string;
  full_name: string;
  role: 'admin' | 'student' | 'lecturer' | 'alumni' | 'librarian' | 'accountant';
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

// ── Notification Center ───────────────────────────────────────

export interface NotificationItem {
  id: number;
  user_id: number;
  title: string;
  message: string;
  notification_type: 'info' | 'warning' | 'success' | 'error';
  category: 'general' | 'academic' | 'deadline' | 'announcement' | 'system' | 'finance' | 'social';
  priority: 'urgent' | 'high' | 'normal' | 'low';
  link?: string | null;
  is_read: boolean;
  read_at?: string | null;
  expires_at?: string | null;
  extra_data?: Record<string, any> | null;
  created_at: string;
}

export interface NotificationPreferences {
  user_id: number;
  email_enabled: boolean;
  in_app_enabled: boolean;
  push_enabled: boolean;
  sms_enabled: boolean;
  notify_academic: boolean;
  notify_deadlines: boolean;
  notify_announcements: boolean;
  notify_messages: boolean;
  notify_grades: boolean;
  quiet_hours_enabled: boolean;
  quiet_hours_start?: string | null;
  quiet_hours_end?: string | null;
  updated_at: string;
}

export interface NotificationStats {
  total_unread: number;
  total_count: number;
  unread_by_category: Record<string, number>;
  unread_by_priority: Record<string, number>;
}

// ── Course Evaluation & Student Feedback ──────────────────────

export interface SurveyQuestion {
  id: number;
  survey_id: number;
  question_text: string;
  question_type: string;
  category: string;
  is_required: boolean;
  options_json?: any;
  display_order: number;
}

export interface CourseEvaluationSurveyItem {
  id: number;
  institution_id?: number | null;
  course_id: number;
  course_code?: string | null;
  course_title?: string | null;
  title: string;
  description?: string | null;
  start_date: string;
  end_date: string;
  is_published: boolean;
  is_anonymous: boolean;
  created_at: string;
  questions_count: number;
  responses_count: number;
  has_submitted?: boolean;
}

export interface CourseEvaluationSurveyDetail extends CourseEvaluationSurveyItem {
  questions: SurveyQuestion[];
}

export interface QuestionAnalytics {
  question_id: number;
  question_text: string;
  category: string;
  question_type: string;
  average_rating?: number | null;
  response_count: number;
  rating_distribution: Record<string, number>;
  text_feedback: string[];
}

export interface SurveyAnalytics {
  survey_id: number;
  title: string;
  course_code: string;
  course_title: string;
  total_responses: number;
  category_averages: Record<string, number>;
  overall_average?: number | null;
  question_analytics: QuestionAnalytics[];
}

// ── Student Wellbeing & Support ───────────────────────────────

export interface WellbeingAppointmentItem {
  id: number;
  request_id: number;
  counselor_id?: number | null;
  counselor_name?: string | null;
  student_id: number;
  student_name?: string | null;
  appointment_type: 'virtual' | 'in_person';
  scheduled_at: string;
  duration_minutes: number;
  location_or_link?: string | null;
  status: 'scheduled' | 'completed' | 'cancelled' | 'rescheduled';
  meeting_notes?: string | null;
  created_at: string;
}

export interface WellbeingSupportRequestItem {
  id: number;
  institution_id?: number | null;
  student_id: number;
  student_name?: string | null;
  student_number?: string | null;
  request_type: 'academic_stress' | 'mental_health' | 'counseling' | 'accessibility_accommodation' | 'financial_emergency' | 'peer_support';
  subject: string;
  description: string;
  urgency: 'low' | 'normal' | 'high' | 'crisis';
  status: 'submitted' | 'assigned' | 'in_progress' | 'scheduled' | 'resolved' | 'closed';
  assigned_counselor_id?: number | null;
  assigned_counselor_name?: string | null;
  is_confidential: boolean;
  resolution_notes?: string | null;
  created_at: string;
  updated_at: string;
  appointments: WellbeingAppointmentItem[];
}

export interface WellbeingResourceItem {
  id: number;
  institution_id?: number | null;
  title: string;
  category: 'mental_health' | 'stress_management' | 'mindfulness' | 'crisis_hotline' | 'study_habits' | 'accessibility';
  description: string;
  content_url?: string | null;
  emergency_phone?: string | null;
  is_crisis_resource: boolean;
  is_featured: boolean;
  created_at: string;
}

// ── Student Billing & Fee Management ──────────────────────────

export interface InvoiceItem {
  id: number;
  invoice_id: number;
  component_name: string;
  amount: number;
}

export interface InvoiceInstallment {
  id: number;
  invoice_id: number;
  installment_number: number;
  amount: number;
  due_date: string;
  status: 'pending' | 'paid' | 'overdue';
  paid_at?: string | null;
}

export interface StudentInvoice {
  id: number;
  invoice_number: string;
  institution_id?: number | null;
  student_id: number;
  student_name?: string | null;
  student_number?: string | null;
  fee_structure_id?: number | null;
  academic_term: string;
  total_amount: number;
  discount_amount: number;
  paid_amount: number;
  balance_due: number;
  currency: string;
  issue_date: string;
  due_date: string;
  status: 'unpaid' | 'partially_paid' | 'paid' | 'overdue' | 'cancelled';
  payment_plan_type: 'full' | 'installment_2' | 'installment_3';
  notes?: string | null;
  created_at: string;
  items: InvoiceItem[];
  installments: InvoiceInstallment[];
}

export interface FeeComponent {
  id: number;
  fee_structure_id: number;
  name: string;
  amount: number;
  is_optional: boolean;
  description?: string | null;
}

export interface FeeStructure {
  id: number;
  institution_id?: number | null;
  program_id?: number | null;
  name: string;
  term_type: string;
  total_amount: number;
  currency: string;
  is_active: boolean;
  created_at: string;
  components: FeeComponent[];
}

export interface BillingSummary {
  total_invoiced: number;
  total_collected: number;
  total_outstanding: number;
  total_overdue: number;
  invoices_count: number;
  paid_invoices_count: number;
  overdue_invoices_count: number;
  currency: string;
}

// ── Payment Gateway & Financial Auditing ─────────────────────────────

export interface PaymentReceipt {
  id: number;
  transaction_id: number;
  invoice_id: number;
  receipt_number: string;
  receipt_url?: string | null;
  amount_paid: number;
  currency: string;
  payment_method: string;
  issued_at: string;
  generated_by: string;
}

export interface PaymentTransaction {
  id: number;
  invoice_id: number;
  installment_id?: number | null;
  student_id: number;
  transaction_ref: string;
  gateway: string;
  gateway_reference?: string | null;
  amount: number;
  currency: string;
  status: 'pending' | 'completed' | 'failed' | 'refunded';
  payment_method: string;
  created_at: string;
  receipt?: PaymentReceipt | null;
}

export interface PaymentCheckoutResponse {
  transaction_id: number;
  transaction_ref: string;
  amount: number;
  currency: string;
  status: string;
  gateway: string;
  checkout_url: string;
  checkout_params: Record<string, any>;
}

export interface FinancialAuditLog {
  id: number;
  transaction_id?: number | null;
  invoice_id?: number | null;
  actor_user_id?: number | null;
  actor_name?: string | null;
  action: string;
  old_status?: string | null;
  new_status?: string | null;
  amount?: number | null;
  ip_address?: string | null;
  details?: Record<string, any> | null;
  created_at: string;
}

// ── Modern Digital Library System ────────────────────────────────────

export interface DigitalLibraryResource {
  id: number;
  title: string;
  author: string;
  resource_type: string;
  doi_or_issn?: string | null;
  subject_category: string;
  file_format: string;
  file_url: string;
  cover_url?: string | null;
  file_size_bytes: number;
  download_count: number;
  view_count: number;
  abstract?: string | null;
  keywords?: string | null;
  is_open_access: boolean;
  published_year?: number | null;
  publisher?: string | null;
  collection_id?: number | null;
  book_id?: number | null;
  is_bookmarked?: boolean;
  created_at: string;
  updated_at?: string | null;
}

export interface LibrarySubjectCollection {
  id: number;
  title: string;
  slug: string;
  description?: string | null;
  icon: string;
  is_featured: boolean;
  resource_count?: number;
  created_at: string;
}

export interface LibraryBookmark {
  id: number;
  user_id: number;
  resource_id: number;
  resource: DigitalLibraryResource;
  notes?: string | null;
  created_at: string;
}

export interface DigitalLibraryStats {
  total_resources: number;
  total_views: number;
  total_downloads: number;
  resource_type_breakdown: Record<string, number>;
  subject_breakdown: Record<string, number>;
}

// ── Circulation and Borrowing Workflows ──────────────────────────────

export interface CirculationLoan {
  id: number;
  book_id: number;
  book_title: string;
  book_author: string;
  student_id: number;
  student_name?: string | null;
  borrowed_at: string;
  due_date: string;
  returned_at?: string | null;
  renewals_count: number;
  renewed_at?: string | null;
  status: string;
  fine_amount: number;
  fine_paid: boolean;
  notes?: string | null;
}

export interface CirculationReservation {
  id: number;
  book_id: number;
  book_title: string;
  student_id: number;
  student_name?: string | null;
  priority_number: number;
  reserved_at: string;
  expires_at: string;
  notified_at?: string | null;
  status: string;
}

export interface LibraryFineRecord {
  id: number;
  borrow_id: number;
  student_id: number;
  student_name?: string | null;
  book_title?: string | null;
  amount: number;
  overdue_days: number;
  status: string;
  waived_by_name?: string | null;
  waiver_reason?: string | null;
  paid_at?: string | null;
  created_at: string;
}

export interface CirculationStats {
  active_loans_count: number;
  overdue_loans_count: number;
  active_reservations_count: number;
  unpaid_fines_total: number;
  collected_fines_total: number;
}

// ── Sports and Athletic Management ───────────────────────────────────

export interface AthleteProfile {
  id: number;
  student_id: number;
  student_name?: string | null;
  student_reg_number?: string | null;
  team_id: number;
  jersey_number?: number | null;
  position_or_role: string;
  fitness_status: string;
  matches_played: number;
  points_or_goals: number;
  mvp_awards: number;
  joined_date?: string | null;
  created_at: string;
}

export interface SportsFixture {
  id: number;
  team_id: number;
  team_name?: string | null;
  sport_type?: string | null;
  tournament_name: string;
  opponent_name: string;
  scheduled_time: string;
  venue: string;
  fixture_type: string;
  status: string;
  our_score?: string | null;
  opponent_score?: string | null;
  match_result?: string | null;
  highlights?: string | null;
  created_at: string;
}

export interface AthleticTeam {
  id: number;
  name: string;
  sport_type: string;
  coach_name?: string | null;
  captain_name?: string | null;
  division: string;
  home_venue?: string | null;
  logo_url?: string | null;
  is_active: boolean;
  roster: AthleteProfile[];
  fixtures: SportsFixture[];
  created_at: string;
}

export interface SportsFacilityBooking {
  id: number;
  facility_name: string;
  booked_by_user_id: number;
  booked_by_name?: string | null;
  team_id?: number | null;
  team_name?: string | null;
  start_time: string;
  end_time: string;
  purpose: string;
  status: string;
  created_at: string;
}

export interface AthleticStats {
  total_teams: number;
  total_athletes: number;
  upcoming_fixtures_count: number;
  matches_won: number;
  matches_lost: number;
  facilities_booked_count: number;
}

// ── Campus News and Media Publication ────────────────────────────────

export interface MediaGalleryItem {
  id: number;
  news_id: number;
  title: string;
  media_type: string;
  media_url: string;
  caption?: string | null;
  sort_order: number;
  created_at: string;
}

export interface NewsComment {
  id: number;
  news_id?: number;
  user_id?: number;
  user?: { full_name: string };
  user_name?: string | null;
  content: string;
  created_at: string;
}

export interface NewsArticle {
  id: number;
  title: string;
  slug: string;
  content: string;
  summary?: string | null;
  category: string;
  author?: string;
  author_id?: number;
  author_name?: string | null;
  cover_image_url?: string | null;
  tags?: string[] | null;
  views: number;
  likes_count?: number;
  is_published?: boolean;
  is_featured?: boolean;
  status?: string;
  target_audience?: string;
  editorial_notes?: string | null;
  published_at?: string | null;
  created_at?: string;
  updated_at?: string | null;
  gallery?: MediaGalleryItem[];
  comments?: NewsComment[];
  user_has_liked?: boolean;
}

export interface NewsPublicationStats {
  total_articles: number;
  total_views: number;
  total_likes: number;
  category_breakdown: Record<string, number>;
}

// ── Hostel & Accommodation ──────────────────────────────────

export interface HostelRoom {
  id: number;
  building_id: number;
  building_name?: string | null;
  room_number: string;
  floor: number;
  room_type: string;
  capacity: number;
  occupied_count: number;
  monthly_fee: number;
  status: string;
  created_at: string;
}

export interface HostelBuilding {
  id: number;
  name: string;
  code: string;
  gender_type: string;
  total_floors: number;
  warden_name: string;
  warden_contact: string;
  campus_location: string;
  amenities?: string[] | null;
  is_active: boolean;
  total_rooms: number;
  total_capacity: number;
  occupied_beds: number;
  available_beds: number;
  created_at: string;
  rooms?: HostelRoom[];
}

export interface HostelAllocation {
  id: number;
  student_id: number;
  student_name?: string | null;
  student_reg_number?: string | null;
  room_id: number;
  room_number?: string | null;
  building_name?: string | null;
  academic_year: string;
  semester: number;
  check_in_date: string;
  check_out_date?: string | null;
  status: string;
  deposit_paid: number;
  emergency_contact?: string | null;
  notes?: string | null;
  created_at: string;
}

export interface HostelMaintenanceRequest {
  id: number;
  room_id: number;
  room_number?: string | null;
  building_name?: string | null;
  student_id: number;
  student_name?: string | null;
  issue_type: string;
  description: string;
  priority: string;
  status: string;
  resolution_notes?: string | null;
  reported_at: string;
  resolved_at?: string | null;
}

export interface HostelOccupancySummary {
  total_buildings: number;
  total_rooms: number;
  total_capacity: number;
  occupied_beds: number;
  available_beds: number;
  occupancy_rate: number;
  active_maintenance_issues: number;
}

// ── Transport & Shuttle ─────────────────────────────────────

export interface TransportVehicle {
  id: number;
  vehicle_number: string;
  vehicle_type: string;
  capacity: number;
  driver_name: string;
  driver_contact: string;
  status: string;
  current_lat?: number | null;
  current_lng?: number | null;
  last_telemetry_at?: string | null;
  created_at: string;
}

export interface ShuttleStop {
  id: number;
  route_id: number;
  stop_name: string;
  stop_order: number;
  latitude?: number | null;
  longitude?: number | null;
  estimated_time_offset_mins: number;
}

export interface ShuttleSchedule {
  id: number;
  route_id: number;
  route_name?: string | null;
  route_code?: string | null;
  vehicle_id?: number | null;
  vehicle_number?: string | null;
  departure_time: string;
  arrival_time: string;
  days_of_week?: string[] | null;
  shift_type: string;
  is_active: boolean;
  created_at: string;
}

export interface ShuttleRoute {
  id: number;
  route_name: string;
  route_code: string;
  origin: string;
  destination: string;
  distance_km: number;
  estimated_duration_mins: number;
  fare_amount: number;
  is_active: boolean;
  created_at: string;
  stops?: ShuttleStop[];
  schedules?: ShuttleSchedule[];
}

export interface StudentTransportPass {
  id: number;
  student_id: number;
  student_name?: string | null;
  student_reg_number?: string | null;
  route_id: number;
  route_name?: string | null;
  route_code?: string | null;
  pass_type: string;
  valid_from: string;
  valid_until: string;
  qr_code_token: string;
  fare_paid: number;
  status: string;
  created_at: string;
}

export interface TransportFleetSummary {
  total_vehicles: number;
  active_vehicles: number;
  maintenance_vehicles: number;
  total_routes: number;
  active_schedules: number;
  active_passes: number;
  fleet_capacity: number;
}















