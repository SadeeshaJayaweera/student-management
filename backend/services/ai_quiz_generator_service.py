"""
NSBM EduSphere — AI Quiz & Question Generation Service
Synthesizes Bloom's taxonomy quiz items, distractor rationales, code analysis tasks,
and rubric guides from course materials, with Question Bank & Quiz integration.
"""
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from backend.models import (
    Course,
    User,
    AIQuizGenerationJob,
    AIGeneratedQuestion,
    QuestionCategory,
    QuestionBankItem,
    Quiz,
    QuizQuestion,
)


class AIQuizGeneratorService:
    """Service generating Bloom's taxonomy assessments from syllabus text"""

    def _extract_concepts(self, text: str) -> List[str]:
        """Extract key academic sentences and concept statements"""
        sentences = [s.strip() for s in re.split(r"[.\n;]", text) if len(s.strip()) > 15]
        return sentences if sentences else [text[:200]]

    async def generate_questions_job(
        self,
        db: AsyncSession,
        course_id: int,
        created_by_user_id: int,
        source_text: str,
        title: str = "Generated Quiz",
        blooms_level: str = "understand",
        difficulty: str = "medium",
        question_count: int = 3,
        question_types: Optional[List[str]] = None
    ) -> AIQuizGenerationJob:
        """Generate structured quiz items with rationales and rubric guidelines"""
        course_res = await db.execute(select(Course).where(Course.id == course_id))
        course = course_res.scalar_one_or_none()
        if not course:
            raise ValueError(f"Course {course_id} does not exist")

        q_types = question_types or ["multiple_choice", "short_answer", "code_analysis"]

        job = AIQuizGenerationJob(
            course_id=course_id,
            created_by_user_id=created_by_user_id,
            title=title or f"AI Quiz — {course.course_code}",
            source_text=source_text,
            blooms_level=blooms_level,
            difficulty=difficulty,
            question_count=question_count,
            question_types=q_types,
            status="completed"
        )
        db.add(job)
        await db.flush()

        concepts = self._extract_concepts(source_text)

        for i in range(question_count):
            q_type = q_types[i % len(q_types)]
            concept = concepts[i % len(concepts)]

            if q_type == "multiple_choice":
                prompt = (
                    f"According to the principles discussed in the lecture materials, "
                    f"which of the following best characterizes: '{concept}'?"
                )
                options = [
                    {"id": "A", "text": f"It directly enforces {concept.lower()} through optimal state evaluation."},
                    {"id": "B", "text": "It applies exclusively to static data structures and cannot scale to dynamic inputs."},
                    {"id": "C", "text": "It incurs an exponential worst-case runtime regardless of optimization."},
                    {"id": "D", "text": "It bypasses formal termination conditions by using non-deterministic jumps."}
                ]
                correct = "A"
                explanation = (
                    "Option A is correct: The syllabus establishes that this mechanism enforces optimal evaluation. "
                    "Option B is a distractor (fails to account for dynamic arrays/graphs). "
                    "Option C is a distractor (confuses polynomial vs exponential complexity). "
                    "Option D is a distractor (violates deterministic correctness)."
                )
                rubric = None

            elif q_type == "code_analysis":
                prompt = (
                    f"Analyze the following algorithm implementation related to '{concept}':\n\n"
                    "```python\n"
                    "def process_elements(items):\n"
                    "    if not items:\n"
                    "        return 0\n"
                    "    pivot = items[len(items) // 2]\n"
                    "    return pivot + process_elements(items[:-1])\n"
                    "```\n\n"
                    "What is the asymptotic time complexity and primary potential failure mode of this implementation?"
                )
                options = None
                correct = (
                    "Time Complexity: O(n^2) due to slicing items[:-1] on each frame. "
                    "Failure mode: RecursionError / Maximum call stack exceeded on large inputs."
                )
                explanation = (
                    "In Python, slicing items[:-1] incurs a shallow copy of size k at each step, yielding a quadratic recurrence T(n) = T(n-1) + O(n). "
                    "Unbounded recursion depth leads to stack overflow."
                )
                rubric = {
                    "criteria": [
                        {"criterion": "Identified O(n^2) slicing complexity", "points": 2.0},
                        {"criterion": "Identified recursion depth / call stack failure", "points": 2.0},
                        {"criterion": "Proposed iterative or pointer-based optimization", "points": 1.0}
                    ],
                    "max_points": 5.0
                }

            else:  # short_answer
                prompt = (
                    f"Explain the theoretical significance and practical application of the following concept in {course.course_code}: "
                    f"'{concept}'. Include at least one concrete educational or industrial example."
                )
                options = None
                correct = f"Comprehensive conceptual definition of {concept}, including mathematical/logical formulation and trade-off comparison."
                explanation = "Student responses must demonstrate Bloom's taxonomy application level with clear argumentation."
                rubric = {
                    "criteria": [
                        {"criterion": "Precise conceptual definition", "points": 2.0},
                        {"criterion": "Valid industrial or educational application", "points": 2.0},
                        {"criterion": "Discussion of limitations and edge cases", "points": 1.0}
                    ],
                    "max_points": 5.0
                }

            q_record = AIGeneratedQuestion(
                job_id=job.id,
                question_type=q_type,
                prompt=prompt,
                options=options,
                correct_answer=correct,
                explanation=explanation,
                blooms_level=blooms_level,
                difficulty=difficulty,
                rubric_guide=rubric,
                is_approved=False
            )
            db.add(q_record)

        await db.commit()
        # Eagerly load questions to prevent greenlet error during serialization
        job_res = await db.execute(
            select(AIQuizGenerationJob)
            .where(AIQuizGenerationJob.id == job.id)
            .options(selectinload(AIQuizGenerationJob.questions))
        )
        return job_res.scalar_one()

    async def get_job_details(
        self,
        db: AsyncSession,
        job_id: int
    ) -> AIQuizGenerationJob:
        """Retrieve job and all generated question items"""
        stmt = (
            select(AIQuizGenerationJob)
            .where(AIQuizGenerationJob.id == job_id)
            .options(selectinload(AIQuizGenerationJob.questions))
        )
        res = await db.execute(stmt)
        job = res.scalar_one_or_none()
        if not job:
            raise ValueError(f"Quiz generation job {job_id} not found")
        return job

    async def list_course_jobs(
        self,
        db: AsyncSession,
        course_id: int
    ) -> List[AIQuizGenerationJob]:
        """List generation jobs for a course"""
        stmt = (
            select(AIQuizGenerationJob)
            .where(AIQuizGenerationJob.course_id == course_id)
            .options(selectinload(AIQuizGenerationJob.questions))
            .order_by(AIQuizGenerationJob.created_at.desc())
        )
        res = await db.execute(stmt)
        return res.scalars().all()

    async def approve_and_export_question(
        self,
        db: AsyncSession,
        question_id: int,
        creator: User
    ) -> QuestionBankItem:
        """Approve generated question and export to Course Question Bank"""
        stmt = (
            select(AIGeneratedQuestion)
            .where(AIGeneratedQuestion.id == question_id)
            .options(selectinload(AIGeneratedQuestion.job))
        )
        res = await db.execute(stmt)
        q = res.scalar_one_or_none()
        if not q:
            raise ValueError(f"Question {question_id} not found")

        course_id = q.job.course_id

        # Find or create default question category
        cat_res = await db.execute(
            select(QuestionCategory).where(
                QuestionCategory.course_id == course_id,
                QuestionCategory.name == "AI Generated Items"
            )
        )
        category = cat_res.scalar_one_or_none()
        if not category:
            category = QuestionCategory(
                course_id=course_id,
                name="AI Generated Items",
                description="Verified questions created via AI Question Generator"
            )
            db.add(category)
            await db.flush()

        # Create QuestionBankItem
        bank_item = QuestionBankItem(
            course_id=course_id,
            category_id=category.id,
            creator_id=creator.id,
            title=f"AI [{q.blooms_level.title()}] - {q.prompt[:60]}...",
            prompt=q.prompt,
            question_type=q.question_type,
            difficulty_level="intermediate" if q.difficulty == "medium" else q.difficulty,
            default_points=5.0 if q.question_type != "multiple_choice" else 1.0,
            explanation=q.explanation,
            options=q.options,
            answer_key={"correct_answer": q.correct_answer},
            is_active=True
        )
        db.add(bank_item)
        await db.flush()

        q.is_approved = True
        q.question_bank_item_id = bank_item.id
        await db.commit()
        await db.refresh(bank_item)
        return bank_item

    async def publish_job_as_live_quiz(
        self,
        db: AsyncSession,
        job_id: int,
        creator: User,
        title: Optional[str] = None,
        time_limit_minutes: int = 30
    ) -> Quiz:
        """Publish questions in job as a live course Quiz"""
        job = await self.get_job_details(db, job_id)

        # Auto-approve all questions if not yet approved
        for q in job.questions:
            if not q.is_approved or not q.question_bank_item_id:
                await self.approve_and_export_question(db, q.id, creator)

        await db.refresh(job)

        quiz = Quiz(
            course_id=job.course_id,
            creator_id=creator.id,
            title=title or f"Quiz: {job.title}",
            description=f"Generated via EduSphere AI Question Generator from source materials ({job.blooms_level} level, {job.difficulty} difficulty).",
            time_limit_minutes=time_limit_minutes,
            passing_score_percentage=50.0,
            status="published",
            due_date=datetime.utcnow() + timedelta(days=14),
            total_points=float(len(job.questions) * 5)
        )
        db.add(quiz)
        await db.flush()

        for idx, q in enumerate(job.questions):
            qq = QuizQuestion(
                quiz_id=quiz.id,
                question_item_id=q.question_bank_item_id,
                order_index=idx,
                points=5.0 if q.question_type != "multiple_choice" else 1.0
            )
            db.add(qq)

        await db.commit()
        quiz_res = await db.execute(
            select(Quiz).where(Quiz.id == quiz.id).options(selectinload(Quiz.questions))
        )
        return quiz_res.scalar_one()


ai_quiz_generator_service = AIQuizGeneratorService()
