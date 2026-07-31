"""
Site / workflow review portal.

Lets Rudy (or any project owner) spin up a "project" — a set of workflow
pages, each describing one screen/process (UI wireframe, process flow, data
fields, downstream effects) — and share a single token link with reviewers
(management, employees, remote reviewers) with no login required. Reviewers
leave comments tagged by category (Bug / Suggestion / Question / Approval);
Rudy triages them from a staff-gated admin view, and a dedicated suggestions
queue tracks anything tagged "suggestion" until it's resolved.

Deliberately kept self-contained in one router file (models + schemas +
routes), matching the pattern already used in employee_applications.py —
no changes needed to app/models.py or app/schemas.py.

Two HTML pages consume this API (registered as page routes in main.py):
  - web/review.html        public, token-gated reviewer view  (/review/{token})
  - web/review-admin.html  staff-gated triage view             (/review-admin)
"""
from __future__ import annotations

import enum
import json
import logging
import os
import secrets
import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel, Field
from sqlalchemy import Column, DateTime, Enum as SAEnum, ForeignKey, Integer, String, Text, inspect as sa_inspect, text
from sqlalchemy.orm import Session, relationship

from .. import mail
from ..auth import get_current_staff
from ..database import Base, SessionLocal, engine, get_db

log = logging.getLogger("review")

router = APIRouter(prefix="/api/review", tags=["review"])

# Screenshots are committed into the repo (web/review-media/) so they survive
# a redeploy. The upload endpoint below also writes here at runtime for
# convenience — but on hosts with an ephemeral filesystem (Render's default,
# no persistent disk attached), anything written at runtime is lost on the
# next deploy unless it's also committed to git. Baked-in screenshots
# (captured once and committed) are unaffected by this.
_HERE = os.path.dirname(os.path.abspath(__file__))
MEDIA_DIR = os.path.normpath(os.path.join(_HERE, "..", "..", "web", "review-media"))
os.makedirs(MEDIA_DIR, exist_ok=True)
_ALLOWED_IMAGE_EXT = {".png", ".jpg", ".jpeg", ".webp"}


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------
class CommentCategory(str, enum.Enum):
    bug = "bug"
    suggestion = "suggestion"
    question = "question"
    approval = "approval"


class CommentStatus(str, enum.Enum):
    open = "open"
    accepted = "accepted"
    deferred = "deferred"
    rejected = "rejected"
    resolved = "resolved"


class ReviewProject(Base):
    __tablename__ = "review_projects"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    slug = Column(String, unique=True, index=True, nullable=False)
    token = Column(String, unique=True, index=True, nullable=False)
    owner_email = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    pages = relationship("ReviewPage", back_populates="project", cascade="all, delete-orphan", order_by="ReviewPage.order_index")


class ReviewPage(Base):
    __tablename__ = "review_pages"

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("review_projects.id"), nullable=False)
    order_index = Column(Integer, default=0)
    title = Column(String, nullable=False)
    summary = Column(Text, nullable=True)          # short "what this screen is for"
    fields_json = Column(Text, nullable=False, default="[]")  # JSON list of {label,type,note}
    flow_notes = Column(Text, nullable=True)        # process-flow quadrant, plain text/steps
    downstream_notes = Column(Text, nullable=True)  # downstream-effects quadrant
    screenshot_filename = Column(String, nullable=True)  # just the filename, served from /review-media/

    project = relationship("ReviewProject", back_populates="pages")
    comments = relationship("ReviewComment", back_populates="page", cascade="all, delete-orphan")


class ReviewComment(Base):
    __tablename__ = "review_comments"

    id = Column(Integer, primary_key=True)
    page_id = Column(Integer, ForeignKey("review_pages.id"), nullable=False)
    project_id = Column(Integer, ForeignKey("review_projects.id"), nullable=False)  # denormalized for fast queue queries
    author_name = Column(String, nullable=True)
    author_email = Column(String, nullable=True)
    category = Column(SAEnum(CommentCategory), nullable=False, default=CommentCategory.question)
    body = Column(Text, nullable=False)
    status = Column(SAEnum(CommentStatus), nullable=False, default=CommentStatus.open)
    resolved_note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)

    page = relationship("ReviewPage", back_populates="comments")


Base.metadata.create_all(bind=engine)


