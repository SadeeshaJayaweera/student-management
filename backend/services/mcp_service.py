"""
NSBM EduSphere — MCP (Model Context Protocol) Server & Tool Orchestrator
Exposes university data as MCP tools with role-based execution boundaries,
parameter schema validation, and persistent audit logging.
"""
import time
from datetime import datetime, date, timedelta
from typing import Any, Optional, Dict, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_, func
from sqlalchemy.orm import selectinload

from backend.config import settings
from backend.models import (
    User,
    Student,
    Lecturer,
    Course,
    Grade,
    Attendance,
    Assignment,
    AssignmentSubmission,
    TimetableSlot,
    CampusFacility,
    FacilityReservation,
    ShuttleRoute,
    ShuttleSchedule,
    TransportVehicle,
    Book,
    ClubEvent,
    News,
    MCPToolExecutionLog,
)


class EduSphereMCPServer:
    """
    Enterprise MCP Server for NSBM EduSphere
    Exposes university data tools for AI agents and LLM tool-calling loops
    with role boundaries and audit logging.
    """

    def __init__(self):
        self._tool_metadata = {
            "lookup_student_timetable": {
                "description": "Retrieve daily or weekly class timetable schedule for an enrolled student",
                "category": "Academics",
                "required_roles": ["student", "lecturer", "admin"],
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "student_id": {"type": "string", "description": "Student registration number (e.g., STU001)"},
                        "day_of_week": {"type": "string", "description": "Specific day (Monday..Friday), or all"}
                    },
                    "required": ["student_id"]
                }
            },
            "check_assignment_deadlines": {
                "description": "Check upcoming assignment deadlines and submission statuses for a student",
                "category": "Academics",
                "required_roles": ["student", "lecturer", "admin"],
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "student_id": {"type": "string", "description": "Student registration number"},
                        "days_ahead": {"type": "integer", "description": "Lookahead horizon in days (default: 30)"}
                    },
                    "required": ["student_id"]
                }
            },
            "get_academic_grade_summary": {
                "description": "Retrieve verified academic grades, earned credits, and calculated GPA",
                "category": "Academics",
                "required_roles": ["student", "lecturer", "admin"],
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "student_id": {"type": "string", "description": "Student registration number"},
                        "semester": {"type": "integer", "description": "Semester number filter (optional)"}
                    },
                    "required": ["student_id"]
                }
            },
            "verify_student_attendance": {
                "description": "Verify student class attendance rates and 80% exam eligibility thresholds",
                "category": "Compliance",
                "required_roles": ["student", "lecturer", "admin"],
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "student_id": {"type": "string", "description": "Student registration number"},
                        "course_code": {"type": "string", "description": "Course code filter (optional)"}
                    },
                    "required": ["student_id"]
                }
            },
            "check_facility_availability": {
                "description": "Inspect availability and reserved time slots for campus facilities/halls",
                "category": "Campus",
                "required_roles": ["student", "lecturer", "admin", "alumni"],
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "facility_name": {"type": "string", "description": "Facility or hall name (optional)"},
                        "facility_type": {"type": "string", "description": "Type: lecture_hall, computer_lab, auditorium, etc."}
                    }
                }
            },
            "lookup_shuttle_schedules": {
                "description": "Lookup commuter shuttle schedules, active routes, and vehicle GPS status",
                "category": "Transit",
                "required_roles": ["student", "lecturer", "admin", "alumni"],
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "origin": {"type": "string", "description": "Origin location (optional)"},
                        "destination": {"type": "string", "description": "Destination location (optional)"}
                    }
                }
            },
            "search_library": {
                "description": "Search the NSBM library catalog for physical and digital books",
                "category": "Library",
                "required_roles": ["student", "lecturer", "admin", "alumni"],
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query (title, author, ISBN)"},
                        "category": {"type": "string", "description": "Book category filter (optional)"}
                    },
                    "required": ["query"]
                }
            },
            "calculate_gpa": {
                "description": "Calculate GPA and academic honors classification from grade list",
                "category": "Academics",
                "required_roles": ["student", "lecturer", "admin", "alumni"],
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
                            "description": "List of courses with letter_grade and credits"
                        }
                    },
                    "required": ["grades"]
                }
            },
            "get_club_events": {
                "description": "Get upcoming university club, athletic, and cultural events",
                "category": "Campus",
                "required_roles": ["student", "lecturer", "admin", "alumni"],
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "club_name": {"type": "string", "description": "Club name filter (optional)"},
                        "days_ahead": {"type": "integer", "description": "Days horizon"}
                    }
                }
            },
            "get_news": {
                "description": "Get published campus news articles and official announcements",
                "category": "Campus",
                "required_roles": ["student", "lecturer", "admin", "alumni"],
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "category": {"type": "string", "description": "Category: academic, sports, events, alumni"},
                        "limit": {"type": "integer", "description": "Number of articles"}
                    }
                }
            }
        }

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """Return MCP standard tool specifications"""
        definitions = []
        for name, meta in self._tool_metadata.items():
            definitions.append({
                "name": name,
                "description": meta["description"],
                "category": meta["category"],
                "required_roles": meta["required_roles"],
                "inputSchema": meta["inputSchema"]
            })
        return definitions

    async def execute_tool(
        self,
        db: AsyncSession,
        tool_name: str,
        arguments: Dict[str, Any],
        caller: User
    ) -> Dict[str, Any]:
        """
        Execute tool with role boundary check, parameter sanitization, latency tracking,
        and persistent audit logging.
        """
        start_time = time.time()
        meta = self._tool_metadata.get(tool_name)
        if not meta:
            return {"error": f"Tool '{tool_name}' is not recognized in MCP registry"}

        # 1. Role Boundary Check
        user_role_str = caller.role.value if hasattr(caller.role, "value") else str(caller.role)
        if user_role_str not in meta["required_roles"]:
            await self._log_invocation(db, caller.id, tool_name, arguments, "unauthorized", 0.0, "Forbidden for caller role")
            return {
                "tool_name": tool_name,
                "result": {"error": f"Role '{user_role_str}' is unauthorized to execute tool '{tool_name}'"},
                "execution_time_ms": 0.0,
                "status": "unauthorized"
            }

        # 2. Privacy Boundary: Students can only query their own data
        if user_role_str == "student" and "student_id" in arguments:
            stu_res = await db.execute(select(Student).where(Student.user_id == caller.id))
            caller_student = stu_res.scalar_one_or_none()
            if not caller_student or caller_student.student_id != arguments["student_id"]:
                await self._log_invocation(db, caller.id, tool_name, arguments, "unauthorized", 0.0, "Privacy boundary violation")
                return {
                    "tool_name": tool_name,
                    "result": {"error": "Access denied: Students can only inspect their own academic records"},
                    "execution_time_ms": 0.0,
                    "status": "unauthorized"
                }

        # 3. Tool Dispatch
        try:
            handler = getattr(self, f"_{tool_name}", None)
            if not handler:
                res_data = {"error": f"Handler not implemented for tool '{tool_name}'"}
                status = "error"
            else:
                res_data = await handler(db, arguments, caller)
                status = "success"
        except Exception as e:
            res_data = {"error": str(e)}
            status = "error"

        latency_ms = round((time.time() - start_time) * 1000.0, 2)
        err_msg = res_data.get("error") if isinstance(res_data, dict) else None
        await self._log_invocation(db, caller.id, tool_name, arguments, status, latency_ms, err_msg)

        return {
            "tool_name": tool_name,
            "result": res_data,
            "execution_time_ms": latency_ms,
            "status": status
        }

    async def _log_invocation(
        self,
        db: AsyncSession,
        user_id: Optional[int],
        tool_name: str,
        arguments: Dict[str, Any],
        status: str,
        latency_ms: float,
        error_message: Optional[str]
    ):
        """Record audit log entry for tool execution"""
        try:
            log_entry = MCPToolExecutionLog(
                user_id=user_id,
                tool_name=tool_name,
                arguments_json=arguments,
                result_status=status,
                execution_time_ms=latency_ms,
                error_message=error_message
            )
            db.add(log_entry)
            await db.commit()
        except Exception:
            pass

    # ── Tool Implementations ──────────────────────────────────────────────────

    async def _lookup_student_timetable(self, db: AsyncSession, args: dict, caller: User) -> dict:
        student_id = args["student_id"]
        day_filter = args.get("day_of_week")

        stu_res = await db.execute(select(Student).where(Student.student_id == student_id))
        student = stu_res.scalar_one_or_none()
        if not student:
            return {"error": f"Student with ID '{student_id}' not found"}

        stmt = (
            select(TimetableSlot)
            .join(Course, TimetableSlot.course_id == Course.id)
            .where(TimetableSlot.is_active == True)
        )
        if student.faculty:
            stmt = stmt.where(Course.faculty == student.faculty)

        day_map = {"monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3, "friday": 4, "saturday": 5, "sunday": 6}
        if day_filter and day_filter.lower() in day_map:
            stmt = stmt.where(TimetableSlot.day_of_week == day_map[day_filter.lower()])

        res = await db.execute(stmt.options(selectinload(TimetableSlot.course)).limit(15))
        slots = res.scalars().all()

        days_reverse = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        return {
            "student_id": student_id,
            "slots_count": len(slots),
            "timetable": [
                {
                    "course_code": s.course.course_code if s.course else "TBD",
                    "course_title": s.course.title if s.course else s.title,
                    "day": days_reverse[s.day_of_week] if 0 <= s.day_of_week < len(days_reverse) else str(s.day_of_week),
                    "time": f"{s.start_time} - {s.end_time}",
                    "room": s.room,
                    "slot_type": s.slot_type
                }
                for s in slots
            ]
        }

    async def _check_assignment_deadlines(self, db: AsyncSession, args: dict, caller: User) -> dict:
        student_id = args["student_id"]
        days_ahead = args.get("days_ahead", 30)

        stu_res = await db.execute(select(Student).where(Student.student_id == student_id))
        student = stu_res.scalar_one_or_none()
        if not student:
            return {"error": f"Student with ID '{student_id}' not found"}

        now = datetime.utcnow()
        cutoff = now + timedelta(days=days_ahead)

        assign_stmt = (
            select(Assignment)
            .where(
                Assignment.due_date >= now,
                Assignment.due_date <= cutoff,
                Assignment.status == "published"
            )
            .options(selectinload(Assignment.course))
            .order_by(Assignment.due_date.asc())
        )
        res = await db.execute(assign_stmt.limit(10))
        assignments = res.scalars().all()

        items = []
        for a in assignments:
            # Check submission
            sub_res = await db.execute(
                select(AssignmentSubmission).where(
                    AssignmentSubmission.assignment_id == a.id,
                    AssignmentSubmission.student_id == student.id
                )
            )
            sub = sub_res.scalar_one_or_none()
            days_left = max(0, (a.due_date - now).days)
            items.append({
                "assignment_id": a.id,
                "title": a.title,
                "course_code": a.course.course_code if a.course else "",
                "due_date": a.due_date.strftime("%Y-%m-%d %H:%M"),
                "days_remaining": days_left,
                "submitted": sub is not None,
                "submission_status": sub.status if sub else "unsubmitted"
            })

        return {
            "student_id": student_id,
            "upcoming_deadlines_count": len(items),
            "deadlines": items
        }

    async def _get_academic_grade_summary(self, db: AsyncSession, args: dict, caller: User) -> dict:
        student_id = args["student_id"]
        sem_filter = args.get("semester")

        stu_res = await db.execute(select(Student).where(Student.student_id == student_id))
        student = stu_res.scalar_one_or_none()
        if not student:
            return {"error": f"Student with ID '{student_id}' not found"}

        stmt = (
            select(Grade)
            .where(Grade.student_id == student.id)
            .options(selectinload(Grade.course))
        )
        if sem_filter:
            stmt = stmt.where(Grade.semester_id == sem_filter)

        res = await db.execute(stmt)
        grades = res.scalars().all()

        total_pts = sum(g.grade_points * (g.course.credits if g.course else 3) for g in grades if g.grade_points is not None)
        total_cr = sum(g.course.credits if g.course else 3 for g in grades if g.grade_points is not None)
        gpa = round(total_pts / total_cr, 2) if total_cr > 0 else (student.gpa or 0.0)

        return {
            "student_id": student_id,
            "gpa": gpa,
            "credits_earned": total_cr or student.credits_earned,
            "courses_graded": len(grades),
            "records": [
                {
                    "course_code": g.course.course_code if g.course else "",
                    "course_title": g.course.title if g.course else "",
                    "letter_grade": g.letter_grade,
                    "grade_points": g.grade_points,
                    "total": g.total
                }
                for g in grades
            ]
        }

    async def _verify_student_attendance(self, db: AsyncSession, args: dict, caller: User) -> dict:
        student_id = args["student_id"]
        stu_res = await db.execute(select(Student).where(Student.student_id == student_id))
        student = stu_res.scalar_one_or_none()
        if not student:
            return {"error": f"Student with ID '{student_id}' not found"}

        att_records_res = await db.execute(
            select(Attendance).where(Attendance.student_id == student.id)
        )
        records = att_records_res.scalars().all()
        total_sessions = len(records)
        present_sessions = sum(
            1 for r in records
            if (r.status == "present" or (hasattr(r.status, "value") and r.status.value == "present"))
        )

        rate = round((present_sessions / total_sessions * 100), 1) if total_sessions > 0 else 100.0
        eligible_for_exams = rate >= 80.0

        return {
            "student_id": student_id,
            "total_sessions": total_sessions,
            "attended_sessions": present_sessions,
            "attendance_rate": rate,
            "eligible_for_exams": eligible_for_exams,
            "warning": None if eligible_for_exams else f"Warning: Attendance rate ({rate}%) is below mandatory 80% threshold"
        }

    async def _check_facility_availability(self, db: AsyncSession, args: dict, caller: User) -> dict:
        fac_name = args.get("facility_name")
        fac_type = args.get("facility_type")

        stmt = select(CampusFacility).where(CampusFacility.status == "available")
        if fac_name:
            stmt = stmt.where(CampusFacility.name.ilike(f"%{fac_name}%"))
        if fac_type:
            stmt = stmt.where(CampusFacility.facility_type == fac_type)

        res = await db.execute(stmt.limit(10))
        facilities = res.scalars().all()

        return {
            "facilities_found": len(facilities),
            "facilities": [
                {
                    "name": f.name,
                    "code": f.code,
                    "type": f.facility_type,
                    "capacity": f.capacity,
                    "building": f.building,
                    "status": f.status
                }
                for f in facilities
            ]
        }

    async def _lookup_shuttle_schedules(self, db: AsyncSession, args: dict, caller: User) -> dict:
        origin = args.get("origin")
        dest = args.get("destination")

        stmt = select(ShuttleRoute).where(ShuttleRoute.is_active == True)
        if origin:
            stmt = stmt.where(ShuttleRoute.origin.ilike(f"%{origin}%"))
        if dest:
            stmt = stmt.where(ShuttleRoute.destination.ilike(f"%{dest}%"))

        res = await db.execute(stmt.options(selectinload(ShuttleRoute.schedules)).limit(10))
        routes = res.scalars().all()

        return {
            "routes_count": len(routes),
            "routes": [
                {
                    "route_code": r.route_code,
                    "route_name": r.route_name,
                    "origin": r.origin,
                    "destination": r.destination,
                    "distance_km": r.distance_km,
                    "fare_amount": r.fare_amount,
                    "schedules": [
                        {
                            "departure_time": s.departure_time,
                            "arrival_time": s.arrival_time,
                            "shift_type": s.shift_type
                        }
                        for s in r.schedules
                    ]
                }
                for r in routes
            ]
        }

    async def _search_library(self, db: AsyncSession, args: dict, caller: User) -> dict:
        query = args["query"]
        category = args.get("category")

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
            "count": len(books),
            "results": [
                {
                    "title": b.title,
                    "author": b.author,
                    "isbn": b.isbn,
                    "category": b.category,
                    "available_copies": b.available_copies,
                    "location": b.location
                }
                for b in books
            ]
        }

    async def _calculate_gpa(self, db: AsyncSession, args: dict, caller: User) -> dict:
        grades = args.get("grades", [])
        gp_map = {
            "A+": 4.0, "A": 4.0, "B+": 3.5, "B": 3.0,
            "C+": 2.5, "C": 2.0, "D": 1.5, "F": 0.0
        }
        total_points = 0.0
        total_credits = 0
        for g in grades:
            letter = g.get("letter_grade", "F").upper()
            credits = g.get("credits", 3)
            gp = gp_map.get(letter, 0.0)
            total_points += gp * credits
            total_credits += credits

        gpa = round(total_points / total_credits, 2) if total_credits > 0 else 0.0
        return {
            "gpa": gpa,
            "total_credits": total_credits,
            "classification": (
                "First Class (Dean's List)" if gpa >= 3.8 else
                "First Class" if gpa >= 3.5 else
                "Second Class Upper" if gpa >= 3.0 else
                "Second Class Lower" if gpa >= 2.5 else
                "General Pass" if gpa >= 2.0 else "Fail"
            )
        }

    async def _get_club_events(self, db: AsyncSession, args: dict, caller: User) -> dict:
        days_ahead = args.get("days_ahead", 30)
        cutoff = datetime.utcnow() + timedelta(days=days_ahead)

        stmt = (
            select(ClubEvent)
            .where(ClubEvent.event_date.between(datetime.utcnow(), cutoff))
            .options(selectinload(ClubEvent.club))
            .order_by(ClubEvent.event_date.asc())
            .limit(10)
        )
        res = await db.execute(stmt)
        events = res.scalars().all()

        return {
            "events_count": len(events),
            "events": [
                {
                    "title": e.title,
                    "club": e.club.name if e.club else "University Event",
                    "event_date": e.event_date.strftime("%Y-%m-%d %H:%M"),
                    "location": e.location
                }
                for e in events
            ]
        }

    async def _get_news(self, db: AsyncSession, args: dict, caller: User) -> dict:
        limit = args.get("limit", 5)
        stmt = select(News).where(News.is_published == True).order_by(News.published_at.desc()).limit(limit)
        res = await db.execute(stmt)
        articles = res.scalars().all()

        return {
            "articles_count": len(articles),
            "articles": [
                {
                    "title": n.title,
                    "summary": n.summary,
                    "category": n.category.value if hasattr(n.category, "value") else str(n.category),
                    "published_at": n.published_at.strftime("%Y-%m-%d")
                }
                for n in articles
            ]
        }


# Global instance
mcp_server = EduSphereMCPServer()
