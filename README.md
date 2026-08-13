# 🎓 NSBM EduSphere — Advanced Student Management System

An enterprise-grade, production-level Student Management System engineered with a **Python FastAPI** backend, **Async SQLAlchemy** ORM, **ChromaDB + Gemini AI** (RAG + Model Context Protocol tools), and a **React 19 + TypeScript + Vite** frontend.

---

## 🌟 Key Features

### 🏛️ Dedicated Portals
1. **Student Portal**:
   - Live GPA tracker & graphical grade distribution
   - Course enrollments & semester schedule
   - Assignment tracker with direct submission modals
   - Real-time attendance monitoring with 80% threshold warnings
   - Exam & weekly timetable views
2. **Lecturer Portal**:
   - Course assignment & student roster management
   - Real-time submission grading center with feedback
   - Comprehensive performance analytics & score distributions
3. **Alumni Network & Hub**:
   - Global alumni directory with search & industry filters
   - Alumni experiences feed with likes and interactive tags
   - Mentorship connection request system
4. **Digital Library**:
   - Searchable book catalog with multi-category filtering
   - Live borrowing, reservations, and fine calculations
5. **Sports & Campus Clubs**:
   - Club discovery with category tags & membership limits
   - Upcoming campus sports & cultural events with 1-click registration
6. **News Portal**:
   - Featured article spotlight & categorized news stream
   - Full article view with interactive commenting system
7. **Administration Panel**:
   - System-wide statistics & KPI metric tracking
   - Full user management (Student, Lecturer, Alumni, Admin) with instant enable/disable

---

## 🤖 Advanced AI Capabilities (RAG + MCP)
- **RAG (Retrieval-Augmented Generation)**: Vector knowledge base using ChromaDB and Google Gemini embeddings with automatic mock fallback.
- **MCP (Model Context Protocol) Server**: Integrated agent tool execution for real-time grade checks, library catalog searches, course schedules, event lookups, and GPA calculation.
- **Server-Sent Events (SSE)**: Streaming responses in the AI Chat Assistant.

---

## 🔐 Demo Credentials

| Role | Username | Password | Notes |
| :--- | :--- | :--- | :--- |
| **Admin** | `admin` | `Admin@123` | Full administrative control |
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

## 🛠️ Technology Stack

- **Backend**: Python 3.11+, FastAPI, Async SQLAlchemy, SQLite / PostgreSQL, Pydantic v2, Python-Jose (JWT), Passlib (Bcrypt), WebSockets
- **AI & RAG**: Google GenAI SDK (Gemini 2.0 Flash), ChromaDB, LangChain, Custom MCP Server
- **Frontend**: React 19, TypeScript, Vite, React Router v7, Axios, Chart.js / React-ChartJS-2, React Hot Toast, Custom Glassmorphism CSS Design System