def _ensure_screenshot_column():
    """create_all only creates missing TABLES, not new columns on tables that
    already exist — so on any deployment where review_pages was created
    before screenshot_filename existed, we need a tiny in-place migration.
    Safe/idempotent on both SQLite and Postgres."""
    insp = sa_inspect(engine)
    if "review_pages" not in insp.get_table_names():
        return
    cols = {c["name"] for c in insp.get_columns("review_pages")}
    if "screenshot_filename" not in cols:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE review_pages ADD COLUMN screenshot_filename VARCHAR"))
        log.info("Migrated review_pages: added screenshot_filename column")


_ensure_screenshot_column()


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
class FieldDef(BaseModel):
    label: str
    type: str = "text"   # text|number|date|select|textarea|checkbox|button|table|readout|section
    note: Optional[str] = None


class ProjectCreate(BaseModel):
    name: str
    slug: str
    owner_email: Optional[str] = None
    description: Optional[str] = None


class ProjectOut(BaseModel):
    id: int
    name: str
    slug: str
    token: str
    owner_email: Optional[str]
    description: Optional[str]
    created_at: datetime
    page_count: int = 0
    open_comment_count: int = 0
    open_suggestion_count: int = 0

    class Config:
        from_attributes = True


class PageCreate(BaseModel):
    project_id: int
    title: str
    summary: Optional[str] = None
    fields: List[FieldDef] = []
    flow_notes: Optional[str] = None
    downstream_notes: Optional[str] = None
    order_index: int = 0


class CommentOut(BaseModel):
    id: int
    page_id: int
    author_name: Optional[str]
    author_email: Optional[str]
    category: CommentCategory
    body: str
    status: CommentStatus
    resolved_note: Optional[str]
    created_at: datetime
    resolved_at: Optional[datetime]

    class Config:
        from_attributes = True


class PageOut(BaseModel):
    id: int
    title: str
    summary: Optional[str]
    fields: List[FieldDef]
    flow_notes: Optional[str]
    downstream_notes: Optional[str]
    order_index: int
    screenshot_url: Optional[str] = None
    comments: List[CommentOut] = []


class ProjectDetailOut(BaseModel):
    id: int
    name: str
    slug: str
    token: str
    owner_email: Optional[str]
    description: Optional[str]
    pages: List[PageOut]


class CommentCreate(BaseModel):
    token: str
    page_id: int
    category: CommentCategory
    body: str = Field(min_length=2)
    author_name: Optional[str] = None
    author_email: Optional[str] = None


class CommentStatusUpdate(BaseModel):
    status: CommentStatus
    resolved_note: Optional[str] = None


class SuggestionOut(BaseModel):
    id: int
    project_name: str
    project_slug: str
    page_title: str
    author_name: Optional[str]
    body: str
    status: CommentStatus
    created_at: datetime
    age_days: int


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _page_to_out(p: ReviewPage) -> PageOut:
    try:
        fields = [FieldDef(**f) for f in json.loads(p.fields_json or "[]")]
    except Exception:
        fields = []
    return PageOut(
        id=p.id, title=p.title, summary=p.summary, fields=fields,
        flow_notes=p.flow_notes, downstream_notes=p.downstream_notes,
        order_index=p.order_index or 0,
        screenshot_url=(f"/review-media/{p.screenshot_filename}" if p.screenshot_filename else None),
        comments=[CommentOut.model_validate(c) for c in sorted(p.comments, key=lambda c: c.created_at or datetime.utcnow(), reverse=True)],
    )


def _project_to_detail(proj: ReviewProject) -> ProjectDetailOut:
    pages = sorted(proj.pages, key=lambda p: p.order_index or 0)
    return ProjectDetailOut(
        id=proj.id, name=proj.name, slug=proj.slug, token=proj.token,
        owner_email=proj.owner_email, description=proj.description,
        pages=[_page_to_out(p) for p in pages],
    )


