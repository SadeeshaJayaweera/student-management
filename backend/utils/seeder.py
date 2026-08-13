"""
NSBM EduSphere — Database Seeder
Seeds realistic demo data for all portals
"""
import asyncio
import random
from datetime import date, datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from backend.database import AsyncSessionLocal, init_db
from backend.models import (
    User, UserRole, Student, Lecturer, Alumni, AlumniExperience,
    Course, Enrollment, Grade, Attendance, AttendanceStatus, Assignment,
    Book, BookStatus, BorrowRecord, BorrowStatus, Club, ClubCategory,
    ClubMembership, ClubEvent, News, NewsCategory, Notification
)
from backend.utils.security import hash_password


FACULTIES = {
    "Faculty of Computing": {
        "departments": ["Computer Science", "Information Technology", "Software Engineering", "Cyber Security"],
        "programs": ["BSc Computer Science", "BSc IT", "BSc Software Engineering", "BSc Cyber Security"]
    },
    "Faculty of Business": {
        "departments": ["Management", "Finance", "Marketing", "HRM"],
        "programs": ["BBA Management", "BBA Finance", "BBA Marketing", "BSc HRM"]
    },
    "Faculty of Engineering": {
        "departments": ["Civil", "Electrical", "Mechanical", "Electronic"],
        "programs": ["BSc Civil Engineering", "BSc Electrical Engineering", "BSc Mechanical Engineering", "BSc Electronic Engineering"]
    }
}

FIRST_NAMES = ["Ashan", "Dilshan", "Kavitha", "Nimasha", "Thilina", "Sachini", "Pradeep", "Manasha",
               "Hiruni", "Ravindu", "Chamara", "Nishani", "Tharindu", "Sadeesha", "Amara", "Kasun",
               "Isuru", "Dhanushka", "Madhawa", "Sithara", "Chamath", "Ruwini", "Lahiru", "Yashini"]
LAST_NAMES = ["Jayaweera", "Fernando", "Silva", "Perera", "Gunawardena", "Bandara", "Wickramasinghe",
              "Rajapaksha", "Mendis", "Herath", "Senanayake", "Dissanayake", "Liyanage", "Amarasinghe"]


def random_name():
    return f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"


