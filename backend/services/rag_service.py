"""
NSBM EduSphere — AI Service with RAG (ChromaDB + LangChain + Gemini)
"""
import os
import asyncio
from typing import Optional, List, AsyncGenerator
from backend.config import settings

# Knowledge base documents for NSBM
NSBM_KNOWLEDGE_BASE = [
    {
        "id": "nsbm_overview",
        "content": """NSBM Green University is a leading private university in Sri Lanka located in Pitipana, Homagama. 
        Founded in 2007, NSBM offers undergraduate and postgraduate programs in Computing, Business, Engineering, 
        Science, Law, and Architecture. NSBM is affiliated with Plymouth University (UK) and Victoria University of Wellington (NZ).
        The university has over 10,000 students and 500+ academic staff."""
    },
    {
        "id": "academic_calendar",
        "content": """NSBM Academic Year 2025-2026:
        - Semester 1: September 2025 - January 2026
        - Semester 2: February 2026 - June 2026
        - Final Exams Semester 1: January 2026 (Week 14-16)
        - Final Exams Semester 2: June 2026 (Week 14-16)
        - Registration Deadline: First 2 weeks of each semester
        - Add/Drop Period: First week of semester"""
    },
    {
        "id": "grading_system",
        "content": """NSBM Grading System:
        A+ (90-100): 4.0 Grade Points - Exceptional
        A  (80-89):  4.0 Grade Points - Excellent  
        B+ (75-79):  3.5 Grade Points - Very Good
        B  (70-74):  3.0 Grade Points - Good
        C+ (65-69):  2.5 Grade Points - Above Average
        C  (60-64):  2.0 Grade Points - Average
        D  (55-59):  1.5 Grade Points - Pass
        F  (0-54):   0.0 Grade Points - Fail
        Minimum GPA to continue: 2.0. Dean's List: GPA 3.8+"""
    },
    {
        "id": "library_policy",
        "content": """NSBM Library Policies:
        - Students can borrow up to 5 books at a time
        - Loan period: 14 days (renewable once)
        - Fine for overdue books: LKR 5 per day per book
        - Library hours: Monday-Friday 8:00 AM - 8:00 PM, Saturday 9:00 AM - 5:00 PM
        - E-library access available 24/7 through the portal
        - Lost book replacement: 3x the book price
        - Reference books cannot be borrowed (reading room only)"""
    },
    {
        "id": "student_services",
        "content": """NSBM Student Services:
        - Career Guidance Center: Internship placement, CV writing, interview prep
        - Counseling Services: Free, confidential counseling for all students
        - Sports Facilities: Cricket ground, football field, badminton courts, gym
        - Cafeteria: Open 7:30 AM - 7:00 PM daily
        - Transportation: Bus service from Colombo, Kandy, Galle routes
        - Medical Center: First aid and basic healthcare
        - IT Help Desk: Room B001, Mon-Fri 8 AM - 5 PM"""
    },
    {
        "id": "faculty_computing",
        "content": """Faculty of Computing Programs:
        - BSc (Hons) Computer Science (3 years + optional 1 year Plymouth UK)
        - BSc (Hons) Information Technology
        - BSc (Hons) Software Engineering
        - BSc (Hons) Cyber Security
        - MSc Computer Science (1.5 years)
        - All programs accredited by IESL and BCS (UK)
        - Dedicated labs: AI Lab, Cybersecurity Lab, IoT Lab, Cloud Computing Lab"""
    },
    {
        "id": "faculty_business",
        "content": """Faculty of Business Programs:
        - BBA (Hons) Management
        - BBA (Hons) Finance
        - BBA (Hons) Marketing
        - BSc (Hons) Human Resource Management
        - BSc (Hons) Accounting & Finance
        - MBA (1.5 years, part-time available)
        - Programs recognized by CIMA, ACCA, CIM (UK)"""
    },
    {
        "id": "clubs_activities",
        "content": """NSBM Student Clubs & Activities:
        - IEEE Student Branch - Technical innovation, workshops, competitions
        - AIESEC NSBM - International exchange programs and leadership
        - Drama & Arts Society - Annual cultural festival (SOORYA)
        - Entrepreneur Club - Startup competitions, pitch days
        - Green Society - Environmental projects, tree planting
        - Coding Warriors - Competitive programming, hackathons
        - Sports: Cricket, Football, Basketball, Badminton, Swimming, Athletics
        Annual events: Freshers' Night, Sports Carnival, Grad Night, Career Fair"""
    },
    {
        "id": "fees_scholarships",
        "content": """NSBM Fees & Scholarships 2025:
        - BSc Computer Science: LKR 285,000/year
        - BBA: LKR 265,000/year
        - BSc Engineering: LKR 295,000/year
        Scholarships available:
        - Academic Excellence: 50% reduction for A/L National Merit students
        - Sports Excellence: 25% reduction for national-level athletes
        - Financial Need: Assessed individually, up to 40% reduction
        - Alumni Children: 10% reduction
        Payment plans: Semester-wise or per-credit-hour basis available"""
    },
    {
        "id": "exam_regulations",
        "content": """NSBM Examination Regulations:
        - Minimum 80% attendance required to sit for final exams
        - Medical certificate required for missed exams within 3 days
        - Medical exam: Scheduled within 2 weeks of original exam
        - Grade appeals: Within 7 days of result publication, fee: LKR 500
        - Academic dishonesty: Zero mark for the module + disciplinary action
        - Exam dress code: Smart casual (no shorts, slippers, or hats)
        - Mobile phones strictly prohibited in exam halls"""
    }
]