def _notify_new_comment(project_id: int, page_id: int, comment_id: int):
    """Runs in a background task — best effort, never blocks or fails the request."""
    db = SessionLocal()
    try:
        c = db.query(ReviewComment).get(comment_id)
        page = db.query(ReviewPage).get(page_id)
        proj = db.query(ReviewProject).get(project_id)
        if not (c and page and proj):
            return
        to = proj.owner_email or mail.inbox_for("REVIEW_INBOX")
        who = c.author_name or "Anonymous reviewer"
        body = (
            f"New {c.category.value.upper()} comment on \"{proj.name}\" → {page.title}\n\n"
            f"From: {who}" + (f" <{c.author_email}>" if c.author_email else "") + "\n\n"
            f"{c.body}\n\n"
            f"Triage at: /review-admin"
        )
        msg = mail.build_message(
            subject=f"[Review] {c.category.value} on {proj.name} / {page.title}",
            to=to, body=body, reply_to=c.author_email or None,
        )
        mail.send(msg)
    except Exception:
        log.exception("Failed to send review-comment notification email")
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Staff-side: projects & pages
# ---------------------------------------------------------------------------
@router.post("/projects", response_model=ProjectOut, status_code=201)
def create_project(payload: ProjectCreate, db: Session = Depends(get_db), staff=Depends(get_current_staff)):
    if db.query(ReviewProject).filter(ReviewProject.slug == payload.slug).first():
        raise HTTPException(409, f"A project with slug '{payload.slug}' already exists.")
    proj = ReviewProject(
        name=payload.name, slug=payload.slug,
        token=secrets.token_urlsafe(20),
        owner_email=(payload.owner_email or None),
        description=(payload.description or None),
    )
    db.add(proj)
    db.commit()
    db.refresh(proj)
    return ProjectOut(
        id=proj.id, name=proj.name, slug=proj.slug, token=proj.token,
        owner_email=proj.owner_email, description=proj.description, created_at=proj.created_at,
        page_count=0, open_comment_count=0, open_suggestion_count=0,
    )


@router.get("/projects", response_model=List[ProjectOut])
def list_projects(db: Session = Depends(get_db), staff=Depends(get_current_staff)):
    out = []
    for proj in db.query(ReviewProject).order_by(ReviewProject.created_at.desc()).all():
        open_comments = db.query(ReviewComment).filter(
            ReviewComment.project_id == proj.id, ReviewComment.status == CommentStatus.open
        ).count()
        open_suggestions = db.query(ReviewComment).filter(
            ReviewComment.project_id == proj.id,
            ReviewComment.status == CommentStatus.open,
            ReviewComment.category == CommentCategory.suggestion,
        ).count()
        out.append(ProjectOut(
            id=proj.id, name=proj.name, slug=proj.slug, token=proj.token,
            owner_email=proj.owner_email, description=proj.description, created_at=proj.created_at,
            page_count=len(proj.pages), open_comment_count=open_comments, open_suggestion_count=open_suggestions,
        ))
    return out


@router.get("/projects/id/{project_id}", response_model=ProjectDetailOut)
def get_project_by_id(project_id: int, db: Session = Depends(get_db), staff=Depends(get_current_staff)):
    """Staff drill-in view — by numeric id, includes every comment regardless of status."""
    proj = db.query(ReviewProject).get(project_id)
    if not proj:
        raise HTTPException(404, "Project not found.")
    return _project_to_detail(proj)


@router.post("/pages", response_model=PageOut, status_code=201)
def add_page(payload: PageCreate, db: Session = Depends(get_db), staff=Depends(get_current_staff)):
    proj = db.query(ReviewProject).get(payload.project_id)
    if not proj:
        raise HTTPException(404, "Project not found.")
    page = ReviewPage(
        project_id=proj.id, order_index=payload.order_index, title=payload.title,
        summary=(payload.summary or None),
        fields_json=json.dumps([f.model_dump() for f in payload.fields]),
        flow_notes=(payload.flow_notes or None),
        downstream_notes=(payload.downstream_notes or None),
    )
    db.add(page)
    db.commit()
    db.refresh(page)
    return _page_to_out(page)


@router.post("/pages/{page_id}/screenshot", response_model=PageOut)
def upload_screenshot(page_id: int, file: UploadFile = File(...), db: Session = Depends(get_db), staff=Depends(get_current_staff)):
    """Attach a screenshot image to a workflow page. NOTE: on a host without a
    persistent disk (Render's default), this file is written to the running
    instance only — it will NOT survive the next deploy. For a screenshot to
    stick permanently, commit the file into web/review-media/ in git and
    reference it via seed/add-pages scripts instead."""
    page = db.query(ReviewPage).get(page_id)
    if not page:
        raise HTTPException(404, "Page not found.")
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in _ALLOWED_IMAGE_EXT:
        raise HTTPException(422, f"Unsupported image type '{ext}'. Use png, jpg, jpeg, or webp.")
    filename = f"page-{page_id}-{uuid.uuid4().hex[:8]}{ext}"
    dest = os.path.join(MEDIA_DIR, filename)
    with open(dest, "wb") as out:
        out.write(file.file.read())
    # Clean up the previous image for this page, if any, so we don't leak files.
    if page.screenshot_filename:
        old_path = os.path.join(MEDIA_DIR, page.screenshot_filename)
        if os.path.exists(old_path):
            try:
                os.remove(old_path)
            except OSError:
                pass
    page.screenshot_filename = filename
    db.commit()
    db.refresh(page)
    return _page_to_out(page)


