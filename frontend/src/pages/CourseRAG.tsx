import React, { useState, useEffect } from 'react';
import api from '../api/client';
import { useAuth } from '../contexts/AuthContext';
import {
  CourseKnowledgeDocument,
  CourseRAGGroundedAnswer,
  CourseRAGSearchResult,
  CourseRAGAnalytics,
  Course,
} from '../types';
import toast from 'react-hot-toast';

export const CourseRAG: React.FC = () => {
  const { user } = useAuth();
  const [courses, setCourses] = useState<Course[]>([]);
  const [selectedCourseId, setSelectedCourseId] = useState<number | null>(null);
  const [activeTab, setActiveTab] = useState<'query' | 'documents' | 'search' | 'analytics'>('query');

  // Grounded Query State
  const [question, setQuestion] = useState('');
  const [groundedAnswer, setGroundedAnswer] = useState<CourseRAGGroundedAnswer | null>(null);
  const [isQuerying, setIsQuerying] = useState(false);
  const [feedbackRating, setFeedbackRating] = useState<number | null>(null);

  // Documents State
  const [documents, setDocuments] = useState<CourseKnowledgeDocument[]>([]);
  const [isLoadingDocs, setIsLoadingDocs] = useState(false);
  const [showIngestModal, setShowIngestModal] = useState(false);
  const [newDoc, setNewDoc] = useState({
    title: '',
    document_type: 'lecture_notes',
    source_citation: '',
    content: '',
  });

  // Search State
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<CourseRAGSearchResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);

  // Analytics State
  const [analytics, setAnalytics] = useState<CourseRAGAnalytics | null>(null);

  useEffect(() => {
    fetchCourses();
  }, []);

  useEffect(() => {
    if (selectedCourseId) {
      if (activeTab === 'documents') fetchDocuments(selectedCourseId);
      if (activeTab === 'analytics') fetchAnalytics(selectedCourseId);
    }
  }, [selectedCourseId, activeTab]);

  const fetchCourses = async () => {
    try {
      const res = await api.get('/courses');
      const data = res.data?.data || res.data || [];
      setCourses(data);
      if (data.length > 0) {
        setSelectedCourseId(data[0].id);
      }
    } catch (err) {
      toast.error('Failed to load courses');
    }
  };

  const fetchDocuments = async (courseId: number) => {
    setIsLoadingDocs(true);
    try {
      const res = await api.get(`/ai/rag/courses/${courseId}/documents`);
      setDocuments(res.data);
    } catch (err) {
      toast.error('Failed to load knowledge documents');
    } finally {
      setIsLoadingDocs(false);
    }
  };

  const fetchAnalytics = async (courseId: number) => {
    try {
      const res = await api.get(`/ai/rag/courses/${courseId}/analytics`);
      setAnalytics(res.data);
    } catch (err) {
      toast.error('Failed to load RAG analytics');
    }
  };

  const handleGroundedQuery = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedCourseId || !question.trim()) return;

    setIsQuerying(true);
    setFeedbackRating(null);
    try {
      const res = await api.post(`/ai/rag/courses/${selectedCourseId}/grounded-query`, {
        question: question.trim(),
      });
      setGroundedAnswer(res.data);
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Grounded query failed');
    } finally {
      setIsQuerying(false);
    }
  };

  const handleFeedback = async (rating: number) => {
    if (!groundedAnswer) return;
    try {
      await api.post(`/ai/rag/queries/${groundedAnswer.query_id}/feedback`, {
        rating,
        comment: 'User rated via Grounded RAG interface',
      });
      setFeedbackRating(rating);
      toast.success('Thank you for your feedback!');
    } catch (err) {
      toast.error('Failed to submit feedback');
    }
  };

  const handleIngestDocument = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedCourseId) return;

    try {
      await api.post(`/ai/rag/courses/${selectedCourseId}/documents`, newDoc);
      toast.success('Document successfully indexed and chunked');
      setShowIngestModal(false);
      setNewDoc({ title: '', document_type: 'lecture_notes', source_citation: '', content: '' });
      fetchDocuments(selectedCourseId);
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Document ingestion failed');
    }
  };

  const handleSemanticSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedCourseId || !searchQuery.trim()) return;

    setIsSearching(true);
    try {
      const res = await api.post(`/ai/rag/courses/${selectedCourseId}/search`, {
        query: searchQuery.trim(),
        top_k: 5,
      });
      setSearchResults(res.data);
    } catch (err) {
      toast.error('Semantic search failed');
    } finally {
      setIsSearching(false);
    }
  };

  const isFacultyOrAdmin = user?.role === 'lecturer' || user?.role === 'admin';

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 bg-white/10 backdrop-blur-md p-6 rounded-2xl border border-white/20 shadow-xl">
        <div>
          <h1 className="text-3xl font-extrabold text-white flex items-center gap-3">
            <span>📚</span> Grounded Course RAG
          </h1>
          <p className="text-gray-300 mt-1">
            Semantic syllabus retrieval with precise document, page, and line citation grounding
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

      {/* Tabs */}
      <div className="flex border-b border-white/10 space-x-2">
        <button
          onClick={() => setActiveTab('query')}
          className={`px-5 py-3 rounded-t-xl font-medium transition-all ${
            activeTab === 'query'
              ? 'bg-indigo-600/40 text-white border-t border-x border-indigo-400/30'
              : 'text-gray-400 hover:text-white hover:bg-white/5'
          }`}
        >
          🔍 Grounded Query
        </button>
        <button
          onClick={() => setActiveTab('documents')}
          className={`px-5 py-3 rounded-t-xl font-medium transition-all ${
            activeTab === 'documents'
              ? 'bg-indigo-600/40 text-white border-t border-x border-indigo-400/30'
              : 'text-gray-400 hover:text-white hover:bg-white/5'
          }`}
        >
          📄 Knowledge Documents
        </button>
        <button
          onClick={() => setActiveTab('search')}
          className={`px-5 py-3 rounded-t-xl font-medium transition-all ${
            activeTab === 'search'
              ? 'bg-indigo-600/40 text-white border-t border-x border-indigo-400/30'
              : 'text-gray-400 hover:text-white hover:bg-white/5'
          }`}
        >
          ⚡ Semantic Chunks
        </button>
        <button
          onClick={() => setActiveTab('analytics')}
          className={`px-5 py-3 rounded-t-xl font-medium transition-all ${
            activeTab === 'analytics'
              ? 'bg-indigo-600/40 text-white border-t border-x border-indigo-400/30'
              : 'text-gray-400 hover:text-white hover:bg-white/5'
          }`}
        >
          📊 RAG Analytics
        </button>
      </div>

      {/* Grounded Query Tab */}
      {activeTab === 'query' && (
        <div className="space-y-6">
          <div className="bg-white/5 backdrop-blur-md p-6 rounded-2xl border border-white/10 shadow-lg">
            <form onSubmit={handleGroundedQuery} className="space-y-4">
              <label className="block text-white font-semibold text-lg">
                Ask a syllabus or course question:
              </label>
              <div className="flex gap-3">
                <input
                  type="text"
                  placeholder="e.g. What are the key concepts of recursion discussed in Week 3?"
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  className="flex-1 bg-gray-900/60 border border-gray-700 text-white rounded-xl px-5 py-3 focus:ring-2 focus:ring-indigo-500 focus:outline-none placeholder-gray-500"
                />
                <button
                  type="submit"
                  disabled={isQuerying || !question.trim()}
                  className="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-semibold px-6 py-3 rounded-xl transition shadow-lg flex items-center gap-2"
                >
                  {isQuerying ? 'Searching...' : 'Ask AI'}
                </button>
              </div>
            </form>
          </div>

          {groundedAnswer && (
            <div className="bg-white/5 backdrop-blur-md p-6 rounded-2xl border border-white/10 shadow-lg space-y-6">
              <div className="flex justify-between items-center border-b border-white/10 pb-4">
                <div className="flex items-center gap-3">
                  <span className="text-xl">🤖</span>
                  <h3 className="text-lg font-bold text-white">Grounded Answer</h3>
                  {groundedAnswer.context_used ? (
                    <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                      Grounded in Course Materials
                    </span>
                  ) : (
                    <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-yellow-500/20 text-yellow-400 border border-yellow-500/30">
                      General Knowledge (No direct match)
                    </span>
                  )}
                </div>
                <span className="text-xs text-gray-400">
                  Latency: {groundedAnswer.latency_ms} ms
                </span>
              </div>

              <div className="text-gray-200 leading-relaxed whitespace-pre-line text-base">
                {groundedAnswer.answer}
              </div>

              {/* Citations Box */}
              {groundedAnswer.citations.length > 0 && (
                <div className="space-y-3 pt-4 border-t border-white/10">
                  <h4 className="text-sm font-semibold text-gray-300 uppercase tracking-wider">
                    Verified Source Citations
                  </h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {groundedAnswer.citations.map((c) => (
                      <div
                        key={c.citation_index}
                        className="p-4 rounded-xl bg-gray-900/60 border border-indigo-500/30 hover:border-indigo-400 transition"
                      >
                        <div className="flex items-center justify-between">
                          <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-indigo-600 text-white text-xs font-bold">
                            [{c.citation_index}]
                          </span>
                          <span className="text-xs text-indigo-300 font-mono">
                            Page {c.page} · Lines {c.lines}
                          </span>
                        </div>
                        <div className="text-sm font-semibold text-white mt-2">
                          {c.document_title}
                        </div>
                        {c.source && (
                          <div className="text-xs text-gray-400">{c.source}</div>
                        )}
                        <p className="text-xs text-gray-300 mt-2 bg-black/30 p-2 rounded border border-white/5 italic">
                          "{c.snippet}"
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Feedback Prompt */}
              <div className="flex items-center justify-between pt-4 border-t border-white/10">
                <span className="text-sm text-gray-400">Was this answer helpful and well-cited?</span>
                <div className="flex gap-2">
                  {[1, 2, 3, 4, 5].map((star) => (
                    <button
                      key={star}
                      onClick={() => handleFeedback(star)}
                      className={`text-xl transition-transform hover:scale-125 ${
                        feedbackRating && feedbackRating >= star
                          ? 'text-yellow-400'
                          : 'text-gray-600 hover:text-yellow-400'
                      }`}
                    >
                      ★
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Documents Tab */}
      {activeTab === 'documents' && (
        <div className="space-y-6">
          <div className="flex justify-between items-center">
            <h2 className="text-xl font-bold text-white">Indexed Course Materials</h2>
            {isFacultyOrAdmin && (
              <button
                onClick={() => setShowIngestModal(true)}
                className="bg-indigo-600 hover:bg-indigo-500 text-white font-semibold px-4 py-2 rounded-xl transition shadow flex items-center gap-2"
              >
                <span>➕</span> Ingest Document
              </button>
            )}
          </div>

          {isLoadingDocs ? (
            <div className="text-center py-12 text-gray-400">Loading documents...</div>
          ) : documents.length === 0 ? (
            <div className="text-center py-12 bg-white/5 rounded-2xl border border-white/10 text-gray-400">
              No knowledge documents indexed for this course yet.
            </div>
          ) : (
            <div className="overflow-x-auto bg-white/5 rounded-2xl border border-white/10">
              <table className="w-full text-left text-sm text-gray-300">
                <thead className="bg-white/10 text-gray-200 uppercase text-xs font-semibold">
                  <tr>
                    <th className="px-6 py-4">Title</th>
                    <th className="px-6 py-4">Type</th>
                    <th className="px-6 py-4">Citation Source</th>
                    <th className="px-6 py-4">Chunks</th>
                    <th className="px-6 py-4">Tokens</th>
                    <th className="px-6 py-4">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/10">
                  {documents.map((doc) => (
                    <tr key={doc.id} className="hover:bg-white/5 transition">
                      <td className="px-6 py-4 font-medium text-white">{doc.title}</td>
                      <td className="px-6 py-4 capitalize">{doc.document_type.replace('_', ' ')}</td>
                      <td className="px-6 py-4 text-xs font-mono text-indigo-300">{doc.source_citation || '—'}</td>
                      <td className="px-6 py-4">{doc.chunk_count}</td>
                      <td className="px-6 py-4">{doc.token_count}</td>
                      <td className="px-6 py-4">
                        <span className="px-2.5 py-1 rounded-full text-xs font-medium bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                          {doc.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Semantic Search Tab */}
      {activeTab === 'search' && (
        <div className="space-y-6">
          <div className="bg-white/5 backdrop-blur-md p-6 rounded-2xl border border-white/10 shadow-lg">
            <form onSubmit={handleSemanticSearch} className="flex gap-3">
              <input
                type="text"
                placeholder="Search raw chunks and semantic vectors..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="flex-1 bg-gray-900/60 border border-gray-700 text-white rounded-xl px-5 py-3 focus:ring-2 focus:ring-indigo-500 focus:outline-none placeholder-gray-500"
              />
              <button
                type="submit"
                disabled={isSearching || !searchQuery.trim()}
                className="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-semibold px-6 py-3 rounded-xl transition"
              >
                {isSearching ? 'Retrieving...' : 'Vector Search'}
              </button>
            </form>
          </div>

          <div className="space-y-4">
            {searchResults.map((res) => (
              <div
                key={res.chunk_id}
                className="p-5 rounded-2xl bg-white/5 border border-white/10 space-y-3"
              >
                <div className="flex justify-between items-center">
                  <span className="text-white font-bold">{res.document_title}</span>
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-gray-400">
                      Relevance: {(res.relevance_score * 100).toFixed(1)}%
                    </span>
                    <span className="text-xs font-mono text-indigo-300 bg-indigo-900/40 px-2.5 py-1 rounded-lg border border-indigo-500/20">
                      Page {res.page_number} · Lines {res.line_start}-{res.line_end}
                    </span>
                  </div>
                </div>
                <p className="text-sm text-gray-300 whitespace-pre-line bg-black/20 p-4 rounded-xl border border-white/5">
                  {res.content}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Analytics Tab */}
      {activeTab === 'analytics' && (
        <div className="space-y-6">
          {analytics ? (
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              <div className="bg-white/5 backdrop-blur-md p-6 rounded-2xl border border-white/10">
                <span className="text-gray-400 text-sm">Indexed Documents</span>
                <div className="text-3xl font-extrabold text-white mt-2">
                  {analytics.document_count}
                </div>
              </div>
              <div className="bg-white/5 backdrop-blur-md p-6 rounded-2xl border border-white/10">
                <span className="text-gray-400 text-sm">Vector Chunks</span>
                <div className="text-3xl font-extrabold text-white mt-2">
                  {analytics.chunk_count}
                </div>
              </div>
              <div className="bg-white/5 backdrop-blur-md p-6 rounded-2xl border border-white/10">
                <span className="text-gray-400 text-sm">Queries Processed</span>
                <div className="text-3xl font-extrabold text-white mt-2">
                  {analytics.query_count}
                </div>
              </div>
              <div className="bg-white/5 backdrop-blur-md p-6 rounded-2xl border border-white/10">
                <span className="text-gray-400 text-sm">Avg Latency</span>
                <div className="text-3xl font-extrabold text-indigo-400 mt-2">
                  {analytics.avg_latency_ms} ms
                </div>
              </div>
            </div>
          ) : (
            <div className="text-center py-12 text-gray-400">Loading analytics...</div>
          )}
        </div>
      )}

      {/* Ingest Document Modal */}
      {showIngestModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className="bg-gray-900 border border-white/20 rounded-2xl max-w-2xl w-full p-6 space-y-4 shadow-2xl">
            <h3 className="text-xl font-bold text-white">Ingest Knowledge Document</h3>
            <form onSubmit={handleIngestDocument} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">Title</label>
                <input
                  type="text"
                  required
                  value={newDoc.title}
                  onChange={(e) => setNewDoc({ ...newDoc, title: e.target.value })}
                  placeholder="e.g. Week 4: Dynamic Programming & Memoization"
                  className="w-full bg-black/40 border border-gray-700 rounded-xl px-4 py-2 text-white"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">Document Type</label>
                  <select
                    value={newDoc.document_type}
                    onChange={(e) => setNewDoc({ ...newDoc, document_type: e.target.value })}
                    className="w-full bg-black/40 border border-gray-700 rounded-xl px-4 py-2 text-white"
                  >
                    <option value="lecture_notes">Lecture Notes</option>
                    <option value="syllabus">Syllabus</option>
                    <option value="textbook_excerpt">Textbook Excerpt</option>
                    <option value="lab_sheet">Lab Sheet</option>
                    <option value="assignment_brief">Assignment Brief</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">Source Citation</label>
                  <input
                    type="text"
                    value={newDoc.source_citation}
                    onChange={(e) => setNewDoc({ ...newDoc, source_citation: e.target.value })}
                    placeholder="e.g. CS201 Module 2 Lecture Slides"
                    className="w-full bg-black/40 border border-gray-700 rounded-xl px-4 py-2 text-white"
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">Content</label>
                <textarea
                  rows={8}
                  required
                  value={newDoc.content}
                  onChange={(e) => setNewDoc({ ...newDoc, content: e.target.value })}
                  placeholder="Paste lecture notes or textbook material here..."
                  className="w-full bg-black/40 border border-gray-700 rounded-xl px-4 py-2 text-white"
                />
              </div>
              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowIngestModal(false)}
                  className="px-4 py-2 rounded-xl text-gray-400 hover:text-white"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="bg-indigo-600 hover:bg-indigo-500 text-white font-semibold px-5 py-2 rounded-xl"
                >
                  Index & Chunk
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
export default CourseRAG;