class RAGService:
    """Retrieval-Augmented Generation service using ChromaDB + Gemini"""

    def __init__(self):
        self._collection = None
        self._embeddings = None
        self._llm = None
        self._initialized = False

    async def initialize(self):
        """Initialize ChromaDB and Gemini"""
        if self._initialized:
            return

        try:
            import chromadb
            from chromadb.utils import embedding_functions

            # Initialize ChromaDB
            client = chromadb.PersistentClient(path=settings.chroma_persist_dir)

            # Use default embedding function (sentence-transformers)
            ef = embedding_functions.DefaultEmbeddingFunction()

            # Get or create collection
            self._collection = client.get_or_create_collection(
                name="nsbm_knowledge",
                embedding_function=ef,
                metadata={"description": "NSBM University Knowledge Base"}
            )

            # Seed knowledge base if empty
            if self._collection.count() == 0:
                await self._seed_knowledge_base()

            # Initialize Gemini LLM
            if settings.google_api_key and settings.ai_enabled:
                import google.generativeai as genai
                genai.configure(api_key=settings.google_api_key)
                self._llm = genai.GenerativeModel(settings.gemini_model)

            self._initialized = True
            print("✅ RAG Service initialized with ChromaDB and Gemini")

        except Exception as e:
            print(f"⚠️  RAG Service init warning: {e}. Using mock mode.")
            self._initialized = True

    async def _seed_knowledge_base(self):
        """Seed the vector DB with NSBM knowledge"""
        if not self._collection:
            return
        try:
            self._collection.upsert(
                ids=[doc["id"] for doc in NSBM_KNOWLEDGE_BASE],
                documents=[doc["content"] for doc in NSBM_KNOWLEDGE_BASE],
                metadatas=[{"source": doc["id"]} for doc in NSBM_KNOWLEDGE_BASE]
            )
            print(f"✅ Seeded {len(NSBM_KNOWLEDGE_BASE)} documents to ChromaDB")
        except Exception as e:
            print(f"⚠️  Knowledge base seeding: {e}")

    def _retrieve_context(self, query: str, n_results: int = 3) -> str:
        """Retrieve relevant context from ChromaDB"""
        if not self._collection:
            return ""
        try:
            results = self._collection.query(
                query_texts=[query],
                n_results=min(n_results, self._collection.count())
            )
            if results and results["documents"]:
                return "\n\n".join(results["documents"][0])
            return ""
        except Exception as e:
            return ""

    async def query(self, question: str, context_hint: str = "") -> dict:
        """Query the RAG system and return answer with sources"""
        if not self._initialized:
            await self.initialize()

        # Retrieve relevant context
        retrieved_context = self._retrieve_context(question)

        # Build prompt
        system_prompt = """You are EduSphere AI, the intelligent assistant for NSBM Green University's EduSphere portal.
You help students, lecturers, and alumni with university-related questions.
Be friendly, helpful, and concise. Use the provided context to give accurate answers.
If information isn't in the context, provide a helpful general response."""

        full_prompt = f"""{system_prompt}

UNIVERSITY KNOWLEDGE BASE:
{retrieved_context}

USER QUESTION: {question}

Please provide a helpful, accurate response:"""

        if self._llm:
            try:
                response = self._llm.generate_content(full_prompt)
                answer = response.text
            except Exception as e:
                answer = self._mock_response(question, retrieved_context)
        else:
            answer = self._mock_response(question, retrieved_context)

        return {
            "answer": answer,
            "sources": [doc["id"] for doc in NSBM_KNOWLEDGE_BASE if
                       any(kw in question.lower() for kw in doc["id"].split("_"))],
            "context_used": bool(retrieved_context)
        }

    async def stream_query(self, question: str) -> AsyncGenerator[str, None]:
        """Stream responses for chat-like experience"""
        if not self._initialized:
            await self.initialize()

        retrieved_context = self._retrieve_context(question)

        if self._llm:
            try:
                prompt = f"""You are EduSphere AI for NSBM Green University.

Context: {retrieved_context}

Question: {question}

Answer helpfully and concisely:"""
                response = self._llm.generate_content(prompt, stream=True)
                for chunk in response:
                    if chunk.text:
                        yield chunk.text
                        await asyncio.sleep(0.01)
                return
            except Exception as e:
                pass

        # Mock streaming
        mock = self._mock_response(question, retrieved_context)
        words = mock.split()
        for i, word in enumerate(words):
            yield word + (" " if i < len(words) - 1 else "")
            await asyncio.sleep(0.05)

    def _mock_response(self, question: str, context: str) -> str:
        """Intelligent mock responses when Gemini is not configured"""
        q = question.lower()

        if context:
            # Extract relevant sentence from context
            sentences = context.split(".")
            relevant = [s.strip() for s in sentences if any(
                word in s.lower() for word in q.split() if len(word) > 3
            )]
            if relevant:
                return f"Based on NSBM's information: {relevant[0]}. {relevant[1] if len(relevant) > 1 else ''}\n\nFor more details, please contact the relevant department or visit the admin office."

        responses = {
            "library": "📚 The NSBM Library is open Monday-Friday 8AM-8PM, Saturday 9AM-5PM. You can borrow up to 5 books for 14 days. Fine: LKR 5/day for overdue books.",
            "gpa": "📊 NSBM uses a 4.0 GPA scale. A+ = 4.0, A = 4.0, B+ = 3.5, B = 3.0, C+ = 2.5, C = 2.0, D = 1.5, F = 0.0. Minimum GPA to continue is 2.0.",
            "exam": "📝 You need 80% attendance to sit for finals. Medical certificates must be submitted within 3 days for missed exams. Grade appeals are within 7 days.",
            "scholarship": "🎓 NSBM offers Academic Excellence (50%), Sports Excellence (25%), and Financial Need scholarships (up to 40% reduction).",
            "fee": "💰 BSc Computing: LKR 285,000/year, BBA: LKR 265,000/year, Engineering: LKR 295,000/year. Semester-wise payment available.",
            "club": "⚽ NSBM has 8+ clubs including IEEE, AIESEC, Drama Society, Coding Warriors, and sports teams. Join through the Sports & Clubs portal!",
            "career": "💼 The Career Guidance Center offers internship placement, CV workshops, and interview preparation. Contact career@nsbm.ac.lk.",
        }
        for key, response in responses.items():
            if key in q:
                return response

        return f"""Hello! I'm EduSphere AI, your NSBM University assistant! 🎓

I can help you with:
• 📚 **Library** - Book availability, borrowing rules, e-resources
• 📊 **Academics** - GPA, grades, course information, exam schedules
• 🎓 **Admissions** - Programs, fees, scholarships
• ⚽ **Campus Life** - Clubs, sports, events, facilities
• 📋 **Regulations** - Attendance policies, exam rules, appeals

Your question: "{question}"

For specific information, please contact:
- Student Services: +94 11 544 5000
- Email: info@nsbm.ac.lk
- Website: www.nsbm.ac.lk

💡 **Tip:** Configure your Gemini API key in `.env` for AI-powered responses!"""

    async def add_document(self, doc_id: str, content: str, metadata: dict = None):
        """Add a document to the knowledge base"""
        if not self._initialized:
            await self.initialize()
        if self._collection:
            self._collection.upsert(
                ids=[doc_id],
                documents=[content],
                metadatas=[metadata or {}]
            )


# Global RAG service instance
rag_service = RAGService()