@router.delete("/pages/{page_id}", status_code=204)
def delete_page(page_id: int, db: Session = Depends(get_db), staff=Depends(get_current_staff)):
    page = db.query(ReviewPage).get(page_id)
    if not page:
        raise HTTPException(404, "Page not found.")
    db.delete(page)
    db.commit()
    return None


# ---------------------------------------------------------------------------
# Public: reviewer view (token-gated, no login)
# ---------------------------------------------------------------------------
@router.get("/projects/{token}", response_model=ProjectDetailOut)
def get_project_by_token(token: str, db: Session = Depends(get_db)):
    proj = db.query(ReviewProject).filter(ReviewProject.token == token).first()
    if not proj:
        raise HTTPException(404, "Review link not found or expired.")
    return _project_to_detail(proj)


@router.post("/comments", response_model=CommentOut, status_code=201)
def add_comment(payload: CommentCreate, background: BackgroundTasks, db: Session = Depends(get_db)):
    proj = db.query(ReviewProject).filter(ReviewProject.token == payload.token).first()
    if not proj:
        raise HTTPException(404, "Review link not found or expired.")
    page = db.query(ReviewPage).get(payload.page_id)
    if not page or page.project_id != proj.id:
        raise HTTPException(404, "That workflow page was not found on this project.")
    if not payload.body.strip():
        raise HTTPException(422, "Comment text is required.")

    c = ReviewComment(
        page_id=page.id, project_id=proj.id,
        author_name=(payload.author_name or None),
        author_email=(payload.author_email or None),
        category=payload.category, body=payload.body.strip(),
        status=CommentStatus.open,
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    background.add_task(_notify_new_comment, proj.id, page.id, c.id)
    return CommentOut.model_validate(c)


# ---------------------------------------------------------------------------
# Staff-side: comment triage + suggestions queue
# ---------------------------------------------------------------------------
@router.get("/projects/{project_id}/comments", response_model=List[CommentOut])
def list_project_comments(
    project_id: int,
    category: Optional[CommentCategory] = None,
    status: Optional[CommentStatus] = None,
    db: Session = Depends(get_db),
    staff=Depends(get_current_staff),
):
    q = db.query(ReviewComment).filter(ReviewComment.project_id == project_id)
    if category:
        q = q.filter(ReviewComment.category == category)
    if status:
        q = q.filter(ReviewComment.status == status)
    rows = q.order_by(ReviewComment.created_at.desc()).all()
    return [CommentOut.model_validate(c) for c in rows]


@router.patch("/comments/{comment_id}", response_model=CommentOut)
def update_comment_status(comment_id: int, payload: CommentStatusUpdate, db: Session = Depends(get_db), staff=Depends(get_current_staff)):
    c = db.query(ReviewComment).get(comment_id)
    if not c:
        raise HTTPException(404, "Comment not found.")
    c.status = payload.status
    if payload.resolved_note is not None:
        c.resolved_note = payload.resolved_note
    if payload.status != CommentStatus.open and not c.resolved_at:
        c.resolved_at = datetime.utcnow()
    if payload.status == CommentStatus.open:
        c.resolved_at = None
    db.commit()
    db.refresh(c)
    return CommentOut.model_validate(c)


@router.get("/suggestions", response_model=List[SuggestionOut])
def suggestions_queue(db: Session = Depends(get_db), staff=Depends(get_current_staff)):
    """Every open, category=suggestion comment across all projects — oldest first,
    so anything sitting unresolved bubbles to the top. Pairs with the 30-day
    resolution expectation described in the review-portal SOP."""
    rows = (
        db.query(ReviewComment)
        .filter(ReviewComment.category == CommentCategory.suggestion, ReviewComment.status == CommentStatus.open)
        .order_by(ReviewComment.created_at.asc())
        .all()
    )
    now = datetime.utcnow()
    out = []
    for c in rows:
        page = c.page
        proj = page.project if page else None
        if not (page and proj):
            continue
        age = (now - (c.created_at or now)).days
        out.append(SuggestionOut(
            id=c.id, project_name=proj.name, project_slug=proj.slug, page_title=page.title,
            author_name=c.author_name, body=c.body, status=c.status, created_at=c.created_at, age_days=age,
        ))
    return out
