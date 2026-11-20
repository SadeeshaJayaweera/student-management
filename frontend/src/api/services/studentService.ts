import api from '@/api/client'
import type {
  StudentDashboard,
  GradeRecord,
  CourseEnrollment,
  AssignmentItem,
  AttendanceRecord,
} from '@/types'

export const studentService = {
  async getDashboard(): Promise<StudentDashboard> {
    const { data } = await api.get<StudentDashboard>('/students/dashboard')
    return data
  },

  async getGrades(): Promise<GradeRecord[]> {
    const { data } = await api.get<GradeRecord[]>('/students/grades')
    return data
  },

  async getCourses(): Promise<CourseEnrollment[]> {
    const { data } = await api.get<CourseEnrollment[]>('/students/courses')
    return data
  },

  async getAssignments(): Promise<AssignmentItem[]> {
    const { data } = await api.get<AssignmentItem[]>('/students/assignments')
    return data
  },

  async submitAssignment(assignmentId: number, textContent: string): Promise<any> {
    const { data } = await api.post(`/students/assignments/${assignmentId}/submit`, {
      assignment_id: assignmentId,
      text_content: textContent,
    })
    return data
  },

  async getAttendance(): Promise<AttendanceRecord[]> {
    const { data } = await api.get<AttendanceRecord[]>('/students/attendance')
    return data
  },
}
