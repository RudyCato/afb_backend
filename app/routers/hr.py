"""
HR / Associate Portal router
Handles: associate profiles, training modules & completions, self-evaluations,
inter-staff messaging, and company announcements.

Access pattern
--------------
  admin / hr_admin / manager  →  full read-write across all associates
  associate / packer          →  read-write on own records only
"""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..auth import get_current_staff
from ..database import get_db
from .. import models

router = APIRouter(prefix="/hr", tags=["hr"])

# ── helpers ──────────────────────────────────────────────────────────────────

HR_ADMIN_ROLES = {models.StaffRole.admin, models.StaffRole.manager, models.StaffRole.hr_admin}


def _is_hr_admin(staff: models.StaffUser) -> bool:
    return staff.role in HR_ADMIN_ROLES


def _require_hr_admin(staff: models.StaffUser):
    if not _is_hr_admin(staff):
        raise HTTPException(403, "HR admin access required")


def _me_or_admin(staff: models.StaffUser, target_staff_id: int):
    """Raise 403 unless the caller is an HR admin OR is accessing their own record."""
    if not _is_hr_admin(staff) and staff.id != target_staff_id:
        raise HTTPException(403, "Access denied")


def _profile_dict(p: models.AssociateProfile, include_staff: bool = True) -> dict:
    d = {
        "id": p.id,
        "staff_id": p.staff_id,
        "employee_id": p.employee_id,
        "department": p.department,
        "position": p.position,
        "hire_date": p.hire_date.isoformat() if p.hire_date else None,
        "status": p.status,
        "phone": p.phone,
        "address": p.address,
        "ec_name": p.ec_name,
        "ec_phone": p.ec_phone,
        "ec_relation": p.ec_relation,
        "bio": p.bio,
        "photo_url": p.photo_url,
        "skills": p.skills or [],
        "certifications": p.certifications or [],
        "onboarding_completed": p.onboarding_completed,
        "onboarding_completed_at": p.onboarding_completed_at.isoformat() if p.onboarding_completed_at else None,
        "onboarding_notes": p.onboarding_notes,
        "notes": p.notes,
        "created_at": p.created_at.isoformat() if p.created_at else None,
        "updated_at": p.updated_at.isoformat() if p.updated_at else None,
    }
    if include_staff and p.staff:
        d["full_name"] = p.staff.full_name
        d["username"] = p.staff.username
        d["role"] = p.staff.role.value
        d["active"] = p.staff.active
    return d


def _module_dict(m: models.TrainingModule) -> dict:
    return {
        "id": m.id,
        "code": m.code,
        "title": m.title,
        "category": m.category,
        "description": m.description,
        "content_url": m.content_url,
        "estimated_minutes": m.estimated_minutes,
        "passing_score": m.passing_score,
        "is_required": m.is_required,
        "required_roles": m.required_roles or [],
        "sqf_cert_module": m.sqf_cert_module,
        "cert_valid_days": m.cert_valid_days,
        "active": m.active,
        "created_at": m.created_at.isoformat() if m.created_at else None,
    }


def _completion_dict(c: models.TrainingCompletion) -> dict:
    return {
        "id": c.id,
        "staff_id": c.staff_id,
        "staff_name": c.staff.full_name if c.staff else None,
        "module_id": c.module_id,
        "module_code": c.module.code if c.module else None,
        "module_title": c.module.title if c.module else None,
        "completed_at": c.completed_at.isoformat() if c.completed_at else None,
        "score": c.score,
        "passed": c.passed,
        "certified_until": c.certified_until.isoformat() if c.certified_until else None,
        "instructor": c.instructor,
        "method": c.method,
        "notes": c.notes,
    }


def _eval_dict(e: models.SelfEvaluation) -> dict:
    return {
        "id": e.id,
        "staff_id": e.staff_id,
        "staff_name": e.staff.full_name if e.staff else None,
        "period": e.period,
        "submitted_at": e.submitted_at.isoformat() if e.submitted_at else None,
        "ratings": e.ratings or {},
        "strengths": e.strengths,
        "improvements": e.improvements,
        "goals": e.goals,
        "comments": e.comments,
        "reviewed_by": e.reviewed_by,
        "reviewed_at": e.reviewed_at.isoformat() if e.reviewed_at else None,
        "manager_comments": e.manager_comments,
        "overall_rating": e.overall_rating,
    }


