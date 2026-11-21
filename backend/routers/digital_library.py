"""backend/routers/digital_library.py
Modern Digital Library System Router
Provides comprehensive institutional digital repository capabilities, e-book reader
streaming, peer-reviewed paper search, curated collection categorization,
user reading list bookmarking, and digital access analytics.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, and_, or_, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.database import get_db
from backend.models import (
    User,
    DigitalLibraryResource,
    LibrarySubjectCollection,
    LibraryResourceBookmark,
)
from backend.schemas import (
    DigitalResourceCreate,
    DigitalResourceUpdate,
    DigitalResourceOut,
    LibrarySubjectCollectionCreate,
    LibrarySubjectCollectionOut,
    LibraryBookmarkOut,
    DigitalLibraryStatsOut,
)
from backend.utils.security import get_current_user, require_roles

router = APIRouter(prefix="/api/digital-library", tags=["Modern Digital Library System"])


# ─── Digital Catalog Search & Discovery ──────────────────────────────────────

@router.get("/catalog", response_model=List[DigitalResourceOut])
async def list_digital_resources(
    query: Optional[str] = Query(None, description="Search keyword in title, author, abstract, or keywords"),
    resource_type: Optional[str] = Query(None, description="ebook, research_paper, journal_article, thesis, video_lecture"),
    file_format: Optional[str] = Query(None, description="pdf, epub, mp4, mp3"),
    subject_category: Optional[str] = Query(None),
    collection_id: Optional[int] = Query(None),
    open_access_only: Optional[bool] = Query(None),
    sort_by: str = Query("recent", regex="^(recent|views|downloads|title)$"),
    limit: int = Query(30, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    """Search and browse digital library publications with multi-facet filters."""
    filters = []

    if query:
        term = f"%{query.strip()}%"
        filters.append(
            or_(
                DigitalLibraryResource.title.ilike(term),
                DigitalLibraryResource.author.ilike(term),
                DigitalLibraryResource.abstract.ilike(term),
                DigitalLibraryResource.keywords.ilike(term),
                DigitalLibraryResource.publisher.ilike(term),
            )
        )
    if resource_type and resource_type != "all":
        filters.append(DigitalLibraryResource.resource_type == resource_type)
    if file_format and file_format != "all":
        filters.append(DigitalLibraryResource.file_format == file_format)
    if subject_category and subject_category != "all":
        filters.append(DigitalLibraryResource.subject_category == subject_category)
    if collection_id:
        filters.append(DigitalLibraryResource.collection_id == collection_id)
    if open_access_only is True:
        filters.append(DigitalLibraryResource.is_open_access == True)

    stmt = select(DigitalLibraryResource)
    if filters:
        stmt = stmt.where(and_(*filters))

    if sort_by == "views":
        stmt = stmt.order_by(desc(DigitalLibraryResource.view_count))
    elif sort_by == "downloads":
        stmt = stmt.order_by(desc(DigitalLibraryResource.download_count))
    elif sort_by == "title":
        stmt = stmt.order_by(DigitalLibraryResource.title.asc())
    else:
        stmt = stmt.order_by(desc(DigitalLibraryResource.created_at))

    stmt = stmt.offset(offset).limit(limit)
    res = await db.execute(stmt)
    resources = res.scalars().all()

    # Determine user bookmarks if logged in
    bookmarked_ids = set()
    if current_user and resources:
        bm_res = await db.execute(
            select(LibraryResourceBookmark.resource_id).where(
                and_(
                    LibraryResourceBookmark.user_id == current_user.id,
                    LibraryResourceBookmark.resource_id.in_([r.id for r in resources])
                )
            )
        )
        bookmarked_ids = set(bm_res.scalars().all())

    out = []
    for r in resources:
        item = DigitalResourceOut.model_validate(r)
        item.is_bookmarked = r.id in bookmarked_ids
        out.append(item)
    return out


@router.get("/catalog/{resource_id}", response_model=DigitalResourceOut)
async def get_digital_resource(
    resource_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    """Retrieve full metadata for a digital library resource and increment view count."""
    res = await db.execute(
        select(DigitalLibraryResource).where(DigitalLibraryResource.id == resource_id)
    )
    resource = res.scalars().first()
    if not resource:
        raise HTTPException(status_code=404, detail="Digital resource not found.")

    # Increment view counter
    resource.view_count += 1
    await db.commit()
    await db.refresh(resource)

    is_bm = False
    if current_user:
        bm_res = await db.execute(
            select(LibraryResourceBookmark.id).where(
                and_(
                    LibraryResourceBookmark.user_id == current_user.id,
                    LibraryResourceBookmark.resource_id == resource.id,
                )
            )
        )
        is_bm = bm_res.scalars().first() is not None

    item = DigitalResourceOut.model_validate(resource)
    item.is_bookmarked = is_bm
    return item


@router.post("/catalog", response_model=DigitalResourceOut, status_code=status.HTTP_201_CREATED)
async def create_digital_resource(
    payload: DigitalResourceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "librarian")),
):
    """Curate and publish an e-book, research paper, or digital asset to the institutional catalog."""
    resource = DigitalLibraryResource(
        title=payload.title,
        author=payload.author,
        resource_type=payload.resource_type,
        doi_or_issn=payload.doi_or_issn,
        subject_category=payload.subject_category,
        file_format=payload.file_format,
        file_url=payload.file_url,
        cover_url=payload.cover_url,
        file_size_bytes=payload.file_size_bytes,
        abstract=payload.abstract,
        keywords=payload.keywords,
        is_open_access=payload.is_open_access,
        published_year=payload.published_year,
        publisher=payload.publisher,
        collection_id=payload.collection_id,
        book_id=payload.book_id,
        created_at=datetime.utcnow(),
    )
    db.add(resource)
    await db.commit()
    await db.refresh(resource)
    return resource


@router.put("/catalog/{resource_id}", response_model=DigitalResourceOut)
async def update_digital_resource(
    resource_id: int,
    payload: DigitalResourceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "librarian")),
):
    """Update metadata for an existing catalog asset."""
    res = await db.execute(
        select(DigitalLibraryResource).where(DigitalLibraryResource.id == resource_id)
    )
    resource = res.scalars().first()
    if not resource:
        raise HTTPException(status_code=404, detail="Digital resource not found.")

    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(resource, k, v)
    resource.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(resource)
    return resource


@router.delete("/catalog/{resource_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_digital_resource(
    resource_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "librarian")),
):
    """Remove a digital asset from the library repository."""
    res = await db.execute(
        select(DigitalLibraryResource).where(DigitalLibraryResource.id == resource_id)
    )
    resource = res.scalars().first()
    if not resource:
        raise HTTPException(status_code=404, detail="Digital resource not found.")

    await db.delete(resource)
    await db.commit()
    return None


@router.post("/catalog/{resource_id}/download")
async def track_resource_download(
    resource_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Track digital download event and return secure direct asset download URL."""
    res = await db.execute(
        select(DigitalLibraryResource).where(DigitalLibraryResource.id == resource_id)
    )
    resource = res.scalars().first()
    if not resource:
        raise HTTPException(status_code=404, detail="Digital resource not found.")

    resource.download_count += 1
    await db.commit()
    return {
        "resource_id": resource.id,
        "title": resource.title,
        "download_url": resource.file_url,
        "file_format": resource.file_format,
        "download_count": resource.download_count,
    }


