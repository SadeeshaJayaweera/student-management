"""
NSBM EduSphere — Resource-Level Authorization (Object-Level Access Control)
Protects against Broken Object-Level Authorization (BOLA / IDOR) vulnerabilities
by validating ownership and domain-specific authorization policies on individual resources.
"""
from typing import Any, Optional, Set
from backend.models import User, UserRole, Student, Course, AssignmentSubmission
from backend.core.exceptions import ForbiddenException


class ResourcePolicy:
    """Base policy interface for fine-grained resource authorization"""
    def can_read(self, user: User, resource: Any) -> bool:
        return False

    def can_write(self, user: User, resource: Any) -> bool:
        return False

    def can_delete(self, user: User, resource: Any) -> bool:
        return False


class StudentProfilePolicy(ResourcePolicy):
    """
    Policy governing Student entity access:
    - Students may view and update their personal record.
    - Lecturers, Registrars, Deans, and Admins may view student records.
    - Only Registrars and Admins may modify academic details or delete records.
    """
    STAFF_READ_ROLES: Set[str] = {
        UserRole.ADMIN.value,
        UserRole.DEAN.value,
        UserRole.REGISTRAR.value,
        UserRole.LECTURER.value,
    }
    STAFF_WRITE_ROLES: Set[str] = {
        UserRole.ADMIN.value,
        UserRole.REGISTRAR.value,
    }

    def can_read(self, user: User, student: Student) -> bool:
        role_val = user.role.value if hasattr(user.role, "value") else str(user.role)
        if role_val in self.STAFF_READ_ROLES:
            return True
        return user.id == student.user_id

    def can_write(self, user: User, student: Student) -> bool:
        role_val = user.role.value if hasattr(user.role, "value") else str(user.role)
        if role_val in self.STAFF_WRITE_ROLES:
            return True
        return user.id == student.user_id

    def can_delete(self, user: User, student: Student) -> bool:
        role_val = user.role.value if hasattr(user.role, "value") else str(user.role)
        return role_val in self.STAFF_WRITE_ROLES


class CourseManagementPolicy(ResourcePolicy):
    """
    Policy governing Course management:
    - Anyone authenticated can read published courses.
    - Only the assigned course lecturer, deans, or admins may edit/manage.
    """
    ADMIN_ROLES: Set[str] = {UserRole.ADMIN.value, UserRole.DEAN.value}

    def can_read(self, user: User, course: Course) -> bool:
        return True

    def can_write(self, user: User, course: Course) -> bool:
        role_val = user.role.value if hasattr(user.role, "value") else str(user.role)
        if role_val in self.ADMIN_ROLES:
            return True
        if course.lecturer and course.lecturer.user_id == user.id:
            return True
        return False

    def can_delete(self, user: User, course: Course) -> bool:
        role_val = user.role.value if hasattr(user.role, "value") else str(user.role)
        return role_val in self.ADMIN_ROLES


class SubmissionAuthorizationPolicy(ResourcePolicy):
    """
    Policy governing Assignment Submissions:
    - A student may only read and submit their own work.
    - Course instructors and admins may review and grade submissions.
    """
    ELEVATED_ROLES: Set[str] = {UserRole.ADMIN.value, UserRole.DEAN.value}

    def can_read(self, user: User, submission: AssignmentSubmission, course: Optional[Course] = None) -> bool:
        role_val = user.role.value if hasattr(user.role, "value") else str(user.role)
        if role_val in self.ELEVATED_ROLES:
            return True
        if course and course.lecturer and course.lecturer.user_id == user.id:
            return True
        if hasattr(user, "student") and user.student and user.student.id == submission.student_id:
            return True
        return False

    def can_grade(self, user: User, submission: AssignmentSubmission, course: Optional[Course] = None) -> bool:
        role_val = user.role.value if hasattr(user.role, "value") else str(user.role)
        if role_val in self.ELEVATED_ROLES:
            return True
        if course and course.lecturer and course.lecturer.user_id == user.id:
            return True
        return False


# ── Authorization Assertion Helpers ──────────────────────────────────────────

def assert_can_read(user: User, policy: ResourcePolicy, resource: Any, resource_name: str = "resource") -> None:
    if not policy.can_read(user, resource):
        raise ForbiddenException(f"Access denied: You do not have permission to view this {resource_name}.")


def assert_can_write(user: User, policy: ResourcePolicy, resource: Any, resource_name: str = "resource") -> None:
    if not policy.can_write(user, resource):
        raise ForbiddenException(f"Access denied: You do not have permission to modify this {resource_name}.")


def assert_can_delete(user: User, policy: ResourcePolicy, resource: Any, resource_name: str = "resource") -> None:
    if not policy.can_delete(user, resource):
        raise ForbiddenException(f"Access denied: You do not have permission to delete this {resource_name}.")
