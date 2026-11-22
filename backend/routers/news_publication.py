"""backend/routers/news_publication.py
Campus News and Media Publication Router
Provides multi-channel campus journalism, university press releases,
editorial review workflows, rich media gallery curation, reader reactions,
and comment discussion threads.
"""

import re
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, and_, or_, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.database import get_db
from backend.models import (
    User,
    News,
    NewsCategory,
    NewsComment,
    MediaGalleryItem,
    NewsReaction,
)
from backend.schemas import (
    NewsArticleCreate,
    NewsArticleUpdate,
    NewsArticleOut,
    NewsCommentCreate,
    NewsCommentOut,
    MediaGalleryItemCreate,
    MediaGalleryItemOut,
    NewsPublicationStatsOut,
)
from backend.utils.security import get_current_user, require_roles

router = APIRouter(prefix="/api/news-publication", tags=["Campus News & Media Publication"])


def slugify(text: str) -> str:
    cleaned = re.sub(r"[^\w\s-]", "", text).strip().lower()
    slug_base = re.sub(r"[-\s]+", "-", cleaned)
    suffix = uuid.uuid4().hex[:6]
    return f"{slug_base[:80]}-{suffix}"


def serialize_article(article: News, current_user_id: Optional[int] = None) -> NewsArticleOut:
    a_name = article.author.full_name if article.author else None
    cat_val = article.category.value if hasattr(article.category, "value") else str(article.category)

    gallery_out = [
        MediaGalleryItemOut(
            id=m.id,
            news_id=m.news_id,
            title=m.title,
            media_type=m.media_type,
            media_url=m.media_url,
            caption=m.caption,
            sort_order=m.sort_order,
            created_at=m.created_at,
        )
        for m in (article.gallery or [])
    ]

    comments_out = [
        NewsCommentOut(
            id=c.id,
            news_id=c.news_id,
            user_id=c.user_id,
            user_name=c.user.full_name if c.user else "Anonymous",
            content=c.content,
            created_at=c.created_at,
        )
        for c in (article.comments or [])
    ]

    user_liked = False
    if current_user_id and article.reactions:
        user_liked = any(r.user_id == current_user_id for r in article.reactions)

    return NewsArticleOut(
        id=article.id,
        title=article.title,
        slug=article.slug,
        content=article.content,
        summary=article.summary,
        category=cat_val,
        author_id=article.author_id,
        author_name=a_name,
        cover_image_url=article.cover_image_url,
        tags=article.tags,
        views=article.views,
        likes_count=article.likes_count,
        is_published=article.is_published,
        is_featured=article.is_featured,
        status=article.status,
        target_audience=article.target_audience,
        editorial_notes=article.editorial_notes,
        published_at=article.published_at,
        created_at=article.created_at,
        updated_at=article.updated_at,
        gallery=gallery_out,
        comments=comments_out,
        user_has_liked=user_liked,
    )


# ─── News Publication & Editorial Endpoints ─────────────────────────────────