async def seed_database():
    """Main seeder function"""
    print("🌱 Initializing database...")
    await init_db()

    async with AsyncSessionLocal() as db:
        # Check if already seeded
        result = await db.execute(select(func.count(User.id)))
        count = result.scalar()
        if count > 0:
            print("✅ Database already seeded. Skipping.")
            return

        print("🌱 Seeding users and profiles...")

        # ── Admin ──────────────────────────────────────────────────────────
        admin = User(
            email="admin@nsbm.ac.lk",
            username="admin",
            hashed_password=hash_password("Admin@123"),
            full_name="System Administrator",
            role=UserRole.ADMIN,
            is_active=True,
            is_verified=True,
        )
        db.add(admin)
        await db.flush()

        # ── Lecturers ──────────────────────────────────────────────────────
        lecturers = []
        lecturer_data = [
            ("Dr. Kamal Perera", "kperera", "kperera@nsbm.ac.lk", "Faculty of Computing", "Computer Science",
             "Artificial Intelligence & Machine Learning", "PhD Computer Science, University of Colombo"),
            ("Prof. Sunanda Fernando", "sfernando", "sfernando@nsbm.ac.lk", "Faculty of Computing", "Software Engineering",
             "Software Architecture & DevOps", "PhD Software Engineering, University of Kelaniya"),
            ("Dr. Malika Silva", "msilva", "msilva@nsbm.ac.lk", "Faculty of Business", "Finance",
             "Corporate Finance & Investments", "PhD Finance, University of Sri Jayewardenepura"),
            ("Dr. Roshan Bandara", "rbandara", "rbandara@nsbm.ac.lk", "Faculty of Engineering", "Civil",
             "Structural Engineering", "PhD Civil Engineering, University of Moratuwa"),
            ("Ms. Chamari Wickramasinghe", "cwickrama", "cwickrama@nsbm.ac.lk", "Faculty of Computing", "Information Technology",
             "Database Systems & Cloud Computing", "MSc IT, University of Colombo"),
        ]
        for name, uname, email, faculty, dept, spec, qual in lecturer_data:
            user = User(
                email=email, username=uname,
                hashed_password=hash_password("Lecturer@123"),
                full_name=name, role=UserRole.LECTURER,
                is_active=True, is_verified=True
            )
            db.add(user)
            await db.flush()
            lec_id = f"LEC{str(user.id).zfill(4)}"
            lecturer = Lecturer(
                user_id=user.id, lecturer_id=lec_id,
                faculty=faculty, department=dept,
                specialization=spec, qualification=qual,
                office_location=f"Block {'ABCDE'[lecturers.__len__()]}, Room {random.randint(100, 399)}",
                office_hours={"monday": "09:00-11:00", "wednesday": "14:00-16:00", "friday": "10:00-12:00"},
                bio=f"Dr. {name.split()[-1]} is a dedicated academic with extensive research experience in {spec}.",
                publications=random.randint(5, 30),
                joined_date=date(random.randint(2010, 2022), random.randint(1, 12), random.randint(1, 28))
            )
            db.add(lecturer)
            await db.flush()
            lecturers.append(lecturer)

        # ── Courses ────────────────────────────────────────────────────────
        print("📚 Seeding courses...")
        courses_data = [
            ("CS101", "Introduction to Programming", "Faculty of Computing", "Computer Science", 1, 1, 3, lecturers[0].id),
            ("CS201", "Data Structures & Algorithms", "Faculty of Computing", "Computer Science", 2, 1, 3, lecturers[0].id),
            ("CS301", "Machine Learning Fundamentals", "Faculty of Computing", "Computer Science", 3, 1, 3, lecturers[0].id),
            ("SE101", "Software Engineering Principles", "Faculty of Computing", "Software Engineering", 1, 1, 3, lecturers[1].id),
            ("SE201", "Web Application Development", "Faculty of Computing", "Software Engineering", 2, 1, 3, lecturers[1].id),
            ("IT101", "Database Management Systems", "Faculty of Computing", "Information Technology", 1, 1, 3, lecturers[4].id),
            ("IT201", "Cloud Computing", "Faculty of Computing", "Information Technology", 2, 2, 3, lecturers[4].id),
            ("BUS101", "Principles of Management", "Faculty of Business", "Management", 1, 1, 3, lecturers[2].id),
            ("FIN201", "Corporate Finance", "Faculty of Business", "Finance", 2, 1, 3, lecturers[2].id),
            ("CE101", "Structural Analysis", "Faculty of Engineering", "Civil", 1, 1, 3, lecturers[3].id),
        ]
        courses = []
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        times = ["08:00", "09:00", "10:00", "11:00", "13:00", "14:00", "15:00"]
        rooms = ["A101", "A202", "B103", "B204", "C105", "C206", "D107"]
        for code, title, faculty, dept, yr, sem, creds, lid in courses_data:
            c = Course(
                course_code=code, title=title, faculty=faculty,
                department=dept, year=yr, semester=sem, credits=creds,
                lecturer_id=lid, max_students=60, is_active=True,
                description=f"This course covers essential topics in {title.lower()} with hands-on practical sessions.",
                schedule={"day": random.choice(days), "time": random.choice(times), "room": random.choice(rooms)}
            )
            db.add(c)
            courses.append(c)
        await db.flush()

        # ── Students ───────────────────────────────────────────────────────
        print("🎓 Seeding students...")
        students = []
        student_users = []
        for i in range(1, 21):
            name = random_name()
            uname = f"student{i:02d}"
            faculty_name = random.choice(list(FACULTIES.keys()))
            faculty_info = FACULTIES[faculty_name]
            dept_idx = random.randint(0, len(faculty_info["departments"]) - 1)
            user = User(
                email=f"{uname}@students.nsbm.ac.lk",
                username=uname,
                hashed_password=hash_password("Student@123"),
                full_name=name, role=UserRole.STUDENT,
                is_active=True, is_verified=True,
                phone=f"+94 7{random.randint(0,9)} {random.randint(1000000,9999999)}"
            )
            db.add(user)
            await db.flush()
            yr = random.randint(1, 4)
            stu = Student(
                user_id=user.id,
                student_id=f"NSBM/{yr+2019}/CS/{str(i).zfill(4)}",
                faculty=faculty_name,
                department=faculty_info["departments"][dept_idx],
                program=faculty_info["programs"][dept_idx],
                year_of_study=yr, semester=random.randint(1, 2),
                gpa=round(random.uniform(2.0, 4.0), 2),
                credits_earned=random.randint(10, 120),
                enrollment_date=date(2019 + yr, 9, 1),
                expected_graduation=date(2023 + yr, 6, 30),
                address=f"No. {random.randint(1,99)}, {random.choice(['Galle Rd', 'Kandy Rd', 'Negombo Rd'])}, Colombo",
                scholarship=random.random() < 0.2
            )
            db.add(stu)
            await db.flush()
            students.append(stu)
            student_users.append(user)

        # ── Enrollments & Grades ───────────────────────────────────────────
        print("📊 Seeding enrollments and grades...")
        for stu in students:
            # Enroll in 3-5 courses
            selected_courses = random.sample(courses, min(4, len(courses)))
            for c in selected_courses:
                enroll = Enrollment(student_id=stu.id, course_id=c.id, status="active")
                db.add(enroll)
                await db.flush()
                midterm = round(random.uniform(40, 100), 1)
                final = round(random.uniform(40, 100), 1)
                asn_avg = round(random.uniform(50, 100), 1)
                total = round(midterm * 0.3 + final * 0.5 + asn_avg * 0.2, 1)
                letter = "A+" if total >= 90 else "A" if total >= 80 else "B+" if total >= 75 else "B" if total >= 70 else "C+" if total >= 65 else "C" if total >= 60 else "D" if total >= 55 else "F"
                gp = 4.0 if total >= 90 else 4.0 if total >= 80 else 3.5 if total >= 75 else 3.0 if total >= 70 else 2.5 if total >= 65 else 2.0 if total >= 60 else 1.5 if total >= 55 else 0.0
                grade = Grade(
                    student_id=stu.id, course_id=c.id,
                    midterm=midterm, final=final, assignments_avg=asn_avg,
                    total=total, letter_grade=letter, grade_points=gp
                )
                db.add(grade)
                # Attendance
                for days_ago in range(60, 0, -7):
                    att_date = date.today() - timedelta(days=days_ago)
                    status = random.choices(
                        [AttendanceStatus.PRESENT, AttendanceStatus.ABSENT, AttendanceStatus.LATE],
                        weights=[0.85, 0.10, 0.05]
                    )[0]
                    att = Attendance(student_id=stu.id, course_id=c.id, date=att_date, status=status)
                    db.add(att)

        # ── Assignments ────────────────────────────────────────────────────
        print("📝 Seeding assignments...")
        for c in courses[:5]:
            for a_num in range(1, 4):
                asn = Assignment(
                    course_id=c.id,
                    title=f"Assignment {a_num}: {c.title}",
                    description=f"Complete the following tasks related to {c.title}. Submit via the portal.",
                    due_date=datetime.now() + timedelta(days=random.randint(3, 21)),
                    max_marks=100.0,
                    assignment_type=random.choice(["assignment", "quiz", "project"])
                )
                db.add(asn)

        # ── Alumni ─────────────────────────────────────────────────────────
        print("🎓 Seeding alumni...")
        alumni_list = []
        industries = ["Technology", "Finance", "Healthcare", "Education", "Engineering", "Consulting", "Startups"]
        companies = ["WSO2", "IFS", "Dialog", "John Keells", "LOLC", "Virtusa", "99X Technology", "Google", "Microsoft"]
        positions = ["Software Engineer", "Senior Developer", "Product Manager", "Data Scientist", "DevOps Engineer",
                     "Tech Lead", "CTO", "Entrepreneur", "Business Analyst"]
        for i in range(1, 11):
            name = random_name()
            uname = f"alumni{i:02d}"
            user = User(
                email=f"{uname}@alumni.nsbm.ac.lk",
                username=uname,
                hashed_password=hash_password("Alumni@123"),
                full_name=name, role=UserRole.ALUMNI,
                is_active=True, is_verified=True
            )
            db.add(user)
            await db.flush()
            al = Alumni(
                user_id=user.id,
                alumni_id=f"ALU{str(i).zfill(4)}",
                graduation_year=random.randint(2015, 2023),
                degree=random.choice(["BSc Computer Science", "BSc IT", "BBA", "BSc Engineering"]),
                current_position=random.choice(positions),
                current_company=random.choice(companies),
                industry=random.choice(industries),
                willing_to_mentor=random.random() < 0.6,
                location=random.choice(["Colombo", "London", "Singapore", "Dubai", "Melbourne", "Toronto"]),
                bio=f"{name} is a proud NSBM alumnus who graduated with distinction and has been making strides in {random.choice(industries)}."
            )
            db.add(al)
            await db.flush()
            alumni_list.append(al)

            # Alumni experiences
            for _ in range(random.randint(1, 3)):
                categories = ["career", "academic", "personal"]
                exp_titles = [
                    f"How NSBM Shaped My Career in {random.choice(industries)}",
                    "From Campus to Corporate: My Journey",
                    "Lessons Learned as a First-Time Entrepreneur",
                    f"Working at {random.choice(companies)}: What I Wish I Knew",
                    "The Skills That Actually Matter in Tech",
                    "Networking Tips for Fresh Graduates"
                ]
                exp = AlumniExperience(
                    alumni_id=al.id,
                    title=random.choice(exp_titles),
                    content=f"""My journey at NSBM was truly transformative. The practical exposure, 
                    dedicated faculty, and industry connections helped me land my first role at {random.choice(companies)}.
                    
                    The most valuable lessons I learned were not just technical skills, but also how to collaborate 
                    effectively, communicate clearly, and approach problems with a growth mindset. The projects and 
                    assignments pushed me to think beyond textbook knowledge.
                    
                    To current students: embrace every opportunity, build your network, and don't be afraid to fail. 
                    Every challenge is a stepping stone to your success. NSBM gave me the foundation — I built the rest.""",
                    category=random.choice(categories),
                    tags=["career", "motivation", "technology"],
                    likes=random.randint(5, 150)
                )
                db.add(exp)

        # ── Library Books ──────────────────────────────────────────────────
        print("📚 Seeding library books...")
        books_data = [
            ("978-0-13-468599-1", "Clean Code", "Robert C. Martin", "Prentice Hall", 2008, "Computer Science", "Programming"),
            ("978-0-201-63361-0", "Design Patterns", "Gang of Four", "Addison-Wesley", 1994, "Computer Science", "Software Engineering"),
            ("978-0-13-110362-7", "The C Programming Language", "Kernighan & Ritchie", "Prentice Hall", 1988, "Computer Science", "Programming"),
            ("978-1-491-91205-8", "Python Data Science Handbook", "Jake VanderPlas", "O'Reilly", 2016, "Data Science", "Python"),
            ("978-0-262-03384-8", "Introduction to Algorithms", "CLRS", "MIT Press", 2009, "Computer Science", "Algorithms"),
            ("978-1-491-95036-2", "Designing Data-Intensive Applications", "Martin Kleppmann", "O'Reilly", 2017, "Databases", "Systems"),
            ("978-0-470-08596-2", "Database Management Systems", "Ramakrishnan & Gehrke", "McGraw-Hill", 2002, "Databases", "Database"),
            ("978-0-13-235088-4", "The Pragmatic Programmer", "Hunt & Thomas", "Addison-Wesley", 2019, "Computer Science", "Professional"),
            ("978-0-201-54435-6", "Refactoring", "Martin Fowler", "Addison-Wesley", 2018, "Software Engineering", "Best Practices"),
            ("978-0-13-140731-2", "Artificial Intelligence: A Modern Approach", "Russell & Norvig", "Prentice Hall", 2020, "AI/ML", "Artificial Intelligence"),
            ("978-1-491-91247-8", "Machine Learning with Python", "Andreas Müller", "O'Reilly", 2016, "AI/ML", "Machine Learning"),
            ("978-0-07-340510-7", "Principles of Corporate Finance", "Brealey & Myers", "McGraw-Hill", 2019, "Business", "Finance"),
            ("978-0-470-19054-2", "Engineering Mathematics", "K.A. Stroud", "Palgrave Macmillan", 2013, "Engineering", "Mathematics"),
            ("978-0-13-606228-7", "Computer Networks", "Tanenbaum", "Pearson", 2010, "Networking", "Computer Networks"),
            ("978-0-8053-4578-7", "Operating System Concepts", "Silberschatz et al.", "Wiley", 2018, "Computer Science", "Operating Systems"),
        ]
        for isbn, title, author, publisher, year, cat, subj in books_data:
            copies = random.randint(2, 8)
            avail = random.randint(0, copies)
            book = Book(
                isbn=isbn, title=title, author=author, publisher=publisher,
                year=year, category=cat, subject=subj, total_copies=copies,
                available_copies=avail,
                status=BookStatus.AVAILABLE if avail > 0 else BookStatus.BORROWED,
                description=f"A comprehensive resource on {subj} for students and professionals.",
                location=f"Shelf {random.choice('ABCDE')}{random.randint(1,10)}"
            )
            db.add(book)
        await db.flush()

        # Borrow records
        book_result = await db.execute(select(Book))
        all_books = book_result.scalars().all()
        for stu in students[:10]:
            for book in random.sample(all_books, random.randint(1, 3)):
                due = datetime.now() + timedelta(days=random.randint(-5, 14))
                borrow = BorrowRecord(
                    book_id=book.id, student_id=stu.id,
                    due_date=due,
                    status=BorrowStatus.ACTIVE if due > datetime.now() else BorrowStatus.OVERDUE,
                    fine_amount=0.0 if due > datetime.now() else round(random.uniform(0, 50), 2)
                )
                db.add(borrow)

        # ── Clubs ──────────────────────────────────────────────────────────
        print("⚽ Seeding clubs and sports...")
        clubs_data = [
            ("NSBM Cricket Club", "Premier cricket club with national-level players", ClubCategory.SPORTS, lecturers[3].id),
            ("NSBM Football Club", "University football team competing in inter-university championships", ClubCategory.SPORTS, lecturers[3].id),
            ("IEEE Student Branch", "Technical excellence through innovation and collaboration", ClubCategory.TECHNICAL, lecturers[0].id),
            ("Drama & Arts Society", "Celebrating Sri Lankan culture through performance arts", ClubCategory.CULTURAL, lecturers[2].id),
            ("Entrepreneur Club", "Fostering startup culture and business innovation", ClubCategory.ACADEMIC, lecturers[2].id),
            ("Green Society", "Environmental sustainability and eco-initiatives on campus", ClubCategory.SOCIAL, lecturers[1].id),
            ("Coding Warriors", "Competitive programming and hackathon team", ClubCategory.TECHNICAL, lecturers[1].id),
            ("Badminton Club", "Competitive badminton for all skill levels", ClubCategory.SPORTS, lecturers[3].id),
        ]
        clubs = []
        for name, desc, cat, adv_id in clubs_data:
            president = random_name()
            club = Club(
                name=name, description=desc, category=cat, advisor_id=adv_id,
                president_name=president, max_members=50, is_active=True,
                achievements=f"Won multiple inter-university competitions. Represented NSBM at national level events.",
                meeting_schedule={"day": random.choice(["Monday", "Wednesday", "Friday"]), "time": "15:00", "venue": "Main Auditorium"}
            )
            db.add(club)
            clubs.append(club)
        await db.flush()

        # Club memberships
        for stu in students:
            for club in random.sample(clubs, random.randint(1, 3)):
                membership = ClubMembership(club_id=club.id, student_id=stu.id, role="member", is_active=True)
                db.add(membership)

        # Club events
        event_titles = [
            "Annual Tech Symposium 2025", "Inter-Faculty Cricket Tournament", "Cultural Night 2025",
            "Hackathon 48H", "Business Plan Competition", "Green Campus Day", "Alumni Meet & Greet",
            "Football League Finals", "CodeStorm 2025", "Career Fair 2025"
        ]
        for i, club in enumerate(clubs):
            for j in range(2):
                event = ClubEvent(
                    club_id=club.id,
                    title=random.choice(event_titles),
                    description="Join us for an exciting event that brings together students, faculty, and industry professionals.",
                    event_date=datetime.now() + timedelta(days=random.randint(3, 60)),
                    location=random.choice(["Main Auditorium", "Sports Ground", "Innovation Hub", "Lecture Hall A"]),
                    max_participants=100, registration_required=True, is_public=True
                )
                db.add(event)

        # ── News ───────────────────────────────────────────────────────────
        print("📰 Seeding news articles...")
        news_articles = [
            ("NSBM Ranks in Top 10 Universities in Sri Lanka", NewsCategory.ACADEMIC, True,
             "NSBM Green University has been recognized among the top 10 universities in Sri Lanka by the QS Asia Rankings 2025."),
            ("Green Campus Initiative Wins National Award", NewsCategory.GENERAL, True,
             "The NSBM Green Campus project has been awarded the National Environmental Excellence Award."),
            ("NSBM Cricket Team Wins Inter-University Championship", NewsCategory.SPORTS, False,
             "The NSBM Cricket team emerged victorious at the Sri Lanka Inter-University Cricket Championship 2025."),
            ("New AI Research Lab Inaugurated", NewsCategory.RESEARCH, True,
             "NSBM inaugurates its state-of-the-art AI and Machine Learning Research Laboratory."),
            ("Career Fair 2025: 100+ Companies to Participate", NewsCategory.EVENTS, False,
             "NSBM's annual Career Fair brings together over 100 leading companies for student recruitment."),
            ("Alumni Success Story: From NSBM to Google", NewsCategory.ALUMNI, True,
             "NSBM alumnus secures senior engineering role at Google's Singapore office."),
            ("Semester Registration Now Open", NewsCategory.ACADEMIC, False,
             "Students can now register for the upcoming semester through the EduSphere portal."),
            ("NSBM Badminton Player Represents Sri Lanka", NewsCategory.SPORTS, False,
             "A current NSBM student has been selected to represent Sri Lanka at the South Asian Badminton Championship."),
        ]
        try:
            from slugify import slugify as _slugify
        except ImportError:
            _slugify = lambda s: s.lower().replace(" ", "-")
        for i, (title, cat, featured, summary) in enumerate(news_articles):
            slug = f"{_slugify(title[:40])}-{i}"
            news = News(
                title=title,
                slug=slug,
                content=f"""{summary}

This is a significant milestone for NSBM Green University and reflects our commitment to excellence in education, 
research, and student development. The entire NSBM community takes pride in this achievement.

Our dedicated faculty, hardworking students, and supportive administration have all contributed to making NSBM 
one of the most sought-after private universities in Sri Lanka.

We continue to invest in world-class facilities, industry partnerships, and student support programs to ensure 
that every NSBM graduate is career-ready and equipped for the challenges of the modern world.

Stay tuned for more updates from NSBM EduSphere — your gateway to campus life.""",
                summary=summary,
                category=cat,
                author_id=admin.id,
                tags=["nsbm", "university", cat.value],
                views=random.randint(50, 2000),
                is_published=True,
                is_featured=featured,
                published_at=datetime.now() - timedelta(days=random.randint(0, 30))
            )
            db.add(news)

        # ── Notifications ──────────────────────────────────────────────────
        print("🔔 Seeding notifications...")
        notif_templates = [
            ("New Assignment Posted", "A new assignment has been posted in CS301", "info", "/assignments"),
            ("Grade Updated", "Your grade for IT101 has been updated", "success", "/grades"),
            ("Library Due Reminder", "A borrowed book is due in 2 days", "warning", "/library"),
            ("Club Event Reminder", "IEEE Symposium starts tomorrow", "info", "/clubs"),
            ("Exam Schedule Released", "Final exam timetable is now available", "info", "/timetable"),
        ]
        for stu_user in student_users[:10]:
            for title, msg, ntype, link in random.sample(notif_templates, 3):
                notif = Notification(
                    user_id=stu_user.id, title=title, message=msg,
                    notification_type=ntype, link=link,
                    is_read=random.random() < 0.4
                )
                db.add(notif)

        await db.commit()
        print("✅ Database seeded successfully!")
        print("\n🔐 Demo Accounts:")
        print("  Admin:    admin / Admin@123")
        print("  Student:  student01 / Student@123")
        print("  Lecturer: kperera / Lecturer@123")
        print("  Alumni:   alumni01 / Alumni@123")


if __name__ == "__main__":
    asyncio.run(seed_database())
