import os
import io
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models import User, UserRole, Course, CourseModule, CourseLesson, Student, Enrollment
from backend.utils.security import hash_password, create_access_token


@pytest.mark.asyncio
async def test_document_and_media_management_lifecycle(
    client: AsyncClient,
    test_session: AsyncSession
):
    # 1. Setup Admin user
    admin_user = User(
        email="doc_admin@nsbm.ac.lk",
        username="doc_admin",
        hashed_password=hash_password("AdminPass123!"),
        full_name="Doc Admin",
        role=UserRole.ADMIN,
        is_active=True,
    )
    test_session.add(admin_user)
    await test_session.commit()
    await test_session.refresh(admin_user)

    admin_token = create_access_token({"sub": str(admin_user.id), "role": admin_user.role.value})
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 2. Create Course
    c_res = await client.post(
        "/api/courses",
        headers=admin_headers,
        json={
            "course_code": "CS302",
            "title": "Cloud Computing and Distributed Storage",
            "credits": 3,
            "semester": 2,
            "year": 3,
            "max_students": 50
        }
    )
    assert c_res.status_code == 201
    course_id = c_res.json()["id"]

    # 3. Test Unsupported MIME Type Upload (e.g. .exe file)
    bad_file = io.BytesIO(b"MZ\x90\x00executable")
    bad_upload = await client.post(
        f"/api/courses/{course_id}/documents/upload",
        headers=admin_headers,
        files={"file": ("malware.exe", bad_file, "application/x-msdownload")},
        data={"title": "Malware Executable"}
    )
    assert bad_upload.status_code == 415

    # 4. Upload Valid PDF Document with Traversal-like filename
    valid_pdf_content = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF"
    pdf_file = io.BytesIO(valid_pdf_content)
    upload_res = await client.post(
        f"/api/courses/{course_id}/documents/upload",
        headers=admin_headers,
        files={"file": ("../../lecture_slides.pdf", pdf_file, "application/pdf")},
        data={"title": "Cloud Architecture Overview", "is_published": "true"}
    )
    assert upload_res.status_code == 201
    doc_data = upload_res.json()
    doc_id = doc_data["id"]
    assert doc_data["title"] == "Cloud Architecture Overview"
    assert doc_data["original_filename"] == "lecture_slides.pdf"  # traversal stripped
    assert doc_data["file_size_bytes"] == len(valid_pdf_content)
    assert len(doc_data["sha256_hash"]) == 64
    assert doc_data["download_count"] == 0

    # 5. Upload a Private / Unpublished Document
    draft_content = b"Confidential Faculty Exam Outline"
    draft_file = io.BytesIO(draft_content)
    draft_res = await client.post(
        f"/api/courses/{course_id}/documents/upload",
        headers=admin_headers,
        files={"file": ("exam_outline.txt", draft_file, "text/plain")},
        data={"title": "Exam Blueprint", "is_published": "false"}
    )
    assert draft_res.status_code == 201
    draft_doc_id = draft_res.json()["id"]

    # 6. Setup Enrolled Student & Non-enrolled Outsider Student
    enrolled_u = User(
        email="enrolled_cs302@nsbm.ac.lk",
        username="enrolled_cs302",
        hashed_password=hash_password("Pass123!"),
        full_name="Enrolled Student",
        role=UserRole.STUDENT,
        is_active=True
    )
    outsider_u = User(
        email="outsider_cs302@nsbm.ac.lk",
        username="outsider_cs302",
        hashed_password=hash_password("Pass123!"),
        full_name="Outsider Student",
        role=UserRole.STUDENT,
        is_active=True
    )
    test_session.add_all([enrolled_u, outsider_u])
    await test_session.commit()
    await test_session.refresh(enrolled_u)
    await test_session.refresh(outsider_u)

    stu_enrolled = Student(
        user_id=enrolled_u.id,
        student_id="STU-ENR-302",
        faculty="Computing",
        department="Computer Systems",
        program="BSc Cloud Computing",
        academic_standing="good_standing"
    )
    stu_outsider = Student(
        user_id=outsider_u.id,
        student_id="STU-OUT-302",
        faculty="Computing",
        department="Computer Systems",
        program="BSc Cloud Computing",
        academic_standing="good_standing"
    )
    test_session.add_all([stu_enrolled, stu_outsider])
    await test_session.commit()
    await test_session.refresh(stu_enrolled)
    await test_session.refresh(stu_outsider)

    # Enroll stu_enrolled
    enr = Enrollment(student_id=stu_enrolled.id, course_id=course_id, status="active")
    test_session.add(enr)
    await test_session.commit()

    enrolled_token = create_access_token({"sub": str(enrolled_u.id), "role": enrolled_u.role.value})
    enrolled_headers = {"Authorization": f"Bearer {enrolled_token}"}

    outsider_token = create_access_token({"sub": str(outsider_u.id), "role": outsider_u.role.value})
    outsider_headers = {"Authorization": f"Bearer {outsider_token}"}

    # 7. Student Document Access & Privacy Controls
    # Enrolled student listing documents:
    enr_list = await client.get(f"/api/courses/{course_id}/documents", headers=enrolled_headers)
    assert enr_list.status_code == 200
    docs = enr_list.json()
    assert len(docs) == 1
    assert docs[0]["id"] == doc_id
    # Draft document is NOT visible to student
    assert draft_doc_id not in [d["id"] for d in docs]

    # Outsider student listing documents receives 403 Forbidden
    out_list = await client.get(f"/api/courses/{course_id}/documents", headers=outsider_headers)
    assert out_list.status_code == 403

    # Enrolled student downloading published document:
    download_res = await client.get(f"/api/documents/{doc_id}/download", headers=enrolled_headers)
    assert download_res.status_code == 200
    assert download_res.content == valid_pdf_content
    assert download_res.headers["x-content-type-options"] == "nosniff"

    # Verify download count incremented:
    meta_res = await client.get(f"/api/documents/{doc_id}", headers=enrolled_headers)
    assert meta_res.status_code == 200
    assert meta_res.json()["download_count"] == 1

    # Outsider student downloading receives 403
    out_download = await client.get(f"/api/documents/{doc_id}/download", headers=outsider_headers)
    assert out_download.status_code == 403

    # Student cannot upload document
    stu_upload = await client.post(
        f"/api/courses/{course_id}/documents/upload",
        headers=enrolled_headers,
        files={"file": ("hw.pdf", io.BytesIO(b"data"), "application/pdf")}
    )
    assert stu_upload.status_code == 403

    # 8. Document Deletion
    del_res = await client.delete(f"/api/documents/{doc_id}", headers=admin_headers)
    assert del_res.status_code == 204

    # Confirm document no longer exists
    get_del = await client.get(f"/api/documents/{doc_id}", headers=admin_headers)
    assert get_del.status_code == 404
