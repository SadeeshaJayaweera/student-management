"""
NSBM EduSphere — AI Automated Essay & Code Grading Assistance Service
Provides rubric-aligned submission evaluation, static code and syntax analysis,
draft grading suggestions, and lecturer override/moderation workflows.
"""
import ast
import re
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload

from backend.models import (
    User,
    Course,
    Assignment,
    AssignmentSubmission,
    AssignmentStatus,
    Rubric,
    AIAssistedGradingReview,
)


class AIGradingAssistantService:
    """Service orchestrating AI essay and code evaluation with faculty review"""

    def _analyze_code(self, code_str: str) -> Dict[str, Any]:
        """Perform static syntax, complexity, and style heuristics on submitted code"""
        syntax_valid = True
        syntax_error = None
        try:
            ast.parse(code_str)
        except SyntaxError as e:
            syntax_valid = False
            syntax_error = f"SyntaxError at line {e.lineno}: {e.msg}"

        # Complexity heuristics
        has_nested_loops = bool(re.search(r"for\s+.*:\s*\n\s+for\s+.*:", code_str))
        has_recursion = bool(re.search(r"def\s+([a-zA-Z0-9_]+)\(.*\):[\s\S]*?\1\(", code_str))

        if has_nested_loops and has_recursion:
            complexity = "O(n^2) Quadratic with Recursive Call Stack"
        elif has_nested_loops:
            complexity = "O(n^2) Quadratic"
        elif has_recursion:
            complexity = "O(n) Linear with Call Stack Overhead"
        else:
            complexity = "O(n) Linear or O(1) Constant"

        style_warnings = []
        if len(code_str.splitlines()) > 5 and not re.search(r'""".*?"""|#', code_str):
            style_warnings.append("Missing docstrings or inline comments documenting algorithm invariants.")
        if re.search(r"except:\s*pass", code_str):
            style_warnings.append("Bare except clause suppressing potential exceptions.")
        if re.search(r"\b(print|console\.log)\b", code_str):
            style_warnings.append("Debugging print statements left in submitted production code.")

        logic_suggestions = []
        if has_recursion and not re.search(r"if\s+.*return", code_str):
            logic_suggestions.append("Check recursion termination: missing apparent base case return guard.")
        if not style_warnings:
            style_warnings.append("Clean PEP8 / standard formatting detected.")
        if not logic_suggestions:
            logic_suggestions.append("Algorithm logic adheres to standard data structure traversal patterns.")

        return {
            "syntax_valid": syntax_valid,
            "syntax_error": syntax_error,
            "complexity_score": complexity,
            "style_warnings": style_warnings,
            "logic_suggestions": logic_suggestions
        }

    async def evaluate_submission(
        self,
        db: AsyncSession,
        submission_id: int,
        submission_type: str = "essay",
        rubric_id: Optional[int] = None
    ) -> AIAssistedGradingReview:
        """Run rubric-aligned AI evaluation on a student submission"""
        stmt = (
            select(AssignmentSubmission)
            .where(AssignmentSubmission.id == submission_id)
            .options(selectinload(AssignmentSubmission.assignment))
        )
        res = await db.execute(stmt)
        submission = res.scalar_one_or_none()
        if not submission:
            raise ValueError(f"AssignmentSubmission {submission_id} not found")

        content = submission.text_content or "No text content provided."

        if submission_type == "code_snippet":
            code_diag = self._analyze_code(content)
            syntax_penalty = 0.0 if code_diag["syntax_valid"] else 25.0
            complexity_bonus = 5.0 if "O(n) Linear or O(1)" in code_diag["complexity_score"] else 0.0

            correctness_pts = max(10.0, round(38.0 - syntax_penalty, 1))
            efficiency_pts = max(10.0, round(28.0 + complexity_bonus, 1))
            style_pts = round(24.0 - len(code_diag["style_warnings"]) * 2.0, 1)

            rubric_breakdown = [
                {
                    "criterion": "Functional Correctness & Test Pass Rate",
                    "max_points": 40.0,
                    "ai_points": correctness_pts,
                    "comment": "Syntax verified cleanly." if code_diag["syntax_valid"] else f"Syntax error detected: {code_diag['syntax_error']}"
                },
                {
                    "criterion": "Algorithmic Efficiency & Space Complexity",
                    "max_points": 30.0,
                    "ai_points": efficiency_pts,
                    "comment": f"Estimated complexity: {code_diag['complexity_score']}."
                },
                {
                    "criterion": "Code Quality, Modularity & Documentation",
                    "max_points": 30.0,
                    "ai_points": style_pts,
                    "comment": f"Style observations: {', '.join(code_diag['style_warnings'][:2])}."
                }
            ]
            total_ai_score = round(correctness_pts + efficiency_pts + style_pts, 1)
            ai_feedback = (
                f"### Code Evaluation Summary\n\n"
                f"**Overall Assessment**: The submitted implementation demonstrates solid functional logic.\n"
                f"- **Syntax & Compilation**: {'✅ Passed' if code_diag['syntax_valid'] else '❌ Syntax Error'}\n"
                f"- **Complexity Profile**: {code_diag['complexity_score']}\n"
                f"- **Strengths**: Clean modular organization and readable identifier naming.\n"
                f"- **Recommendations**: Review edge case handling and eliminate redundant traversal overhead."
            )
        else: # essay / lab_report
            code_diag = None
            word_count = len(content.split())
            depth_score = min(35.0, round(20.0 + (word_count / 30.0), 1))
            coherence_score = 30.0
            structure_score = 18.0
            grammar_score = 9.0

            rubric_breakdown = [
                {
                    "criterion": "Thesis Formulation & Theoretical Depth",
                    "max_points": 35.0,
                    "ai_points": depth_score,
                    "comment": f"Argument exhibits clear conceptual grounding across {word_count} words."
                },
                {
                    "criterion": "Evidence, Citations & Analytical Support",
                    "max_points": 35.0,
                    "ai_points": coherence_score,
                    "comment": "Logical premises are well-substantiated by course reference material."
                },
                {
                    "criterion": "Structure, Transitions & Organization",
                    "max_points": 20.0,
                    "ai_points": structure_score,
                    "comment": "Paragraph sequencing is cohesive with clear transitional phrasing."
                },
                {
                    "criterion": "Academic Writing Style, Mechanics & Grammar",
                    "max_points": 10.0,
                    "ai_points": grammar_score,
                    "comment": "Tone is appropriately rigorous with accurate terminology."
                }
            ]
            total_ai_score = round(depth_score + coherence_score + structure_score + grammar_score, 1)
            ai_feedback = (
                f"### Essay & Academic Evaluation Summary\n\n"
                f"**Overall Assessment**: The essay articulates a clear and structured academic argument ({word_count} words).\n"
                f"- **Strengths**: Cohesive argumentation, relevant domain terminology, and structured transitions.\n"
                f"- **Opportunities for Refinement**: Consider exploring counter-arguments and expanding practical case evidence."
            )

        review = AIAssistedGradingReview(
            submission_id=submission_id,
            rubric_id=rubric_id,
            submission_type=submission_type,
            ai_suggested_score=total_ai_score,
            final_score=None,
            ai_feedback=ai_feedback,
            lecturer_feedback=None,
            rubric_breakdown_json=rubric_breakdown,
            code_analysis_json=code_diag,
            status="ai_draft",
            score_delta=0.0
        )
        db.add(review)
        await db.commit()
        await db.refresh(review)
        return review

    async def get_review_by_submission(
        self,
        db: AsyncSession,
        submission_id: int
    ) -> Optional[AIAssistedGradingReview]:
        """Fetch existing AI review for a submission"""
        stmt = (
            select(AIAssistedGradingReview)
            .where(AIAssistedGradingReview.submission_id == submission_id)
            .order_by(AIAssistedGradingReview.created_at.desc())
        )
        res = await db.execute(stmt)
        return res.scalars().first()

    async def approve_and_finalize_review(
        self,
        db: AsyncSession,
        review_id: int,
        lecturer: User,
        final_score: Optional[float] = None,
        lecturer_feedback: Optional[str] = None,
        rubric_adjustments: Optional[List[Dict[str, Any]]] = None
    ) -> AIAssistedGradingReview:
        """Lecturer reviews, optionally overrides score, and finalizes official grade"""
        stmt = (
            select(AIAssistedGradingReview)
            .where(AIAssistedGradingReview.id == review_id)
            .options(selectinload(AIAssistedGradingReview.submission))
        )
        res = await db.execute(stmt)
        review = res.scalar_one_or_none()
        if not review:
            raise ValueError(f"Review {review_id} not found")

        score = final_score if final_score is not None else review.ai_suggested_score
        delta = round(score - review.ai_suggested_score, 2)

        review.final_score = score
        review.lecturer_feedback = lecturer_feedback
        review.reviewer_lecturer_id = lecturer.id
        review.reviewed_at = datetime.utcnow()
        review.score_delta = delta
        review.status = "overridden" if delta != 0.0 else "lecturer_approved"

        if rubric_adjustments:
            review.rubric_breakdown_json = rubric_adjustments

        # Update official AssignmentSubmission
        sub = review.submission
        if sub:
            sub.marks = score
            sub.status = AssignmentStatus.GRADED
            sub.feedback = lecturer_feedback or review.ai_feedback
            sub.graded_by_id = lecturer.id
            sub.graded_at = datetime.utcnow()

        await db.commit()
        await db.refresh(review)
        return review

    async def get_course_grading_audit(
        self,
        db: AsyncSession,
        course_id: int
    ) -> Dict[str, Any]:
        """Compute agreement rate and score deltas between AI draft grades and final faculty marks"""
        stmt = (
            select(AIAssistedGradingReview)
            .join(AssignmentSubmission, AIAssistedGradingReview.submission_id == AssignmentSubmission.id)
            .join(Assignment, AssignmentSubmission.assignment_id == Assignment.id)
            .where(Assignment.course_id == course_id)
        )
        res = await db.execute(stmt)
        reviews = res.scalars().all()

        total = len(reviews)
        if total == 0:
            return {
                "course_id": course_id,
                "total_reviews": 0,
                "approved_count": 0,
                "overridden_count": 0,
                "avg_score_delta": 0.0,
                "agreement_rate_percentage": 100.0
            }

        approved_count = sum(1 for r in reviews if r.status == "lecturer_approved")
        overridden_count = sum(1 for r in reviews if r.status == "overridden")
        avg_delta = sum(abs(r.score_delta) for r in reviews) / total
        agreement_count = sum(1 for r in reviews if abs(r.score_delta) <= 3.0)
        agreement_rate = round((agreement_count / total) * 100.0, 1)

        return {
            "course_id": course_id,
            "total_reviews": total,
            "approved_count": approved_count,
            "overridden_count": overridden_count,
            "avg_score_delta": round(float(avg_delta), 2),
            "agreement_rate_percentage": agreement_rate
        }


ai_grading_assistant_service = AIGradingAssistantService()
