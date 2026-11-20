"""
NSBM EduSphere — Student Service & Repository Unit Tests
Verifies student data access, course enrollments, and grade querying
"""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import Student, Course, Enrollment, Grade
from backend.repositories.student_repository import StudentRepository


@pytest.mark.asyncio
async def test_student_repository_operations(test_session: AsyncSession, seeded_user):
    """Verify StudentRepository creates, retrieves, and counts student relations"""
    repo = StudentRepository(test_session)

    # Create Student profile linked to seeded_user
    student = Student(
        user_id=seeded_user.id,
        student_id="STU9999",
        faculty="Faculty of Computing",
        department="Computer Science",
        program="BSc Computer Science",
        year_of_study=2,
        semester=1,
        gpa=3.85,
        credits_earned=45,
    )
    test_session.add(student)
    await test_session.commit()
    await test_session.refresh(student)

    # Test get_by_user_id
    retrieved = await repo.get_by_user_id(seeded_user.id)
    assert retrieved is not None
    assert retrieved.student_id == "STU9999"
    assert retrieved.user.email == seeded_user.email

    # Test get_by_student_id
    by_student_id = await repo.get_by_student_id("STU9999")
    assert by_student_id is not None
    assert by_student_id.id == student.id

    # Create a Course and active Enrollment
    course = Course(
        course_code="CS201",
        title="Data Structures & Algorithms",
        credits=4,
        faculty="Faculty of Computing",
        department="Computer Science",
        semester=1,
        year=2,
    )
    test_session.add(course)
    await test_session.commit()
    await test_session.refresh(course)

    enrollment = Enrollment(student_id=student.id, course_id=course.id, status="active")
    test_session.add(enrollment)
    await test_session.commit()

    # Test active enrollment count
    count = await repo.count_active_enrollments(student.id)
    assert count == 1

    # Add a Grade and verify grade retrieval
    grade = Grade(
        student_id=student.id,
        course_id=course.id,
        total=88.5,
        letter_grade="A",
        grade_points=4.0,
    )
    test_session.add(grade)
    await test_session.commit()

    grades = await repo.get_student_grades(student.id)
    assert len(grades) == 1
    assert grades[0].letter_grade == "A"
    assert grades[0].course.course_code == "CS201"
