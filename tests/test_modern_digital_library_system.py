import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models import User, UserRole, Student
from backend.utils.security import hash_password, create_access_token


@pytest.mark.asyncio
async def test_modern_digital_library_system(
    client: AsyncClient,
    test_session: AsyncSession
):
    # 1. Setup Student and Librarian users
    student_user = User(
        email="lib_student@nsbm.ac.lk",
        username="lib_student",
        hashed_password=hash_password("Pass123!"),
        full_name="Nuwan Pradeep",
        role=UserRole.STUDENT,
        is_active=True,
    )
    librarian_user = User(
        email="librarian@nsbm.ac.lk",
        username="librarian_admin",
        hashed_password=hash_password("LibPass123!"),
        full_name="Head Librarian Jayasinghe",
        role=UserRole.ADMIN,  # Has librarian/admin privileges
        is_active=True,
    )
    test_session.add_all([student_user, librarian_user])
    await test_session.commit()

    student = Student(
        user_id=student_user.id,
        student_id="STU-LIB-01",
        faculty="Computing",
        department="Software Engineering",
        program="BSc Software Engineering",
        year_of_study=3,
        semester=1,
        gpa=3.65,
        credits_earned=75,
    )
    test_session.add(student)
    await test_session.commit()

    student_token = create_access_token({"sub": str(student_user.id), "role": "student"})
    librarian_token = create_access_token({"sub": str(librarian_user.id), "role": "admin"})

    student_headers = {"Authorization": f"Bearer {student_token}"}
    librarian_headers = {"Authorization": f"Bearer {librarian_token}"}

    # 2. Librarian creates Curated Subject Collection
    col_payload = {
        "title": "Software Architecture & Distributed Systems",
        "slug": "software-architecture-distributed-systems",
        "description": "Curated collection of seminal distributed computing and architectural books",
        "icon": "🏗️",
        "is_featured": True,
    }
    res = await client.post("/api/digital-library/collections", json=col_payload, headers=librarian_headers)
    assert res.status_code == 201
    col_data = res.json()
    assert col_data["title"] == "Software Architecture & Distributed Systems"
    collection_id = col_data["id"]

    # 3. Librarian publishes a Digital Resource
    res_payload = {
        "title": "Patterns of Enterprise Application Architecture",
        "author": "Martin Fowler",
        "resource_type": "ebook",
        "doi_or_issn": "ISBN:978-0321127426",
        "subject_category": "Software Engineering",
        "file_format": "pdf",
        "file_url": "https://cdn.edusphere.nsbm.ac.lk/repository/poeaa.pdf",
        "file_size_bytes": 15420000,
        "abstract": "Foundational architectural patterns for enterprise software applications and relational data mapping.",
        "keywords": "architecture, patterns, enterprise, orm",
        "is_open_access": True,
        "published_year": 2003,
        "publisher": "Addison-Wesley",
        "collection_id": collection_id,
    }
    res = await client.post("/api/digital-library/catalog", json=res_payload, headers=librarian_headers)
    assert res.status_code == 201
    created_res = res.json()
    resource_id = created_res["id"]
    assert created_res["title"] == "Patterns of Enterprise Application Architecture"
    assert created_res["resource_type"] == "ebook"

    # 4. Student searches the catalog
    res = await client.get("/api/digital-library/catalog?query=Enterprise&resource_type=ebook", headers=student_headers)
    assert res.status_code == 200
    catalog = res.json()
    assert len(catalog) >= 1
    found = next(r for r in catalog if r["id"] == resource_id)
    assert found["author"] == "Martin Fowler"
    assert found["is_bookmarked"] is False

    # 5. Student views the resource details -> Increments view count
    res = await client.get(f"/api/digital-library/catalog/{resource_id}", headers=student_headers)
    assert res.status_code == 200
    detail = res.json()
    assert detail["id"] == resource_id
    assert detail["view_count"] >= 1

    # 6. Student bookmarks the resource (adds to reading list)
    res = await client.post(f"/api/digital-library/catalog/{resource_id}/bookmark", headers=student_headers)
    assert res.status_code == 200
    bm_data = res.json()
    assert bm_data["bookmarked"] is True

    # 7. Student retrieves personal reading list
    res = await client.get("/api/digital-library/my-bookmarks", headers=student_headers)
    assert res.status_code == 200
    bookmarks = res.json()
    assert len(bookmarks) >= 1
    my_bm = next(b for b in bookmarks if b["resource_id"] == resource_id)
    assert my_bm["resource"]["title"] == "Patterns of Enterprise Application Architecture"
    assert my_bm["resource"]["is_bookmarked"] is True

    # 8. Student tracks download
    res = await client.post(f"/api/digital-library/catalog/{resource_id}/download", headers=student_headers)
    assert res.status_code == 200
    dl_data = res.json()
    assert dl_data["download_count"] >= 1
    assert dl_data["download_url"] == "https://cdn.edusphere.nsbm.ac.lk/repository/poeaa.pdf"

    # 9. Query Institutional Collections
    res = await client.get("/api/digital-library/collections", headers=student_headers)
    assert res.status_code == 200
    collections = res.json()
    assert any(c["id"] == collection_id for c in collections)

    # 10. Query Digital Library Analytics
    res = await client.get("/api/digital-library/stats", headers=student_headers)
    assert res.status_code == 200
    stats = res.json()
    assert stats["total_resources"] >= 1
    assert stats["total_views"] >= 1
    assert stats["total_downloads"] >= 1
    assert stats["resource_type_breakdown"].get("ebook", 0) >= 1
