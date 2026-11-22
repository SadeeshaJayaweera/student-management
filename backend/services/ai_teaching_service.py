"""
NSBM EduSphere — Conversational AI Teaching Assistant Service
Implements a Socratic AI tutoring engine with pedagogical scaffolding,
multi-turn session memory, syllabus boundary guardrails, and progressive hints.
"""
import re
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from backend.models import (
    Student,
    Course,
    AITeachingSession,
    AITeachingMessage,
)
from backend.services.course_rag_service import course_rag_service


OUT_OF_SCOPE_KEYWORDS = [
    "leak", "cheat", "hack", "bypass", "exploit", "exam paper leak",
    "give me the answers to the exam", "write my entire essay for me",
    "ignore all previous instructions", "jailbreak", "system prompt"
]


class AITeachingService:
    """Service orchestrating conversational Socratic teaching interactions"""

    async def create_session(
        self,
        db: AsyncSession,
        student_id: int,
        course_id: int,
        title: str = "Tutoring Session",
        teaching_mode: str = "socratic"
    ) -> AITeachingSession:
        """Create a new conversational teaching session with initial Socratic greeting"""
        # Verify course
        course_res = await db.execute(select(Course).where(Course.id == course_id))
        course = course_res.scalar_one_or_none()
        if not course:
            raise ValueError(f"Course {course_id} does not exist")

        session = AITeachingSession(
            student_id=student_id,
            course_id=course_id,
            title=title or f"{course.course_code} Tutoring",
            teaching_mode=teaching_mode,
            is_active=True,
            turn_count=0
        )
        db.add(session)
        await db.flush()

        # Initial opening message based on teaching mode
        if teaching_mode == "socratic":
            opening = (
                f"Hello! I am your Socratic AI Tutor for {course.course_code}: {course.title}. "
                f"Rather than simply handing over final answers, I'll guide you step-by-step so you truly master the material. "
                f"What concept, problem, or topic would you like to explore today?"
            )
            followups = [
                "I'm stuck on algorithmic complexity and Big-O notation",
                "Can you help me understand recursion base cases?",
                "How do graph traversal algorithms like BFS and DFS differ?"
            ]
        elif teaching_mode == "code_mentor":
            opening = (
                f"Welcome to your Code Mentorship session for {course.course_code}. "
                f"Paste your function or algorithm attempt, and let's analyze its correctness, edge cases, and runtime efficiency."
            )
            followups = [
                "Review my recursive Fibonacci implementation",
                "How can I optimize this O(n^2) nested loop?",
                "Help me structure a binary search tree traversal"
            ]
        elif teaching_mode == "exam_prep":
            opening = (
                f"Welcome to Exam Preparation mode for {course.course_code}. "
                f"Let's practice key exam questions. Shall we start with a conceptual challenge or an analytical problem?"
            )
            followups = [
                "Give me a high-yield conceptual question",
                "Test me on algorithm trace analysis",
                "Review common pitfalls in graph algorithms"
            ]
        else:
            opening = (
                f"Welcome! I am your AI Teaching Assistant for {course.course_code}: {course.title}. "
                f"Feel free to ask any question regarding lecture materials, assignments, or concepts."
            )
            followups = [
                "Explain the core topics of this module",
                "Summarize key definitions",
                "Show an illustrative practical example"
            ]

        msg = AITeachingMessage(
            session_id=session.id,
            role="assistant",
            content=opening,
            socratic_phase="inquiry",
            tokens_used=len(opening.split()),
            guardrail_triggered=False,
            suggested_followups=followups,
            hints=None
        )
        db.add(msg)
        await db.commit()
        await db.refresh(session)
        return session

    async def get_student_sessions(
        self,
        db: AsyncSession,
        student_id: int,
        course_id: Optional[int] = None
    ) -> List[AITeachingSession]:
        """List active teaching sessions for student"""
        stmt = (
            select(AITeachingSession)
            .where(
                AITeachingSession.student_id == student_id,
                AITeachingSession.is_active == True
            )
        )
        if course_id is not None:
            stmt = stmt.where(AITeachingSession.course_id == course_id)
        stmt = stmt.order_by(AITeachingSession.updated_at.desc())
        res = await db.execute(stmt)
        return res.scalars().all()

    async def get_session_details(
        self,
        db: AsyncSession,
        session_id: int,
        student_id: int
    ) -> AITeachingSession:
        """Fetch session with all chronological messages"""
        stmt = (
            select(AITeachingSession)
            .where(
                AITeachingSession.id == session_id,
                AITeachingSession.student_id == student_id
            )
            .options(selectinload(AITeachingSession.messages))
        )
        res = await db.execute(stmt)
        session = res.scalar_one_or_none()
        if not session:
            raise ValueError("Teaching session not found")
        return session

    def _check_guardrails(self, student_message: str, course_title: str) -> Optional[str]:
        """Validate input against academic integrity and syllabus boundaries"""
        msg_lower = student_message.lower()

        for bad_kw in OUT_OF_SCOPE_KEYWORDS:
            if bad_kw in msg_lower:
                return (
                    f"🛡️ Academic Guardrail Triggered: As an NSBM AI Teaching Assistant, I uphold university academic integrity. "
                    f"I cannot provide leaked examination materials, bypass academic checks, or write full graded assignments for you. "
                    f"However, I would be delighted to guide you through understanding the foundational concepts in {course_title}!"
                )
        return None

    def _determine_socratic_phase(self, turn_count: int, student_msg: str) -> str:
        """Progress through pedagogical phases: inquiry -> hint -> reflection -> verification -> summary"""
        msg_lower = student_msg.lower()
        if any(w in msg_lower for w in ["summary", "summarize", "recap", "wrap up", "in conclusion"]):
            return "summary"
        if any(w in msg_lower for w in ["i think", "is it because", "does that mean", "my attempt", "i got"]):
            return "verification"
        if any(w in msg_lower for w in ["hint", "stuck", "don't know", "dont know", "clue", "help me start"]):
            return "hint"
        if turn_count <= 2:
            return "inquiry"
        if turn_count <= 5:
            return "hint"
        return "reflection"

    async def process_student_turn(
        self,
        db: AsyncSession,
        session_id: int,
        student_id: int,
        content: str
    ) -> Dict[str, Any]:
        """
        Process student input, apply guardrails, ground with course materials,
        and generate Socratic pedagogical scaffolding.
        """
        session = await self.get_session_details(db, session_id, student_id)
        course_res = await db.execute(select(Course).where(Course.id == session.course_id))
        course = course_res.scalar_one_or_none()
        course_title = course.title if course else "Course Materials"

        # 1. Record student message
        user_msg = AITeachingMessage(
            session_id=session.id,
            role="user",
            content=content,
            socratic_phase="inquiry",
            tokens_used=len(content.split()),
            guardrail_triggered=False
        )
        db.add(user_msg)
        await db.flush()

        # 2. Check guardrails
        guardrail_violation = self._check_guardrails(content, course_title)
        if guardrail_violation:
            bot_msg = AITeachingMessage(
                session_id=session.id,
                role="assistant",
                content=guardrail_violation,
                socratic_phase="guardrail",
                tokens_used=len(guardrail_violation.split()),
                guardrail_triggered=True,
                suggested_followups=[
                    f"Let's review the fundamental concepts of {course_title}",
                    "Can you walk me through an example problem?",
                    "What are the prerequisite topics I should review?"
                ]
            )
            db.add(bot_msg)
            session.turn_count += 1
            await db.commit()
            await db.refresh(bot_msg)
            return {
                "user_message": user_msg,
                "assistant_message": bot_msg,
                "session": session
            }

        # 3. Grounding via course materials if relevant
        relevant_chunks = await course_rag_service.search_course_knowledge(
            db, session.course_id, content, top_k=2
        )
        course_context_hint = ""
        if relevant_chunks and relevant_chunks[0]["relevance_score"] > 0.1:
            best_chunk = relevant_chunks[0]
            course_context_hint = f" [Syllabus Reference: {best_chunk['document_title']}, Page {best_chunk['page_number']}]"

        # 4. Generate Socratic pedagogical response
        turn = session.turn_count + 1
        phase = self._determine_socratic_phase(turn, content)

        if phase == "hint":
            reply = (
                f"Let's break this down into smaller steps.{course_context_hint}\n\n"
                f"Consider the core condition: what happens when your input reaches its smallest possible value? "
                f"If you were to trace this step-by-step with an example value of n=3, what value would be produced first?"
            )
            hints = [
                "Hint 1: Recall that recursive algorithms require at least one terminating condition to prevent infinite stack growth.",
                "Hint 2: Identify the state variables that decrease toward the base case with each successive call."
            ]
            followups = [
                "I think the base case should return 1 or 0",
                "What happens when the input is negative?",
                "Could you provide another hint?"
            ]
        elif phase == "verification":
            reply = (
                f"Excellent reasoning! You are making keen progress.{course_context_hint}\n\n"
                f"Your intuition about the state transition is right on track. Now, reflect on this: "
                f"How does this choice impact the worst-case space complexity on the call stack?"
            )
            hints = [
                "Consider the maximum recursion depth, which determines the maximum number of activation records allocated."
            ]
            followups = [
                "The maximum stack depth would be O(n)",
                "Could we convert this recursion into an iterative loop with O(1) space?",
                "Let's test this with a larger input"
            ]
        elif phase == "summary":
            reply = (
                f"🎓 Outstanding work! Here is a structured recap of what you've synthesized today:\n\n"
                f"1. **Core Concept**: Understanding boundary constraints and state recurrence relations.\n"
                f"2. **Algorithm Mechanics**: Ensuring guaranteed termination through well-defined base cases.\n"
                f"3. **Efficiency Trade-off**: Balancing readable recursive formulations against memory overhead on the execution stack.\n\n"
                f"Would you like to try a related challenge problem to solidify your understanding?"
            )
            hints = None
            followups = [
                "Yes, give me a practice problem!",
                "Let's review the corresponding lecture notes",
                "I'm ready for the next topic"
            ]
        else: # inquiry
            reply = (
                f"That is an insightful question.{course_context_hint}\n\n"
                f"Before we jump to the conclusion, let's explore your current intuition: "
                f"When you approach this problem in {course_title}, what is the first principle or rule of thumb that comes to your mind?"
            )
            hints = [
                "Think about how similar problems were framed in the introductory lecture examples."
            ]
            followups = [
                "I usually try brute force first",
                "I consider divide-and-conquer principles",
                "Could you give me a starting hint?"
            ]

        bot_msg = AITeachingMessage(
            session_id=session.id,
            role="assistant",
            content=reply,
            socratic_phase=phase,
            tokens_used=len(reply.split()),
            guardrail_triggered=False,
            suggested_followups=followups,
            hints=hints
        )
        db.add(bot_msg)
        session.turn_count = turn
        await db.commit()
        await db.refresh(bot_msg)

        return {
            "user_message": user_msg,
            "assistant_message": bot_msg,
            "session": session
        }

    async def archive_session(
        self,
        db: AsyncSession,
        session_id: int,
        student_id: int
    ) -> AITeachingSession:
        """Mark session as inactive"""
        session = await self.get_session_details(db, session_id, student_id)
        session.is_active = False
        await db.commit()
        await db.refresh(session)
        return session


ai_teaching_service = AITeachingService()
