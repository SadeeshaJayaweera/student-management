import React, { useState, useEffect } from 'react';
import api from '../api/client';
import { useAuth } from '../contexts/AuthContext';
import {
  AIAssistedGradingReview,
  AIGradingAuditStats,
  Course,
} from '../types';
import toast from 'react-hot-toast';

export const AIGradingAssistant: React.FC = () => {
  const { user } = useAuth();
  const [courses, setCourses] = useState<Course[]>([]);
  const [selectedCourseId, setSelectedCourseId] = useState<number | null>(null);

  // Sample submission input for evaluation testbed
  const [submissionId, setSubmissionId] = useState<number>(1);
  const [submissionType, setSubmissionType] = useState<'essay' | 'code_snippet'>('essay');
  const [submissionContent, setSubmissionContent] = useState<string>(
    'The Liskov Substitution Principle provides strong behavioral subtyping guarantees. ' +
    'Subclasses must conform to the contract established by their base types without weakening preconditions.'
  );

  // Review State
  const [review, setReview] = useState<AIAssistedGradingReview | null>(null);
  const [isEvaluating, setIsEvaluating] = useState<boolean>(false);
  const [finalScoreInput, setFinalScoreInput] = useState<string>('');
  const [lecturerFeedbackInput, setLecturerFeedbackInput] = useState<string>('');
  const [isApproving, setIsApproving] = useState<boolean>(false);

  // Audit Stats
  const [auditStats, setAuditStats] = useState<AIGradingAuditStats | null>(null);

  useEffect(() => {
    fetchCourses();
  }, []);

  useEffect(() => {
    if (selectedCourseId) {
      fetchAudit(selectedCourseId);
    }
  }, [selectedCourseId]);

  const fetchCourses = async () => {
    try {
      const res = await api.get('/courses');
      const data: Course[] = res.data?.data || res.data || [];
      setCourses(data);
      if (data.length > 0) {
        setSelectedCourseId(data[0].id);
      }
    } catch (err) {
      toast.error('Failed to load courses');
    }
  };

  const fetchAudit = async (courseId: number) => {
    try {
      const res = await api.get(`/ai/grading/courses/${courseId}/audit`);
      setAuditStats(res.data);
    } catch (err) {
      // Non-critical if no reviews yet
    }
  };

  const handleRunEvaluation = async () => {
    setIsEvaluating(true);
    try {
      const res = await api.post(`/ai/grading/submissions/${submissionId}/evaluate`, {
        submission_type: submissionType,
      });
      setReview(res.data);
      setFinalScoreInput(String(res.data.ai_suggested_score));
      setLecturerFeedbackInput(res.data.ai_feedback);
      toast.success('AI evaluation complete with rubric breakdown');
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Evaluation failed (verify submission ID exists)');
    } finally {
      setIsEvaluating(false);
    }
  };

  const handleApproveOrOverride = async () => {
    if (!review) return;
    setIsApproving(true);
    try {
      const res = await api.post(`/ai/grading/reviews/${review.id}/approve`, {
        final_score: Number(finalScoreInput),
        lecturer_feedback: lecturerFeedbackInput,
      });
      setReview(res.data);
      toast.success(
        res.data.status === 'overridden'
          ? `Grade overridden to ${res.data.final_score}`
          : 'AI proposed grade approved'
      );
      if (selectedCourseId) fetchAudit(selectedCourseId);
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Approval failed');
    } finally {
      setIsApproving(false);
    }
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 bg-white/10 backdrop-blur-md p-6 rounded-2xl border border-white/20 shadow-xl">
        <div>
          <h1 className="text-3xl font-extrabold text-white flex items-center gap-3">
            <span>⚖️</span> AI Essay & Code Grading Assistant
          </h1>
          <p className="text-gray-300 mt-1">
            Rubric-grounded feedback, automated static code diagnostics & faculty score moderation
          </p>
        </div>

        {/* Course Selector */}
        <div className="flex items-center gap-3">
          <label className="text-white font-medium text-sm">Course:</label>
          <select
            className="bg-gray-800/80 text-white border border-gray-700 rounded-xl px-4 py-2 focus:ring-2 focus:ring-indigo-500 focus:outline-none"
            value={selectedCourseId || ''}
            onChange={(e) => setSelectedCourseId(Number(e.target.value))}
          >
            {courses.map((c) => (
              <option key={c.id} value={c.id}>
                {c.course_code} — {c.title}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Audit KPI Cards */}
      {auditStats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="bg-white/5 backdrop-blur-md p-5 rounded-2xl border border-white/10">
            <span className="text-gray-400 text-xs uppercase font-semibold">Total Submissions Evaluated</span>
            <div className="text-2xl font-extrabold text-white mt-1">
              {auditStats.total_reviews}
            </div>
          </div>
          <div className="bg-white/5 backdrop-blur-md p-5 rounded-2xl border border-white/10">
            <span className="text-gray-400 text-xs uppercase font-semibold">Faculty Approval Rate</span>
            <div className="text-2xl font-extrabold text-emerald-400 mt-1">
              {auditStats.agreement_rate_percentage}%
            </div>
          </div>
          <div className="bg-white/5 backdrop-blur-md p-5 rounded-2xl border border-white/10">
            <span className="text-gray-400 text-xs uppercase font-semibold">Score Overrides</span>
            <div className="text-2xl font-extrabold text-amber-400 mt-1">
              {auditStats.overridden_count}
            </div>
          </div>
          <div className="bg-white/5 backdrop-blur-md p-5 rounded-2xl border border-white/10">
            <span className="text-gray-400 text-xs uppercase font-semibold">Avg Score Delta</span>
            <div className="text-2xl font-extrabold text-indigo-400 mt-1">
              ±{auditStats.avg_score_delta} pts
            </div>
          </div>
        </div>
      )}

      {/* Evaluation Workspace */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left: Student Submission Viewer */}
        <div className="bg-white/5 backdrop-blur-md rounded-2xl border border-white/10 p-6 space-y-4 shadow-xl flex flex-col">
          <div className="flex justify-between items-center pb-2 border-b border-white/10">
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <span>📄</span> Student Submission
            </h2>
            <div className="flex items-center gap-2">
              <span className="text-xs text-gray-400">Type:</span>
              <select
                value={submissionType}
                onChange={(e) => setSubmissionType(e.target.value as any)}
                className="bg-gray-800 text-white text-xs border border-gray-700 rounded-lg px-2.5 py-1"
              >
                <option value="essay">Essay / Analysis</option>
                <option value="code_snippet">Code Snippet / Implementation</option>
              </select>
            </div>
          </div>

          <div className="flex gap-3">
            <div className="w-1/3">
              <label className="block text-xs font-medium text-gray-400 mb-1">Submission ID</label>
              <input
                type="number"
                min={1}
                value={submissionId}
                onChange={(e) => setSubmissionId(Number(e.target.value))}
                className="w-full bg-black/40 border border-gray-700 text-white rounded-xl px-3 py-2 text-sm"
              />
            </div>
            <div className="flex-1 flex items-end">
              <button
                onClick={handleRunEvaluation}
                disabled={isEvaluating}
                className="w-full bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-semibold py-2 rounded-xl transition shadow flex items-center justify-center gap-2 text-sm"
              >
                {isEvaluating ? 'Evaluating...' : '🤖 Run AI Grading'}
              </button>
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-400 mb-1">
              Submitted Content (Preview)
            </label>
            <textarea
              rows={12}
              value={submissionContent}
              onChange={(e) => setSubmissionContent(e.target.value)}
              className="w-full bg-black/50 font-mono text-xs text-gray-200 p-4 rounded-xl border border-gray-800 focus:ring-2 focus:ring-indigo-500 focus:outline-none"
            />
          </div>
        </div>

        {/* Right: AI Grading & Moderation Panel */}
        <div className="bg-white/5 backdrop-blur-md rounded-2xl border border-white/10 p-6 space-y-5 shadow-xl flex flex-col">
          <div className="flex justify-between items-center pb-2 border-b border-white/10">
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <span>📊</span> AI Grading & Moderation Panel
            </h2>
            {review && (
              <span
                className={`text-xs px-2.5 py-0.5 rounded-full font-semibold uppercase ${
                  review.status === 'lecturer_approved'
                    ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                    : review.status === 'overridden'
                    ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                    : 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/30'
                }`}
              >
                {review.status.replace('_', ' ')}
              </span>
            )}
          </div>

          {review ? (
            <div className="space-y-4">
              {/* Score Overview */}
              <div className="p-4 rounded-xl bg-black/30 border border-white/10 flex items-center justify-between">
                <div>
                  <span className="text-xs text-gray-400">AI Suggested Score:</span>
                  <div className="text-3xl font-extrabold text-indigo-400">
                    {review.ai_suggested_score} <span className="text-sm font-normal text-gray-400">/ 100</span>
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  <div>
                    <label className="block text-xs text-gray-400 mb-0.5">Final Faculty Mark</label>
                    <input
                      type="number"
                      min={0}
                      max={100}
                      step={0.5}
                      value={finalScoreInput}
                      onChange={(e) => setFinalScoreInput(e.target.value)}
                      className="w-24 bg-gray-900 border border-indigo-500/50 rounded-xl px-3 py-1.5 text-white font-bold text-lg text-center"
                    />
                  </div>
                </div>
              </div>

              {/* Rubric Breakdown */}
              {review.rubric_breakdown_json && (
                <div className="space-y-2">
                  <h4 className="text-xs font-bold text-gray-300 uppercase tracking-wider">
                    Rubric Criteria Evaluation
                  </h4>
                  <div className="space-y-2">
                    {review.rubric_breakdown_json.map((r, i) => (
                      <div
                        key={i}
                        className="p-3 rounded-xl bg-white/5 border border-white/5 flex justify-between items-start text-xs"
                      >
                        <div className="space-y-0.5">
                          <span className="font-semibold text-white">{r.criterion}</span>
                          <p className="text-gray-400">{r.comment}</p>
                        </div>
                        <span className="font-mono text-emerald-400 font-bold ml-3 flex-shrink-0">
                          {r.ai_points} / {r.max_points}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Code Analysis if applicable */}
              {review.code_analysis_json && (
                <div className="p-3.5 rounded-xl bg-gray-950/60 border border-indigo-500/20 text-xs space-y-1">
                  <div className="flex justify-between items-center text-indigo-300 font-bold">
                    <span>Code Complexity: {review.code_analysis_json.complexity_score}</span>
                    <span className="text-emerald-400 font-mono">
                      {review.code_analysis_json.syntax_valid ? 'Syntax Valid' : 'Syntax Warning'}
                    </span>
                  </div>
                  {review.code_analysis_json.style_warnings?.map((w: string, i: number) => (
                    <div key={i} className="text-gray-400">
                      • {w}
                    </div>
                  ))}
                </div>
              )}

              {/* Lecturer Feedback Editor */}
              <div className="space-y-1">
                <label className="block text-xs font-semibold text-gray-300">
                  Lecturer Feedback & Qualitative Commentary:
                </label>
                <textarea
                  rows={4}
                  value={lecturerFeedbackInput}
                  onChange={(e) => setLecturerFeedbackInput(e.target.value)}
                  className="w-full bg-black/40 border border-gray-700 rounded-xl p-3 text-xs text-white"
                />
              </div>

              {/* Finalize Button */}
              <button
                onClick={handleApproveOrOverride}
                disabled={isApproving}
                className="w-full bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white font-bold py-2.5 rounded-xl transition shadow flex items-center justify-center gap-2 text-sm"
              >
                {isApproving
                  ? 'Finalizing...'
                  : Number(finalScoreInput) !== review.ai_suggested_score
                  ? '⚡ Save Override & Finalize Marks'
                  : '✓ Approve AI Grade & Publish'}
              </button>
            </div>
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center text-gray-400 space-y-2 py-12 text-center">
              <span className="text-3xl">🤖</span>
              <p className="text-sm font-semibold text-white">No Evaluation Loaded</p>
              <p className="text-xs max-w-xs">
                Select a submission ID on the left and click "Run AI Grading" to generate automated rubric scores.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
export default AIGradingAssistant;