def _msg_dict(m: models.HRMessage) -> dict:
    return {
        "id": m.id,
        "from_staff_id": m.from_staff_id,
        "from_name": m.from_staff.full_name if m.from_staff else None,
        "to_staff_id": m.to_staff_id,
        "to_name": m.to_staff.full_name if m.to_staff else None,
        "subject": m.subject,
        "body": m.body,
        "message_type": m.message_type,
        "status": m.status,
        "priority": m.priority,
        "request_dates": m.request_dates,
        "request_reason": m.request_reason,
        "response_body": m.response_body,
        "responded_by": m.responded_by,
        "responded_at": m.responded_at.isoformat() if m.responded_at else None,
        "created_at": m.created_at.isoformat() if m.created_at else None,
        "read_at": m.read_at.isoformat() if m.read_at else None,
    }


def _ann_dict(a: models.HRAnnouncement) -> dict:
    return {
        "id": a.id,
        "title": a.title,
        "body": a.body,
        "category": a.category,
        "emoji": a.emoji,
        "author": a.author,
        "pinned": a.pinned,
        "active": a.active,
        "posted_at": a.posted_at.isoformat() if a.posted_at else None,
        "expires_at": a.expires_at.isoformat() if a.expires_at else None,
    }


# ── /hr/me — current user identity + profile ─────────────────────────────────

@router.get("/me")
def hr_me(staff: models.StaffUser = Depends(get_current_staff), db: Session = Depends(get_db)):
    profile = db.query(models.AssociateProfile).filter(
        models.AssociateProfile.staff_id == staff.id
    ).first()
    return {
        "id": staff.id,
        "username": staff.username,
        "full_name": staff.full_name,
        "role": staff.role.value,
        "is_hr_admin": _is_hr_admin(staff),
        "profile": _profile_dict(profile, include_staff=False) if profile else None,
    }


# ── Associate Profiles ────────────────────────────────────────────────────────

@router.get("/associates")
def list_associates(
    status: str | None = None,
    department: str | None = None,
    db: Session = Depends(get_db),
    staff: models.StaffUser = Depends(get_current_staff),
):
    _require_hr_admin(staff)
    q = db.query(models.AssociateProfile)
    if status:
        q = q.filter(models.AssociateProfile.status == status)
    if department:
        q = q.filter(models.AssociateProfile.department == department)
    rows = q.order_by(models.AssociateProfile.created_at.desc()).all()
    return [_profile_dict(p) for p in rows]


