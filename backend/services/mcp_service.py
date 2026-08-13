"""
NSBM EduSphere — MCP (Model Context Protocol) Server
Exposes university data as MCP tools
"""
from typing import Any, Optional
from backend.config import settings


class EduSphereMCPServer:
    """
    MCP Server for NSBM EduSphere
    Exposes university tools for AI agents to use
    """

    def __init__(self):
        self.tools = {
            "get_student_grades": self.get_student_grades,
            "search_library": self.search_library,
            "get_course_schedule": self.get_course_schedule,
            "get_club_events": self.get_club_events,
            "get_news": self.get_news,
            "calculate_gpa": self.calculate_gpa,
            "get_exam_schedule": self.get_exam_schedule,
        }

    def get_tool_definitions(self) -> list:
        """Return MCP-compatible tool definitions"""
        return [
            {
                "name": "get_student_grades",
                "description": "Retrieve grade information for a student",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "student_id": {"type": "string", "description": "The student ID"},
                        "semester": {"type": "integer", "description": "Semester number (optional)"}
                    },
                    "required": ["student_id"]
                }
            },
            {
                "name": "search_library",
                "description": "Search the NSBM library catalog for books",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query (title, author, ISBN)"},
                        "category": {"type": "string", "description": "Book category filter (optional)"}
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "get_course_schedule",
                "description": "Get the timetable/schedule for courses",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "faculty": {"type": "string", "description": "Faculty name"},
                        "semester": {"type": "integer", "description": "Semester number"}
                    }
                }
            },
            {
                "name": "get_club_events",
                "description": "Get upcoming club and sports events",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "club_name": {"type": "string", "description": "Specific club name (optional)"},
                        "days_ahead": {"type": "integer", "description": "Number of days to look ahead"}
                    }
                }
            },
            {
                "name": "calculate_gpa",
                "description": "Calculate GPA from grades",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "grades": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "letter_grade": {"type": "string"},
                                    "credits": {"type": "integer"}
                                }
                            },
                            "description": "Array of grade objects with letter_grade and credits"
                        }
                    },
                    "required": ["grades"]
                }
            },
            {
                "name": "get_news",
                "description": "Get latest university news and announcements",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "category": {"type": "string", "description": "News category (academic, sports, events, alumni)"},
                        "limit": {"type": "integer", "description": "Number of articles to return"}
                    }
                }
            },
            {
                "name": "get_exam_schedule",
                "description": "Get exam schedule information",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "semester": {"type": "integer", "description": "Semester number"},
                        "faculty": {"type": "string", "description": "Faculty name (optional)"}
                    }
                }
            }
        ]

    async def execute_tool(self, tool_name: str, arguments: dict) -> Any:
        """Execute an MCP tool by name"""
        if tool_name not in self.tools:
            return {"error": f"Unknown tool: {tool_name}"}
        try:
            return await self.tools[tool_name](**arguments)
        except Exception as e:
            return {"error": str(e)}

    async def get_student_grades(self, student_id: str, semester: Optional[int] = None) -> dict:
        """MCP Tool: Get student grades from database"""
        from backend.database import AsyncSessionLocal
        from backend.models import Student, Grade, Course
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload

        async with AsyncSessionLocal() as db:
            stu_q = await db.execute(select(Student).where(Student.student_id == student_id))
            student = stu_q.scalar_one_or_none()
            if not student:
                return {"error": f"Student {student_id} not found"}

            grades_q = await db.execute(
                select(Grade).where(Grade.student_id == student.id)
                .options(selectinload(Grade.course))
            )
            grades = grades_q.scalars().all()

            return {
                "student_id": student_id,
                "gpa": student.gpa,
                "grades": [
                    {
                        "course": g.course.title,
                        "code": g.course.course_code,
                        "credits": g.course.credits,
                        "total": g.total,
                        "letter": g.letter_grade,
                        "grade_points": g.grade_points
                    }
                    for g in grades
                ]
            }

    async def search_library(self, query: str, category: Optional[str] = None) -> dict:
        """MCP Tool: Search library catalog"""
        from backend.database import AsyncSessionLocal
        from backend.models import Book
        from sqlalchemy import select, or_

        async with AsyncSessionLocal() as db:
            q = select(Book).where(
                or_(
                    Book.title.ilike(f"%{query}%"),
                    Book.author.ilike(f"%{query}%"),
                    Book.isbn.ilike(f"%{query}%")
                )
            )
            if category:
                q = q.where(Book.category == category)
            result = await db.execute(q.limit(10))
            books = result.scalars().all()
            return {
                "results": [
                    {
                        "title": b.title,
                        "author": b.author,
                        "isbn": b.isbn,
                        "category": b.category,
                        "available": b.available_copies,
                        "total": b.total_copies,
                        "location": b.location
                    }
                    for b in books
                ],
                "count": len(books)
            }

    async def get_course_schedule(self, faculty: Optional[str] = None, semester: Optional[int] = None) -> dict:
        """MCP Tool: Get course schedule"""
        from backend.database import AsyncSessionLocal
        from backend.models import Course, Lecturer
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload

        async with AsyncSessionLocal() as db:
            q = select(Course).where(Course.is_active == True)
            if faculty:
                q = q.where(Course.faculty == faculty)
            if semester:
                q = q.where(Course.semester == semester)
            q = q.options(selectinload(Course.lecturer).selectinload(Lecturer.user))
            result = await db.execute(q.limit(20))
            courses = result.scalars().all()
            return {
                "courses": [
                    {
                        "code": c.course_code,
                        "title": c.title,
                        "credits": c.credits,
                        "faculty": c.faculty,
                        "schedule": c.schedule,
                        "lecturer": c.lecturer.user.full_name if c.lecturer else "TBD"
                    }
                    for c in courses
                ]
            }

    async def get_club_events(self, club_name: Optional[str] = None, days_ahead: int = 30) -> dict:
        """MCP Tool: Get upcoming club events"""
        from backend.database import AsyncSessionLocal
        from backend.models import Club, ClubEvent
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        from datetime import datetime, timedelta

        async with AsyncSessionLocal() as db:
            cutoff = datetime.utcnow() + timedelta(days=days_ahead)
            q = select(ClubEvent).where(
                ClubEvent.event_date.between(datetime.utcnow(), cutoff)
            ).options(selectinload(ClubEvent.club))
            result = await db.execute(q.order_by(ClubEvent.event_date).limit(10))
            events = result.scalars().all()
            return {
                "events": [
                    {
                        "title": e.title,
                        "club": e.club.name,
                        "date": e.event_date.strftime("%Y-%m-%d %H:%M"),
                        "location": e.location,
                        "registration_required": e.registration_required
                    }
                    for e in events
                ]
            }

    async def calculate_gpa(self, grades: list) -> dict:
        """MCP Tool: Calculate GPA from grade list"""
        gp_map = {
            "A+": 4.0, "A": 4.0, "B+": 3.5, "B": 3.0,
            "C+": 2.5, "C": 2.0, "D": 1.5, "F": 0.0
        }
        total_points = 0
        total_credits = 0
        for g in grades:
            letter = g.get("letter_grade", "F")
            credits = g.get("credits", 3)
            gp = gp_map.get(letter, 0.0)
            total_points += gp * credits
            total_credits += credits
        gpa = round(total_points / total_credits, 2) if total_credits > 0 else 0.0
        return {
            "gpa": gpa,
            "total_credits": total_credits,
            "classification": "Dean's List" if gpa >= 3.8 else "First Class" if gpa >= 3.5 else
                              "Second Class Upper" if gpa >= 3.0 else "Second Class Lower" if gpa >= 2.5 else
                              "Pass" if gpa >= 2.0 else "Fail"
        }

    async def get_news(self, category: Optional[str] = None, limit: int = 5) -> dict:
        """MCP Tool: Get latest news"""
        from backend.database import AsyncSessionLocal
        from backend.models import News
        from sqlalchemy import select

        async with AsyncSessionLocal() as db:
            q = select(News).where(News.is_published == True)
            if category:
                q = q.where(News.category == category)
            result = await db.execute(q.order_by(News.published_at.desc()).limit(limit))
            articles = result.scalars().all()
            return {
                "articles": [
                    {
                        "title": n.title,
                        "summary": n.summary,
                        "category": n.category.value,
                        "published_at": n.published_at.strftime("%Y-%m-%d")
                    }
                    for n in articles
                ]
            }

    async def get_exam_schedule(self, semester: Optional[int] = None, faculty: Optional[str] = None) -> dict:
        """MCP Tool: Get exam schedule"""
        # Mock exam schedule data
        schedule = {
            "semester": semester or 1,
            "exams": [
                {"course": "CS101", "date": "2026-01-15", "time": "09:00 AM", "venue": "Hall A"},
                {"course": "CS201", "date": "2026-01-17", "time": "09:00 AM", "venue": "Hall B"},
                {"course": "SE101", "date": "2026-01-20", "time": "02:00 PM", "venue": "Hall A"},
                {"course": "IT101", "date": "2026-01-22", "time": "09:00 AM", "venue": "Hall C"},
            ],
            "note": "Please bring your student ID and exam slip. Mobile phones are strictly prohibited."
        }
        return schedule


# Global MCP server instance
mcp_server = EduSphereMCPServer()