@router.get("/articles", response_model=List[NewsArticleOut])
async def list_news_articles(
    category: Optional[str] = Query(None),
    status_filter: Optional[str] = Query("published"),
    target_audience: Optional[str] = Query(None),
    featured_only: Optional[bool] = Query(None),
    query: Optional[str] = Query(None),
    limit: int = Query(30, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    """Retrieve curated campus news stories with multi-facet filters."""
    stmt = (
        select(News)
        .options(
            selectinload(News.author),
            selectinload(News.gallery),
            selectinload(News.comments).selectinload(NewsComment.user),
            selectinload(News.reactions),
        )
        .order_by(desc(News.published_at), desc(News.created_at))
        .offset(offset)
        .limit(limit)
    )

    filters = []
    if status_filter and status_filter != "all":
        filters.append(News.status == status_filter)
    if category and category != "all":
        filters.append(News.category == category)
    if target_audience and target_audience != "all":
        filters.append(or_(News.target_audience == target_audience, News.target_audience == "all"))
    if featured_only is True:
        filters.append(News.is_featured == True)
    if query:
        term = f"%{query.strip()}%"
        filters.append(
            or_(
                News.title.ilike(term),
                News.content.ilike(term),
                News.summary.ilike(term),
            )
        )

    if filters:
        stmt = stmt.where(and_(*filters))

    res = await db.execute(stmt)
    articles = res.scalars().all()
    uid = current_user.id if current_user else None
    return [serialize_article(a, uid) for a in articles]


@router.get("/articles/{identifier}", response_model=NewsArticleOut)
async def get_news_article_detail(
    identifier: str,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    """Fetch article by numeric ID or URL slug and increment view counter."""
    stmt = (
        select(News)
        .options(
            selectinload(News.author),
            selectinload(News.gallery),
            selectinload(News.comments).selectinload(NewsComment.user),
            selectinload(News.reactions),
        )
    )
    if identifier.isdigit():
        stmt = stmt.where(News.id == int(identifier))
    else:
        stmt = stmt.where(News.slug == identifier)

    res = await db.execute(stmt)
    article = res.scalars().first()
    if not article:
        raise HTTPException(status_code=404, detail="News article not found.")

    # Increment view counter
    article.views += 1
    await db.commit()
    await db.refresh(article)

    uid = current_user.id if current_user else None
    return serialize_article(article, uid)


@router.post("/articles", response_model=NewsArticleOut, status_code=status.HTTP_201_CREATED)
async def create_news_article(
    payload: NewsArticleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Draft or publish an article or press release."""
    # Determine initial status based on role
    init_status = payload.status
    if current_user.role not in ["admin", "lecturer"]:
        init_status = "submitted"  # student submissions go to editorial review

    slug = slugify(payload.title)
    cat_enum = NewsCategory(payload.category) if payload.category in [c.value for c in NewsCategory] else NewsCategory.GENERAL

    article = News(
        title=payload.title,
        slug=slug,
        content=payload.content,
        summary=payload.summary,
        category=cat_enum,
        author_id=current_user.id,
        cover_image_url=payload.cover_image_url,
        tags=payload.tags or [],
        views=0,
        likes_count=0,
        is_published=(init_status == "published"),
        is_featured=payload.is_featured,
        status=init_status,
        target_audience=payload.target_audience,
        published_at=datetime.utcnow() if init_status == "published" else None,
        created_at=datetime.utcnow(),
    )
    db.add(article)
    await db.commit()

    reload_res = await db.execute(
        select(News)
        .options(
            selectinload(News.author),
            selectinload(News.gallery),
            selectinload(News.comments),
            selectinload(News.reactions),
        )
        .where(News.id == article.id)
    )
    loaded = reload_res.scalars().first()
    return serialize_article(loaded, current_user.id)


@router.put("/articles/{article_id}", response_model=NewsArticleOut)
async def update_news_article(
    article_id: int,
    payload: NewsArticleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update article content or metadata."""
    res = await db.execute(
        select(News)
        .options(
            selectinload(News.author),
            selectinload(News.gallery),
            selectinload(News.comments),
            selectinload(News.reactions),
        )
        .where(News.id == article_id)
    )
    article = res.scalars().first()
    if not article:
        raise HTTPException(status_code=404, detail="News article not found.")

    if current_user.role not in ["admin", "lecturer"] and article.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Unauthorized to edit this article.")

    for k, v in payload.model_dump(exclude_unset=True).items():
        if k == "category" and v:
            setattr(article, k, NewsCategory(v) if v in [c.value for c in NewsCategory] else NewsCategory.GENERAL)
        else:
            setattr(article, k, v)

    article.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(article)
    return serialize_article(article, current_user.id)


@router.put("/articles/{article_id}/publish", response_model=NewsArticleOut)
async def publish_news_article(
    article_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "lecturer")),
):
    """Editorial publication authorization."""
    res = await db.execute(
        select(News)
        .options(
            selectinload(News.author),
            selectinload(News.gallery),
            selectinload(News.comments),
            selectinload(News.reactions),
        )
        .where(News.id == article_id)
    )
    article = res.scalars().first()
    if not article:
        raise HTTPException(status_code=404, detail="News article not found.")

    article.status = "published"
    article.is_published = True
    article.published_at = datetime.utcnow()
    article.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(article)
    return serialize_article(article, current_user.id)


# ─── Rich Media Gallery & Reactions ──────────────────────────────────────────

@router.post("/articles/{article_id}/media", response_model=MediaGalleryItemOut, status_code=status.HTTP_201_CREATED)
async def add_media_gallery_item(
    article_id: int,
    payload: MediaGalleryItemCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Attach rich photos or video assets to a news story gallery."""
    res = await db.execute(select(News).where(News.id == article_id))
    article = res.scalars().first()
    if not article:
        raise HTTPException(status_code=404, detail="News article not found.")

    if current_user.role not in ["admin", "lecturer"] and article.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Unauthorized to modify this gallery.")

    item = MediaGalleryItem(
        news_id=article.id,
        title=payload.title,
        media_type=payload.media_type,
        media_url=payload.media_url,
        caption=payload.caption,
        sort_order=payload.sort_order,
        created_at=datetime.utcnow(),
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


@router.post("/articles/{article_id}/react")
async def toggle_article_reaction(
    article_id: int,
    reaction_type: str = Query("like", pattern="^(like|applause|insightful)$"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Toggle reader like/reaction on an article."""
    art_res = await db.execute(select(News).where(News.id == article_id))
    article = art_res.scalars().first()
    if not article:
        raise HTTPException(status_code=404, detail="News article not found.")

    rxn_res = await db.execute(
        select(NewsReaction).where(
            and_(
                NewsReaction.news_id == article_id,
                NewsReaction.user_id == current_user.id,
            )
        )
    )
    existing = rxn_res.scalars().first()
    if existing:
        await db.delete(existing)
        article.likes_count = max(0, article.likes_count - 1)
        await db.commit()
        return {"liked": False, "likes_count": article.likes_count}
    else:
        new_rxn = NewsReaction(
            news_id=article_id,
            user_id=current_user.id,
            reaction_type=reaction_type,
            created_at=datetime.utcnow(),
        )
        db.add(new_rxn)
        article.likes_count += 1
        await db.commit()
        return {"liked": True, "likes_count": article.likes_count}


@router.post("/articles/{article_id}/comments", response_model=NewsCommentOut, status_code=status.HTTP_201_CREATED)
async def post_news_comment(
    article_id: int,
    payload: NewsCommentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Post reader commentary on a published article."""
    art_res = await db.execute(select(News).where(News.id == article_id))
    article = art_res.scalars().first()
    if not article:
        raise HTTPException(status_code=404, detail="News article not found.")

    comment = NewsComment(
        news_id=article.id,
        user_id=current_user.id,
        content=payload.content.strip(),
        created_at=datetime.utcnow(),
    )
    db.add(comment)
    await db.commit()
    await db.refresh(comment)

    return NewsCommentOut(
        id=comment.id,
        news_id=comment.news_id,
        user_id=comment.user_id,
        user_name=current_user.full_name,
        content=comment.content,
        created_at=comment.created_at,
    )


# ─── Journalism & Publication Analytics ──────────────────────────────────────

@router.get("/stats", response_model=NewsPublicationStatsOut)
async def get_news_stats(
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    """Institutional media desk overview: total articles, reader impressions, and engagement."""
    res = await db.execute(select(News).where(News.status == "published"))
    all_articles = res.scalars().all()

    tot_articles = len(all_articles)
    tot_views = sum(a.views for a in all_articles)
    tot_likes = sum(a.likes_count for a in all_articles)

    cat_counts: Dict[str, int] = {}
    for a in all_articles:
        cat_name = a.category.value if hasattr(a.category, "value") else str(a.category)
        cat_counts[cat_name] = cat_counts.get(cat_name, 0) + 1

    return NewsPublicationStatsOut(
        total_articles=tot_articles,
        total_views=tot_views,
        total_likes=tot_likes,
        category_breakdown=cat_counts,
    )