@router.post("/associates", status_code=201)
def create_associate_profile(
    payload: dict,
    db: Session = Depends(get_db),
    staff: models.StaffUser = Depends(get_current_staff),
):
    _require_hr_admin(staff)
    target_staff_id = payload.get("staff_id")
    if not target_staff_id:
        raise HTTPException(400, "staff_id is required")
    existing = db.query(models.AssociateProfile).filter(
        models.AssociateProfile.staff_id == target_staff_id
    ).first()
    if existing:
        raise HTTPException(409, "Profile already exists for this staff member")

    from datetime import date
    hire_str = payload.get("hire_date")
    hire_date = None
    if hire_str:
        try:
            hire_date = date.fromisoformat(hire_str)
        except ValueError:
            pass

    p = models.AssociateProfile(
        staff_id=target_staff_id,
        employee_id=payload.get("employee_id"),
        department=payload.get("department"),
        position=payload.get("position"),
        hire_date=hire_date,
        status=payload.get("status", "active"),
        phone=payload.get("phone"),
        address=payload.get("address"),
        ec_name=payload.get("ec_name"),
        ec_phone=payload.get("ec_phone"),
        ec_relation=payload.get("ec_relation"),
        bio=payload.get("bio"),
        photo_url=payload.get("photo_url"),
        skills=payload.get("skills", []),
        certifications=payload.get("certifications", []),
        onboarding_completed=payload.get("onboarding_completed", False),
        notes=payload.get("notes"),
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return _profile_dict(p)


@router.get("/associates/me")
def my_profile(staff: models.StaffUser = Depends(get_current_staff), db: Session = Depends(get_db)):
    p = db.query(models.AssociateProfile).filter(
        models.AssociateProfile.staff_id == staff.id
    ).first()
    if not p:
        raise HTTPException(404, "No profile found — ask HR to create one.")
    return _profile_dict(p)


@router.get("/associates/{profile_id}")
def get_associate(
    profile_id: int,
    db: Session = Depends(get_db),
    staff: models.StaffUser = Depends(get_current_staff),
):
    p = db.query(models.AssociateProfile).get(profile_id)
    if not p:
        raise HTTPException(404, "Profile not found")
    _me_or_admin(staff, p.staff_id)
    return _profile_dict(p)


@router.patch("/associates/{profile_id}")
def update_associate(
    profile_id: int,
    payload: dict,
    db: Session = Depends(get_db),
    staff: models.StaffUser = Depends(get_current_staff),
):
    p = db.query(models.AssociateProfile).get(profile_id)
    if not p:
        raise HTTPException(404, "Profile not found")
    _me_or_admin(staff, p.staff_id)

    # Associates can edit their own bio/phone/address/emergency contact only
    # HR admins can edit everything
    admin_only_fields = {"employee_id", "department", "position", "hire_date",
                         "status", "onboarding_completed", "onboarding_notes", "notes"}

    from datetime import date
    for field, value in payload.items():
        if field in admin_only_fields and not _is_hr_admin(staff):
            continue  # silently skip — associates can't change these
        if field == "hire_date":
            try:
                value = date.fromisoformat(value) if value else None
            except ValueError:
                continue
        if field == "onboarding_completed" and value and not p.onboarding_completed:
            p.onboarding_completed_at = datetime.utcnow()
        if hasattr(p, field):
            setattr(p, field, value)

    p.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(p)
    return _profile_dict(p)


# ── Training Modules ──────────────────────────────────────────────────────────

@router.get("/training/modules")
def list_modules(
    category: str | None = None,
    active_only: bool = True,
    db: Session = Depends(get_db),
    staff: models.StaffUser = Depends(get_current_staff),
):
    q = db.query(models.TrainingModule)
    if active_only:
        q = q.filter(models.TrainingModule.active == True)  # noqa: E712
    if category:
        q = q.filter(models.TrainingModule.category == category)
    return [_module_dict(m) for m in q.order_by(models.TrainingModule.code).all()]


@router.post("/training/modules", status_code=201)
def create_module(
    payload: dict,
    db: Session = Depends(get_db),
    staff: models.StaffUser = Depends(get_current_staff),
):
    _require_hr_admin(staff)
    if not payload.get("code") or not payload.get("title"):
        raise HTTPException(400, "code and title are required")
    existing = db.query(models.TrainingModule).filter(
        models.TrainingModule.code == payload["code"]
    ).first()
    if existing:
        raise HTTPException(409, f"Module code {payload['code']} already exists")
    m = models.TrainingModule(
        code=payload["code"],
        title=payload["title"],
        category=payload.get("category", "general"),
        description=payload.get("description"),
        content_url=payload.get("content_url"),
        estimated_minutes=payload.get("estimated_minutes", 30),
        passing_score=payload.get("passing_score", 80),
        is_required=payload.get("is_required", True),
        required_roles=payload.get("required_roles", []),
        sqf_cert_module=payload.get("sqf_cert_module", False),
        cert_valid_days=payload.get("cert_valid_days"),
        active=payload.get("active", True),
    )
    db.add(m)
    db.commit()
    db.refresh(m)
    return _module_dict(m)


@router.patch("/training/modules/{module_id}")
def update_module(
    module_id: int,
    payload: dict,
    db: Session = Depends(get_db),
    staff: models.StaffUser = Depends(get_current_staff),
):
    _require_hr_admin(staff)
    m = db.query(models.TrainingModule).get(module_id)
    if not m:
        raise HTTPException(404, "Module not found")
    for k, v in payload.items():
        if hasattr(m, k):
            setattr(m, k, v)
    db.commit()
    db.refresh(m)
    return _module_dict(m)


# ── Training Completions ──────────────────────────────────────────────────────

@router.get("/training/completions")
def list_completions(
    staff_id: int | None = None,
    module_id: int | None = None,
    db: Session = Depends(get_db),
    staff: models.StaffUser = Depends(get_current_staff),
):
    q = db.query(models.TrainingCompletion)
    if not _is_hr_admin(staff):
        q = q.filter(models.TrainingCompletion.staff_id == staff.id)
    elif staff_id:
        q = q.filter(models.TrainingCompletion.staff_id == staff_id)
    if module_id:
        q = q.filter(models.TrainingCompletion.module_id == module_id)
    return [_completion_dict(c) for c in q.order_by(models.TrainingCompletion.completed_at.desc()).all()]


@router.post("/training/completions", status_code=201)
def record_completion(
    payload: dict,
    db: Session = Depends(get_db),
    staff: models.StaffUser = Depends(get_current_staff),
):
    module_id = payload.get("module_id")
    target_staff_id = payload.get("staff_id", staff.id)

    if not _is_hr_admin(staff) and target_staff_id != staff.id:
        raise HTTPException(403, "Cannot record completions for other associates")

    module = db.query(models.TrainingModule).get(module_id)
    if not module:
        raise HTTPException(404, "Training module not found")

    # Compute certification expiry
    certified_until = None
    if module.cert_valid_days:
        from datetime import timedelta
        certified_until = datetime.utcnow() + timedelta(days=module.cert_valid_days)

    c = models.TrainingCompletion(
        staff_id=target_staff_id,
        module_id=module_id,
        score=payload.get("score"),
        passed=payload.get("passed", True),
        certified_until=certified_until,
        instructor=payload.get("instructor"),
        method=payload.get("method", "self_study"),
        notes=payload.get("notes"),
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    return _completion_dict(c)


@router.get("/training/status/{target_staff_id}")
def training_status(
    target_staff_id: int,
    db: Session = Depends(get_db),
    staff: models.StaffUser = Depends(get_current_staff),
):
    """Return all active modules with completion status for a given associate."""
    _me_or_admin(staff, target_staff_id)

    modules = db.query(models.TrainingModule).filter(
        models.TrainingModule.active == True  # noqa: E712
    ).order_by(models.TrainingModule.code).all()

    completions = db.query(models.TrainingCompletion).filter(
        models.TrainingCompletion.staff_id == target_staff_id
    ).all()
    completed_map: dict[int, models.TrainingCompletion] = {c.module_id: c for c in completions}

    result = []
    for m in modules:
        c = completed_map.get(m.id)
        expired = False
        if c and c.certified_until and c.certified_until < datetime.utcnow():
            expired = True
        result.append({
            **_module_dict(m),
            "completed": c is not None and not expired,
            "completion": _completion_dict(c) if c else None,
            "expired": expired,
        })
    return result


# ── Self Evaluations ──────────────────────────────────────────────────────────

@router.get("/evaluations")
def list_evaluations(
    period: str | None = None,
    db: Session = Depends(get_db),
    staff: models.StaffUser = Depends(get_current_staff),
):
    q = db.query(models.SelfEvaluation)
    if not _is_hr_admin(staff):
        q = q.filter(models.SelfEvaluation.staff_id == staff.id)
    if period:
        q = q.filter(models.SelfEvaluation.period == period)
    return [_eval_dict(e) for e in q.order_by(models.SelfEvaluation.submitted_at.desc()).all()]


@router.post("/evaluations", status_code=201)
def submit_evaluation(
    payload: dict,
    db: Session = Depends(get_db),
    staff: models.StaffUser = Depends(get_current_staff),
):
    period = payload.get("period")
    if not period:
        raise HTTPException(400, "period is required (e.g. 'Q3 2026')")

    # Prevent duplicate submission for same period
    existing = db.query(models.SelfEvaluation).filter(
        models.SelfEvaluation.staff_id == staff.id,
        models.SelfEvaluation.period == period,
    ).first()
    if existing:
        raise HTTPException(409, f"Evaluation already submitted for {period}")

    e = models.SelfEvaluation(
        staff_id=staff.id,
        period=period,
        ratings=payload.get("ratings", {}),
        strengths=payload.get("strengths"),
        improvements=payload.get("improvements"),
        goals=payload.get("goals"),
        comments=payload.get("comments"),
    )
    db.add(e)
    db.commit()
    db.refresh(e)
    return _eval_dict(e)


@router.patch("/evaluations/{eval_id}")
def review_evaluation(
    eval_id: int,
    payload: dict,
    db: Session = Depends(get_db),
    staff: models.StaffUser = Depends(get_current_staff),
):
    _require_hr_admin(staff)
    e = db.query(models.SelfEvaluation).get(eval_id)
    if not e:
        raise HTTPException(404, "Evaluation not found")

    e.reviewed_by      = staff.full_name
    e.reviewed_at      = datetime.utcnow()
    e.manager_comments = payload.get("manager_comments", e.manager_comments)
    e.overall_rating   = payload.get("overall_rating", e.overall_rating)
    db.commit()
    db.refresh(e)
    return _eval_dict(e)


# ── HR Messages ───────────────────────────────────────────────────────────────

@router.get("/messages")
def list_messages(
    message_type: str | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
    staff: models.StaffUser = Depends(get_current_staff),
):
    q = db.query(models.HRMessage)
    if _is_hr_admin(staff):
        # HR admins see all messages directed to HR (to_staff_id IS NULL or to them)
        pass
    else:
        # Associates see only their own messages
        q = q.filter(models.HRMessage.from_staff_id == staff.id)
    if message_type:
        q = q.filter(models.HRMessage.message_type == message_type)
    if status:
        q = q.filter(models.HRMessage.status == status)
    return [_msg_dict(m) for m in q.order_by(models.HRMessage.created_at.desc()).all()]


@router.get("/messages/unread-count")
def unread_count(
    staff: models.StaffUser = Depends(get_current_staff),
    db: Session = Depends(get_db),
):
    if _is_hr_admin(staff):
        count = db.query(models.HRMessage).filter(
            models.HRMessage.status == "pending"
        ).count()
    else:
        count = db.query(models.HRMessage).filter(
            models.HRMessage.from_staff_id == staff.id,
            models.HRMessage.status.in_(["approved", "denied", "read"]),
            models.HRMessage.read_at == None,  # noqa: E711
        ).count()
    return {"count": count}


@router.post("/messages", status_code=201)
def send_message(
    payload: dict,
    db: Session = Depends(get_db),
    staff: models.StaffUser = Depends(get_current_staff),
):
    if not payload.get("subject") or not payload.get("body"):
        raise HTTPException(400, "subject and body are required")
    m = models.HRMessage(
        from_staff_id=staff.id,
        to_staff_id=payload.get("to_staff_id"),
        subject=payload["subject"],
        body=payload["body"],
        message_type=payload.get("message_type", "general"),
        priority=payload.get("priority", "normal"),
        request_dates=payload.get("request_dates"),
        request_reason=payload.get("request_reason"),
    )
    db.add(m)
    db.commit()
    db.refresh(m)
    return _msg_dict(m)


@router.patch("/messages/{msg_id}")
def respond_to_message(
    msg_id: int,
    payload: dict,
    db: Session = Depends(get_db),
    staff: models.StaffUser = Depends(get_current_staff),
):
    m = db.query(models.HRMessage).get(msg_id)
    if not m:
        raise HTTPException(404, "Message not found")

    # HR admin: can change status, add response, mark read
    # Associate: can only mark their own messages as read
    if _is_hr_admin(staff):
        if "status" in payload:
            m.status = payload["status"]
        if "response_body" in payload:
            m.response_body = payload["response_body"]
            m.responded_by  = staff.full_name
            m.responded_at  = datetime.utcnow()
        if payload.get("mark_read"):
            m.read_at = datetime.utcnow()
    else:
        if m.from_staff_id != staff.id:
            raise HTTPException(403, "Access denied")
        if payload.get("mark_read"):
            m.read_at = datetime.utcnow()

    db.commit()
    db.refresh(m)
    return _msg_dict(m)


# ── Announcements ─────────────────────────────────────────────────────────────

@router.get("/announcements")
def list_announcements(
    category: str | None = None,
    include_expired: bool = False,
    db: Session = Depends(get_db),
    staff: models.StaffUser = Depends(get_current_staff),
):
    q = db.query(models.HRAnnouncement).filter(
        models.HRAnnouncement.active == True  # noqa: E712
    )
    if not include_expired:
        q = q.filter(
            (models.HRAnnouncement.expires_at == None) |  # noqa: E711
            (models.HRAnnouncement.expires_at > datetime.utcnow())
        )
    if category:
        q = q.filter(models.HRAnnouncement.category == category)
    rows = q.order_by(
        models.HRAnnouncement.pinned.desc(),
        models.HRAnnouncement.posted_at.desc(),
    ).all()
    return [_ann_dict(a) for a in rows]


@router.post("/announcements", status_code=201)
def create_announcement(
    payload: dict,
    db: Session = Depends(get_db),
    staff: models.StaffUser = Depends(get_current_staff),
):
    _require_hr_admin(staff)
    if not payload.get("title") or not payload.get("body"):
        raise HTTPException(400, "title and body are required")

    expires_at = None
    if payload.get("expires_at"):
        try:
            expires_at = datetime.fromisoformat(payload["expires_at"])
        except ValueError:
            pass

    a = models.HRAnnouncement(
        title=payload["title"],
        body=payload["body"],
        category=payload.get("category", "general"),
        emoji=payload.get("emoji"),
        author=staff.full_name,
        pinned=payload.get("pinned", False),
        active=True,
        expires_at=expires_at,
    )
    db.add(a)
    db.commit()
    db.refresh(a)
    return _ann_dict(a)


@router.patch("/announcements/{ann_id}")
def update_announcement(
    ann_id: int,
    payload: dict,
    db: Session = Depends(get_db),
    staff: models.StaffUser = Depends(get_current_staff),
):
    _require_hr_admin(staff)
    a = db.query(models.HRAnnouncement).get(ann_id)
    if not a:
        raise HTTPException(404, "Announcement not found")
    for k, v in payload.items():
        if k == "expires_at":
            try:
                v = datetime.fromisoformat(v) if v else None
            except ValueError:
                continue
        if hasattr(a, k):
            setattr(a, k, v)
    db.commit()
    db.refresh(a)
    return _ann_dict(a)


@router.delete("/announcements/{ann_id}", status_code=204)
def deactivate_announcement(
    ann_id: int,
    db: Session = Depends(get_db),
    staff: models.StaffUser = Depends(get_current_staff),
):
    _require_hr_admin(staff)
    a = db.query(models.HRAnnouncement).get(ann_id)
    if not a:
        raise HTTPException(404, "Announcement not found")
    a.active = False
    db.commit()


# ── HR Dashboard stats ────────────────────────────────────────────────────────

@router.get("/dashboard")
def hr_dashboard(
    staff: models.StaffUser = Depends(get_current_staff),
    db: Session = Depends(get_db),
):
    _require_hr_admin(staff)

    total_associates   = db.query(models.AssociateProfile).filter(
        models.AssociateProfile.status == "active"
    ).count()
    pending_onboarding = db.query(models.AssociateProfile).filter(
        models.AssociateProfile.onboarding_completed == False,  # noqa: E712
        models.AssociateProfile.status == "active",
    ).count()
    pending_messages   = db.query(models.HRMessage).filter(
        models.HRMessage.status == "pending"
    ).count()
    pending_evals      = db.query(models.SelfEvaluation).filter(
        models.SelfEvaluation.reviewed_by == None  # noqa: E711
    ).count()

    # Expiring certifications (within 30 days)
    from datetime import timedelta
    expiry_window = datetime.utcnow() + timedelta(days=30)
    expiring_certs = db.query(models.TrainingCompletion).filter(
        models.TrainingCompletion.certified_until != None,  # noqa: E711
        models.TrainingCompletion.certified_until < expiry_window,
        models.TrainingCompletion.certified_until > datetime.utcnow(),
    ).count()

    return {
        "total_active_associates": total_associates,
        "pending_onboarding": pending_onboarding,
        "pending_messages": pending_messages,
        "pending_evaluations": pending_evals,
        "expiring_certifications_30d": expiring_certs,
    }
