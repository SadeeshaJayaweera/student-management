# 🎓 NSBM EduSphere — Advanced Student Management System

An enterprise-grade, production-level Student Management System engineered with a **Python FastAPI** backend, **Async SQLAlchemy** ORM, **ChromaDB + Gemini AI** (Grounded RAG + Model Context Protocol tools), and a **React 19 + TypeScript + Vite** frontend.

---

## 📸 Application Previews

### 🔐 Authentication & Student Experience
| Login Portal with Role Quick-Fill | Personalized Student Dashboard |
| :---: | :---: |
| ![Login Portal](screenshots/01_login.png) | ![Student Dashboard](screenshots/02_student_dashboard.png) |
| *Multi-role authentication supporting MFA, role-based redirection, and quick-fill demo access.* | *Real-time GPA tracker, course schedules, attendance thresholds, and notifications.* |

---

### 🤖 AI-Powered Academic Intelligence
| Automated Essay & Code Grading Assistant | AI Quiz & Assessment Question Generator |
| :---: | :---: |
| ![AI Grading Assistant](screenshots/08_ai_grading_assistant.png) | ![AI Quiz Generator](screenshots/09_ai_quiz_generator.png) |
| *Rubric-grounded evaluation for essays and code, confidence scoring, and lecturer override audits.* | *Instant quiz synthesis across difficulty tiers with bloom taxonomy alignments.* |

| Grounded Course RAG Knowledge Base | Socratic AI Teaching Assistant |
| :---: | :---: |
| ![Course RAG Architecture](screenshots/03_course_rag.png) | ![AI Teaching Assistant](screenshots/04_ai_teaching_assistant.png) |
| *Vector semantic search over course syllabi and lecture slides with citation verification.* | *Interactive Socratic tutor offering step-by-step guidance without revealing solutions.* |

---

### ⚙️ Extensibility & Operations Command
| Model Context Protocol (MCP) Console | Campus Operations Command Center |
| :---: | :---: |
| ![MCP Tools Console](screenshots/05_mcp_console.png) | ![Campus Operations Command](screenshots/10_campus_operations.png) |
| *Standardized MCP tool execution testbed for grades, library queries, and schedules.* | *Comprehensive facility booking, student accommodation, and shuttle fleet tracking.* |

---

### 📚 Campus Ecosystem & Student Life
| Modern Digital Library System | Sports, Athletics & Campus Clubs |
| :---: | :---: |
| ![Digital Library](screenshots/06_digital_library.png) | ![Sports and Clubs](screenshots/07_sports_and_clubs.png) |
| *Multi-category book discovery, real-time reservations, and automated borrow tracking.* | *Campus athletic events, club registrations, and fixture management.* |

---

## 🌟 Key Features

### ⚖️ Automated Essay & Code Grading Assistant (Latest)
- **Multi-Modal Evaluation Engine**: Evaluates both analytical essays and code implementations against predefined academic rubrics.
- **Rubric Criterion Breakdown**: Generates itemized scores across dimensions (Logic & Correctness, Architecture & Contract Compliance, Edge Cases, Code Style).
- **Confidence Scoring & Flagging**: Evaluates AI confidence levels and automatically flags borderline submissions for mandatory human review.
- **Human-in-the-Loop Moderation**: Allows course lecturers to review AI suggestions, adjust grades, add customized feedback, and approve final submissions.
- **Grading Audit Trail & Metrics**: Aggregates course-level statistics, lecturer override counts, and average score deltas for academic integrity.

### 🤖 Full-Stack AI Academic Suite
- **Grounded Course RAG (Retrieval-Augmented Generation)**: Vector knowledge base using ChromaDB and Google Gemini embeddings with automatic mock fallback.
- **Socratic AI Teaching Assistant**: Conversational tutor designed to guide students with probing questions and hints.
- **AI Quiz & Question Generator**: Synthesizes multiple-choice questions, code challenges, and conceptual prompts with instant answer explanations.
- **MCP (Model Context Protocol) Server**: Integrated agent tool execution for grade checks, library catalog searches, course schedules, and GPA calculation.

### 🏛️ Dedicated Portals & Campus Operations
1. **Student Portal**:
   - Live GPA tracker & graphical grade distribution
   - Course enrollments & semester schedule
   - Assignment tracker with direct submission modals
   - Real-time attendance monitoring with 80% threshold warnings
   - Exam & weekly timetable views
2. **Lecturer Portal**:
   - Course assignment & student roster management
   - AI-assisted grading center with human moderation
   - Submission grading center with granular rubric feedback
   - Comprehensive performance analytics & score distributions
3. **Campus Operations**:
   - **Hostel & Housing Management**: Room allocations, resident records, and maintenance requests.
   - **Transport & Shuttles**: Route mapping, stop schedules, and vehicle fleet tracking.
   - **Facility Booking**: Classroom, lab, and hall reservation workflows with conflict resolution.
4. **Digital Library**:
   - Searchable book catalog with multi-category filtering
   - Live borrowing, reservations, and fine calculations
5. **Sports & Athletic Clubs**:
   - Club discovery with category tags & membership limits
   - Upcoming campus sports & cultural events with 1-click registration
6. **Alumni Network & Hub**:
   - Global alumni directory with search & industry filters
   - Alumni experiences feed with likes and interactive tags
   - Mentorship connection request system
7. **Administration Panel**:
   - System-wide statistics & KPI metric tracking
   - Full user management (Student, Lecturer, Alumni, Admin) with instant enable/disable

---

## 🔐 Demo Credentials

| Role | Username | Password | Notes |
| :--- | :--- | :--- | :--- |
| **Admin** | `admin` | `Admin@123` | Full administrative control & campus operations |
| **Student** | `student01` | `Student@123` | CS 2nd Year Student (Sadeesha Perera) |
| **Lecturer** | `kperera` | `Lecturer@123` | Senior Lecturer (Dr. Kasun Perera) |
| **Alumni** | `alumni01` | `Alumni@123` | Tech Lead @ WSO2 (Ruwan Jayasinghe) |

---

## 🚀 Getting Started

### 1. Unified Single-Server Mode (Recommended)
```bash
./run.sh
```
Opens the app on `http://localhost:8000` (FastAPI serves both API and the pre-built React SPA).

### 2. Full Development Mode (Hot-Reloading Frontend & Backend)
```bash
./run.sh dev
```
- **React Frontend (Vite)**: `http://localhost:5173`
- **FastAPI Backend**: `http://localhost:8000`
- **Swagger Interactive API Docs**: `http://localhost:8000/docs`

---

## 🧪 Testing & Verification

The test suite covers unit and integration tests across all modules (136 tests):

```bash
./venv/bin/pytest
```

```
======================= 136 passed in 183s =======================
```

---

## 🛠️ Technology Stack

- **Backend**: Python 3.11+, FastAPI, Async SQLAlchemy, SQLite / PostgreSQL, Pydantic v2, Python-Jose (JWT), Passlib (Bcrypt), WebSockets
- **AI & RAG**: Google GenAI SDK (Gemini 2.0 Flash), ChromaDB, LangChain, Custom MCP Server
- **Frontend**: React 19, TypeScript, Vite, React Router v7, Axios, Chart.js / React-ChartJS-2, React Hot Toast, Tailwind CSS & Glassmorphism Design System
- **Testing**: Pytest, Pytest-Asyncio, AnyIO, HTTPX