# ─── Reading List & Bookmarks ────────────────────────────────────────────────

@router.post("/catalog/{resource_id}/bookmark")
async def toggle_resource_bookmark(
    resource_id: int,
    notes: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Toggle digital asset in student or faculty reading list."""
    # Check resource existence
    res = await db.execute(
        select(DigitalLibraryResource).where(DigitalLibraryResource.id == resource_id)
    )
    resource = res.scalars().first()
    if not resource:
        raise HTTPException(status_code=404, detail="Digital resource not found.")

    bm_res = await db.execute(
        select(LibraryResourceBookmark).where(
            and_(
                LibraryResourceBookmark.user_id == current_user.id,
                LibraryResourceBookmark.resource_id == resource_id,
            )
        )
    )
    existing = bm_res.scalars().first()
    if existing:
        await db.delete(existing)
        await db.commit()
        return {"bookmarked": False, "message": "Removed from your reading list."}
    else:
        new_bm = LibraryResourceBookmark(
            user_id=current_user.id,
            resource_id=resource_id,
            notes=notes,
            created_at=datetime.utcnow(),
        )
        db.add(new_bm)
        await db.commit()
        return {"bookmarked": True, "message": "Saved to your reading list."}


@router.get("/my-bookmarks", response_model=List[LibraryBookmarkOut])
async def list_my_bookmarks(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve personal reading list bookmarks for the current user."""
    res = await db.execute(
        select(LibraryResourceBookmark)
        .options(selectinload(LibraryResourceBookmark.resource))
        .where(LibraryResourceBookmark.user_id == current_user.id)
        .order_by(desc(LibraryResourceBookmark.created_at))
    )
    bookmarks = res.scalars().all()

    out = []
    for bm in bookmarks:
        r_out = DigitalResourceOut.model_validate(bm.resource)
        r_out.is_bookmarked = True
        out.append(
            LibraryBookmarkOut(
                id=bm.id,
                user_id=bm.user_id,
                resource_id=bm.resource_id,
                resource=r_out,
                notes=bm.notes,
                created_at=bm.created_at,
            )
        )
    return out


# ─── Institutional Collections ───────────────────────────────────────────────

@router.get("/collections", response_model=List[LibrarySubjectCollectionOut])
async def list_subject_collections(
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    """List curated institutional digital collections."""
    res = await db.execute(
        select(LibrarySubjectCollection)
        .options(selectinload(LibrarySubjectCollection.resources))
        .order_by(LibrarySubjectCollection.title.asc())
    )
    collections = res.scalars().all()
    out = []
    for c in collections:
        out.append(
            LibrarySubjectCollectionOut(
                id=c.id,
                title=c.title,
                slug=c.slug,
                description=c.description,
                icon=c.icon,
                is_featured=c.is_featured,
                resource_count=len(c.resources) if c.resources else 0,
                created_at=c.created_at,
            )
        )
    return out


@router.post("/collections", response_model=LibrarySubjectCollectionOut, status_code=status.HTTP_201_CREATED)
async def create_subject_collection(
    payload: LibrarySubjectCollectionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "librarian")),
):
    """Create a curated institutional subject collection."""
    exist_slug = await db.execute(
        select(LibrarySubjectCollection).where(LibrarySubjectCollection.slug == payload.slug)
    )
    if exist_slug.scalars().first():
        raise HTTPException(status_code=400, detail="Collection slug already exists.")

    col = LibrarySubjectCollection(
        title=payload.title,
        slug=payload.slug,
        description=payload.description,
        icon=payload.icon,
        is_featured=payload.is_featured,
        created_at=datetime.utcnow(),
    )
    db.add(col)
    await db.commit()
    await db.refresh(col)
    return LibrarySubjectCollectionOut(
        id=col.id,
        title=col.title,
        slug=col.slug,
        description=col.description,
        icon=col.icon,
        is_featured=col.is_featured,
        resource_count=0,
        created_at=col.created_at,
    )


# ─── Digital Library Analytics ───────────────────────────────────────────────

@router.get("/stats", response_model=DigitalLibraryStatsOut)
async def get_digital_library_stats(
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    """Institutional analytics on repository size, readership views, and downloads."""
    res = await db.execute(select(DigitalLibraryResource))
    all_res = res.scalars().all()

    tot_resources = len(all_res)
    tot_views = sum(r.view_count for r in all_res)
    tot_downloads = sum(r.download_count for r in all_res)

    type_counts: Dict[str, int] = {}
    subj_counts: Dict[str, int] = {}

    for r in all_res:
        type_counts[r.resource_type] = type_counts.get(r.resource_type, 0) + 1
        subj_counts[r.subject_category] = subj_counts.get(r.subject_category, 0) + 1

    return DigitalLibraryStatsOut(
        total_resources=tot_resources,
        total_views=tot_views,
        total_downloads=tot_downloads,
        resource_type_breakdown=type_counts,
        subject_breakdown=subj_counts,
    )
