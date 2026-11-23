import React, { useState, useEffect } from 'react';
import api from '../api/client';
import { useAuth } from '../contexts/AuthContext';
import {
  AIQuizGenerationJob,
  AIGeneratedQuestion,
  Course,
} from '../types';
import toast from 'react-hot-toast';

export const AIQuizGenerator: React.FC = () => {
  const { user } = useAuth();
  const [courses, setCourses] = useState<Course[]>([]);
  const [selectedCourseId, setSelectedCourseId] = useState<number | null>(null);

  // Form
  const [title, setTitle] = useState('Mid-Term Concept Quiz');
  const [sourceText, setSourceText] = useState('');
  const [bloomsLevel, setBloomsLevel] = useState('understand');
  const [difficulty, setDifficulty] = useState('medium');
  const [questionCount, setQuestionCount] = useState(3);
  const [types, setTypes] = useState<string[]>(['multiple_choice', 'short_answer', 'code_analysis']);
  const [isGenerating, setIsGenerating] = useState(false);

  // Current Job & Questions
  const [currentJob, setCurrentJob] = useState<AIQuizGenerationJob | null>(null);
  const [isPublishing, setIsPublishing] = useState(false);

  useEffect(() => {
    fetchCourses();
  }, []);

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

  const toggleType = (t: string) => {
    setTypes((prev) =>
      prev.includes(t) ? prev.filter((x) => x !== t) : [...prev, t]
    );
  };

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedCourseId || !sourceText.trim()) {
      toast.error('Please enter course lecture notes or syllabus excerpt');
      return;
    }
    if (types.length === 0) {
      toast.error('Please select at least one question type');
      return;
    }

    setIsGenerating(true);
    try {
      const res = await api.post('/ai/quiz-generation/generate', {
        course_id: selectedCourseId,
        title,
        source_text: sourceText.trim(),
        blooms_level: bloomsLevel,
        difficulty,
        question_count: questionCount,
        question_types: types,
      });
      setCurrentJob(res.data);
      toast.success('Successfully generated quiz items with Bloom’s taxonomy rubrics!');
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Question generation failed');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleApprove = async (questionId: number) => {
    try {
      await api.post(`/ai/quiz-generation/questions/${questionId}/approve`);
      toast.success('Exported to Course Question Bank');
      setCurrentJob((prev) =>
        prev
          ? {
              ...prev,
              questions: prev.questions.map((q) =>
                q.id === questionId ? { ...q, is_approved: true } : q
              ),
            }
          : prev
      );
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Approval failed');
    }
  };

  const handlePublishQuiz = async () => {
    if (!currentJob) return;
    setIsPublishing(true);
    try {
      const res = await api.post(`/ai/quiz-generation/jobs/${currentJob.id}/publish-quiz`, {
        title: currentJob.title,
        time_limit_minutes: 30,
      });
      toast.success(`Published as active Quiz: ${res.data.title}`);
      // Mark all questions as approved
      setCurrentJob((prev) =>
        prev
          ? {
              ...prev,
              questions: prev.questions.map((q) => ({ ...q, is_approved: true })),
            }
          : prev
      );
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to publish quiz');
    } finally {
      setIsPublishing(false);
    }
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 bg-white/10 backdrop-blur-md p-6 rounded-2xl border border-white/20 shadow-xl">
        <div>
          <h1 className="text-3xl font-extrabold text-white flex items-center gap-3">
            <span>📝</span> AI Quiz & Question Generator
          </h1>
          <p className="text-gray-300 mt-1">
            Bloom's taxonomy item synthesis, distractor rationales, code analysis tasks & automated rubric design
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

      {/* Generator Form */}
      <div className="bg-white/5 backdrop-blur-md p-6 rounded-2xl border border-white/10 shadow-xl space-y-5">
        <h2 className="text-xl font-bold text-white flex items-center gap-2">
          <span>⚙️</span> Assessment Parameters
        </h2>

        <form onSubmit={handleGenerate} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">Quiz Title</label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="e.g. Week 4 Trees & Graph Algorithms"
                className="w-full bg-black/40 border border-gray-700 rounded-xl px-4 py-2.5 text-white"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">Bloom's Taxonomy Level</label>
              <select
                value={bloomsLevel}
                onChange={(e) => setBloomsLevel(e.target.value)}
                className="w-full bg-black/40 border border-gray-700 rounded-xl px-4 py-2.5 text-white capitalize"
              >
                <option value="remember">Remember (Knowledge recall)</option>
                <option value="understand">Understand (Comprehension & summary)</option>
                <option value="apply">Apply (Practical scenario)</option>
                <option value="analyze">Analyze (Complexity & structure)</option>
                <option value="evaluate">Evaluate (Critique & trade-offs)</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">Difficulty</label>
              <select
                value={difficulty}
                onChange={(e) => setDifficulty(e.target.value)}
                className="w-full bg-black/40 border border-gray-700 rounded-xl px-4 py-2.5 text-white capitalize"
              >
                <option value="easy">Easy (Foundational)</option>
                <option value="medium">Medium (Standard)</option>
                <option value="hard">Hard (Advanced Rigor)</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">Questions Count</label>
              <input
                type="number"
                min={1}
                max={10}
                value={questionCount}
                onChange={(e) => setQuestionCount(Number(e.target.value))}
                className="w-full bg-black/40 border border-gray-700 rounded-xl px-4 py-2.5 text-white"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">Question Formats</label>
            <div className="flex flex-wrap gap-4">
              <label className="flex items-center gap-2 text-sm text-gray-200 cursor-pointer">
                <input
                  type="checkbox"
                  checked={types.includes('multiple_choice')}
                  onChange={() => toggleType('multiple_choice')}
                  className="rounded border-gray-700 text-indigo-600 focus:ring-indigo-500"
                />
                Multiple Choice (MCQ with Distractors)
              </label>
              <label className="flex items-center gap-2 text-sm text-gray-200 cursor-pointer">
                <input
                  type="checkbox"
                  checked={types.includes('code_analysis')}
                  onChange={() => toggleType('code_analysis')}
                  className="rounded border-gray-700 text-indigo-600 focus:ring-indigo-500"
                />
                Code Analysis & Bug Finding
              </label>
              <label className="flex items-center gap-2 text-sm text-gray-200 cursor-pointer">
                <input
                  type="checkbox"
                  checked={types.includes('short_answer')}
                  onChange={() => toggleType('short_answer')}
                  className="rounded border-gray-700 text-indigo-600 focus:ring-indigo-500"
                />
                Short Answer & Conceptual
              </label>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">
              Source Lecture Notes / Textbook Material
            </label>
            <textarea
              rows={6}
              required
              value={sourceText}
              onChange={(e) => setSourceText(e.target.value)}
              placeholder="Paste lecture notes, slide transcripts, or textbook chapters here to synthesize questions from..."
              className="w-full bg-black/40 border border-gray-700 rounded-xl px-4 py-3 text-white placeholder-gray-500 text-sm focus:ring-2 focus:ring-indigo-500 focus:outline-none"
            />
          </div>

          <div className="flex justify-end pt-2">
            <button
              type="submit"
              disabled={isGenerating || !sourceText.trim()}
              className="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-semibold px-6 py-3 rounded-xl transition shadow-lg flex items-center gap-2"
            >
              {isGenerating ? 'Synthesizing Questions...' : '🚀 Generate Assessment Items'}
            </button>
          </div>
        </form>
      </div>

      {/* Generated Questions Deck */}
      {currentJob && (
        <div className="space-y-6">
          <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 bg-indigo-950/40 border border-indigo-500/30 p-5 rounded-2xl">
            <div>
              <h3 className="text-xl font-bold text-white flex items-center gap-2">
                <span>🎯</span> {currentJob.title}
              </h3>
              <div className="flex items-center gap-2 text-xs text-indigo-300 mt-1">
                <span className="capitalize">Bloom's: {currentJob.blooms_level}</span>
                <span>·</span>
                <span className="capitalize">Difficulty: {currentJob.difficulty}</span>
                <span>·</span>
                <span>{currentJob.questions.length} Items Generated</span>
              </div>
            </div>

            <button
              onClick={handlePublishQuiz}
              disabled={isPublishing}
              className="bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white font-bold px-6 py-2.5 rounded-xl transition shadow flex items-center gap-2"
            >
              {isPublishing ? 'Publishing...' : '🚀 Publish All as Active Quiz'}
            </button>
          </div>

          {/* Question Cards */}
          <div className="space-y-5">
            {currentJob.questions.map((q, idx) => (
              <div
                key={q.id}
                className="bg-white/5 backdrop-blur-md rounded-2xl border border-white/10 p-6 space-y-4 shadow-lg"
              >
                <div className="flex justify-between items-start">
                  <div className="flex items-center gap-3">
                    <span className="inline-flex items-center justify-center w-8 h-8 rounded-xl bg-indigo-600 text-white font-bold text-sm">
                      {idx + 1}
                    </span>
                    <span className="text-xs uppercase font-mono px-3 py-1 rounded-full bg-white/10 text-indigo-300">
                      {q.question_type.replace('_', ' ')}
                    </span>
                  </div>

                  {q.is_approved ? (
                    <span className="text-xs font-semibold px-3 py-1 rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 flex items-center gap-1">
                      <span>✓</span> Added to Question Bank
                    </span>
                  ) : (
                    <button
                      onClick={() => handleApprove(q.id)}
                      className="text-xs font-semibold px-4 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white transition shadow"
                    >
                      ➕ Approve & Export
                    </button>
                  )}
                </div>

                <div className="text-gray-100 font-medium text-base whitespace-pre-line leading-relaxed">
                  {q.prompt}
                </div>

                {/* MCQ Options */}
                {q.options && (
                  <div className="space-y-2 pt-2">
                    {q.options.map((opt) => (
                      <div
                        key={opt.id}
                        className={`p-3 rounded-xl border text-sm flex items-center gap-3 ${
                          opt.id === q.correct_answer
                            ? 'bg-emerald-950/40 border-emerald-500/50 text-emerald-200 font-semibold'
                            : 'bg-black/20 border-white/5 text-gray-300'
                        }`}
                      >
                        <span className="font-bold font-mono px-2 py-0.5 rounded bg-white/10">
                          {opt.id}
                        </span>
                        <span>{opt.text}</span>
                        {opt.id === q.correct_answer && (
                          <span className="ml-auto text-xs text-emerald-400 font-mono">
                            Correct Answer
                          </span>
                        )}
                      </div>
                    ))}
                  </div>
                )}

                {/* Distractor Rationale / Explanation */}
                {q.explanation && (
                  <div className="p-3.5 rounded-xl bg-black/30 border border-white/5 text-xs text-gray-300 leading-relaxed">
                    <span className="font-bold text-indigo-300 block mb-1">
                      💡 Pedagogical Rationale & Distractor Breakdown:
                    </span>
                    {q.explanation}
                  </div>
                )}

                {/* Rubric Guide for Short Answer / Code Analysis */}
                {q.rubric_guide && (
                  <div className="p-4 rounded-xl bg-indigo-950/30 border border-indigo-500/20 space-y-2 text-xs">
                    <div className="flex justify-between items-center text-indigo-300 font-bold uppercase tracking-wider">
                      <span>Grading Rubric Guide</span>
                      <span>Total: {q.rubric_guide.max_points} pts</span>
                    </div>
                    <div className="divide-y divide-white/5">
                      {q.rubric_guide.criteria.map((c, i) => (
                        <div key={i} className="py-1.5 flex justify-between text-gray-300">
                          <span>{c.criterion}</span>
                          <span className="font-mono text-emerald-400 font-semibold">
                            {c.points} pts
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
export default AIQuizGenerator;
