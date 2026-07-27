"""
SOP library, acknowledgments, training records and cleaning logs.

Design rules, all of which exist because an auditor will eventually read this:

  * Document bodies are versioned and append-only. Editing a document writes a
    NEW version; the old one is retained and stays readable.
  * An acknowledgment is bound to a specific version. If the document changes,
    prior acknowledgments do not carry forward — people must read the new one.
  * Nothing is ever silently overwritten or deleted. Retirement is a status.
  * Fields the source documents do not contain are stored as NULL, never guessed.

Seed with:  python -m app.seed_sops   (reads sops.json)
"""

import json
import os
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import (Column, Integer, String, Text, DateTime, Boolean,
                        ForeignKey, UniqueConstraint, func)
from sqlalchemy.orm import Session, relationship

from ..database import Base, engine, get_db

router = APIRouter(prefix="/api/sops", tags=["sops"])


def _aware(dt):
    """SQLite drops tzinfo even on DateTime(timezone=True); Postgres keeps it.
    Normalize before comparing or the same code passes on one and raises on the other."""
    if dt is None:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _now():
    return datetime.now(timezone.utc)


# --------------------------------------------------------------------- models
class SopDocument(Base):
    __tablename__ = "sop_documents"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(40), unique=True, nullable=False, index=True)
    title = Column(String(300), nullable=False)

    # procedure | role_sop | training_program | form
    doc_type = Column(String(40), nullable=False, index=True)
    # sqf | business  — decides whether it is audit-scoped
    scope = Column(String(20), nullable=False, default="business", index=True)

    department = Column(String(120))
    roles = Column(Text)                      # comma separated role titles

    owner = Column(String(160))               # NULL until AFB fills it in
    approver = Column(String(160))
    effective_date = Column(DateTime(timezone=True))
    review_due = Column(DateTime(timezone=True))

    current_version = Column(String(20))
    status = Column(String(20), default="draft", index=True)   # draft|active|retired

    source_file = Column(String(255))
    generates_record = Column(String(60))     # e.g. "cleaning_log"
    critical_control = Column(Boolean, default=False)
    confidential = Column(Boolean, default=False)
    notes = Column(Text)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    versions = relationship("SopVersion", back_populates="document",
                            order_by="SopVersion.id.desc()")

    @property
    def role_list(self):
        return [r.strip() for r in (self.roles or "").split(",") if r.strip()]

    @property
    def control_gaps(self):
        """What is missing before this can be called a controlled document."""
        gaps = []
        if not self.owner: gaps.append("owner")
        if not self.approver: gaps.append("approver")
        if not self.current_version: gaps.append("version")
        if not self.effective_date: gaps.append("effective date")
        if not self.review_due: gaps.append("review date")
        return gaps


class SopVersion(Base):
    """Append-only. A correction is a new row, never an edit."""
    __tablename__ = "sop_versions"
    __table_args__ = (UniqueConstraint("document_id", "version", name="uq_doc_version"),)

    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey("sop_documents.id"), nullable=False, index=True)
    version = Column(String(20), nullable=False)
    body = Column(Text, nullable=False)           # markdown or structured JSON
    change_note = Column(Text)
    authored_by = Column(String(160))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    approved_by = Column(String(160))
    approved_at = Column(DateTime(timezone=True))
    superseded_at = Column(DateTime(timezone=True))

    document = relationship("SopDocument", back_populates="versions")


class SopAcknowledgment(Base):
    """Read-and-understood, bound to one version. This is a training record."""
    __tablename__ = "sop_acknowledgments"

    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey("sop_documents.id"), nullable=False, index=True)
    version = Column(String(20), nullable=False)
    person = Column(String(160), nullable=False, index=True)
    person_role = Column(String(120))
    acknowledged_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    method = Column(String(40), default="portal")     # portal | paper | in_person
    recorded_by = Column(String(160))                 # set when entered on someone's behalf


class TrainingRecord(Base):
    """Competency, not attendance. Built to the framework in the TTT guide."""
    __tablename__ = "training_records"

    id = Column(Integer, primary_key=True)
    person = Column(String(160), nullable=False, index=True)
    person_role = Column(String(120))
    program = Column(String(160), nullable=False)     # e.g. TRN-SLS-001
    module = Column(String(160))                      # stage or assessment name
    score = Column(Integer)
    pass_mark = Column(Integer)
    passed = Column(Boolean, index=True)
    attempt = Column(Integer, default=1)
    assessed_by = Column(String(160))
    assessed_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime(timezone=True), index=True)
    notes = Column(Text)


class CleaningLog(Base):
    """
    The digital form of the log SOP-PKG-001 step 6 requires.
    Every field here comes from the procedure, not from imagination.
    """
    __tablename__ = "cleaning_logs"

    id = Column(Integer, primary_key=True)
    sop_code = Column(String(40), default="SOP-PKG-001")
    sop_version = Column(String(20))

    area = Column(String(120), nullable=False, default="Packing Room")
    equipment = Column(String(200))
    log_type = Column(String(30), default="changeover", index=True)   # changeover | end_of_day

    product_before = Column(String(200))
    product_after = Column(String(200))
    allergen_changeover = Column(Boolean, default=False, index=True)
    allergens_involved = Column(String(200))

    started_at = Column(DateTime(timezone=True))
    sanitizer_applied_at = Column(DateTime(timezone=True))
    contact_minutes = Column(Integer)
    completed_at = Column(DateTime(timezone=True))

    performed_by = Column(String(160), nullable=False)
    verified_by = Column(String(160))
    test_run_clear = Column(Boolean)
    notes = Column(Text)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    @property
    def contact_time_met(self):
        """SOP requires 10 minutes. Returns None when we can't tell."""
        if self.contact_minutes is None:
            return None
        return self.contact_minutes >= 10


Base.metadata.create_all(bind=engine)


# --------------------------------------------------------------------- schemas
class AckIn(BaseModel):
    person: str
    person_role: str | None = None
    method: str = "portal"
    recorded_by: str | None = None


class VersionIn(BaseModel):
    version: str
    body: str
    change_note: str | None = None
    authored_by: str | None = None


class TrainingIn(BaseModel):
    person: str
    person_role: str | None = None
    program: str
    module: str | None = None
    score: int | None = None
    pass_mark: int | None = None
    attempt: int = 1
    assessed_by: str | None = None
    expires_in_days: int | None = None
    notes: str | None = None


class CleaningIn(BaseModel):
    area: str = "Packing Room"
    equipment: str | None = None
    log_type: str = "changeover"
    product_before: str | None = None
    product_after: str | None = None
    allergen_changeover: bool = False
    allergens_involved: str | None = None
    started_at: datetime | None = None
    sanitizer_applied_at: datetime | None = None
    contact_minutes: int | None = Field(None, ge=0)
    completed_at: datetime | None = None
    performed_by: str
    verified_by: str | None = None
    test_run_clear: bool | None = None
    notes: str | None = None


# ---------------------------------------------------------------------- routes
def _doc_out(d: SopDocument, include_body=False, db: Session | None = None):
    out = {
        "code": d.code, "title": d.title, "docType": d.doc_type, "scope": d.scope,
        "department": d.department, "roles": d.role_list, "owner": d.owner,
        "approver": d.approver, "version": d.current_version, "status": d.status,
        "effectiveDate": d.effective_date, "reviewDue": d.review_due,
        "generatesRecord": d.generates_record, "criticalControl": d.critical_control,
        "confidential": d.confidential, "notes": d.notes,
        "controlGaps": d.control_gaps,
        "reviewOverdue": bool(d.review_due and _aware(d.review_due) < _now()),
    }
    if include_body and d.versions:
        current = d.versions[0]
        out["body"] = current.body
        out["versionHistory"] = [
            {"version": v.version, "authoredBy": v.authored_by,
             "createdAt": v.created_at, "changeNote": v.change_note,
             "approvedBy": v.approved_by}
            for v in d.versions
        ]
    return out


@router.get("")
def list_documents(role: str | None = None, scope: str | None = None,
                   doc_type: str | None = None, status: str | None = "active",
                   db: Session = Depends(get_db)):
    """The library. Pass ?role= to get exactly what one person must read."""
    q = db.query(SopDocument)
    if status:
        q = q.filter(SopDocument.status == status)
    if scope:
        q = q.filter(SopDocument.scope == scope)
    if doc_type:
        q = q.filter(SopDocument.doc_type == doc_type)
    docs = q.order_by(SopDocument.code).all()
    if role:
        docs = [d for d in docs if role in d.role_list]
    return [_doc_out(d) for d in docs]


@router.get("/gaps")
def control_gaps(db: Session = Depends(get_db)):
    """Every document that isn't yet a controlled document, and why."""
    out = []
    for d in db.query(SopDocument).filter(SopDocument.status != "retired").all():
        gaps = d.control_gaps
        overdue = bool(d.review_due and _aware(d.review_due) < _now())
        if gaps or overdue:
            out.append({"code": d.code, "title": d.title, "scope": d.scope,
                        "criticalControl": d.critical_control,
                        "missing": gaps, "reviewOverdue": overdue})
    # SQF-scoped and critical items first — those are the ones an auditor opens
    out.sort(key=lambda r: (r["scope"] != "sqf", not r["criticalControl"], r["code"]))
    return out


@router.post("/{code}/versions", status_code=201)
def add_version(code: str, payload: VersionIn, db: Session = Depends(get_db)):
    """Revise a document. Never edits in place — writes a new version."""
    d = db.query(SopDocument).filter(SopDocument.code == code).first()
    if not d:
        raise HTTPException(404, f"No document {code}")
    if db.query(SopVersion).filter(SopVersion.document_id == d.id,
                                   SopVersion.version == payload.version).first():
        raise HTTPException(409, f"Version {payload.version} already exists for {code}")

    now = datetime.now(timezone.utc)
    for v in d.versions:
        if v.superseded_at is None:
            v.superseded_at = now

    db.add(SopVersion(document_id=d.id, version=payload.version, body=payload.body,
                      change_note=payload.change_note, authored_by=payload.authored_by))
    d.current_version = payload.version
    db.commit()
    return {"ok": True, "code": code, "version": payload.version,
            "note": "Existing acknowledgments do not carry to this version."}


@router.post("/{code}/acknowledge", status_code=201)
def acknowledge(code: str, payload: AckIn, db: Session = Depends(get_db)):
    d = db.query(SopDocument).filter(SopDocument.code == code).first()
    if not d:
        raise HTTPException(404, f"No document {code}")
    if not d.current_version:
        raise HTTPException(409,
            f"{code} has no version number yet. Assign one before collecting acknowledgments — "
            "an acknowledgment that isn't bound to a version proves nothing.")

    row = SopAcknowledgment(document_id=d.id, version=d.current_version,
                            person=payload.person.strip(), person_role=payload.person_role,
                            method=payload.method, recorded_by=payload.recorded_by)
    db.add(row)
    db.commit()
    return {"ok": True, "code": code, "version": d.current_version, "person": row.person}


@router.get("/{code}/acknowledgments")
def list_acknowledgments(code: str, current_only: bool = True, db: Session = Depends(get_db)):
    d = db.query(SopDocument).filter(SopDocument.code == code).first()
    if not d:
        raise HTTPException(404, f"No document {code}")
    q = db.query(SopAcknowledgment).filter(SopAcknowledgment.document_id == d.id)
    if current_only and d.current_version:
        q = q.filter(SopAcknowledgment.version == d.current_version)
    return {"code": code, "currentVersion": d.current_version,
            "acknowledgments": [
                {"person": a.person, "role": a.person_role, "version": a.version,
                 "at": a.acknowledged_at, "method": a.method}
                for a in q.order_by(SopAcknowledgment.acknowledged_at.desc()).all()]}


@router.get("/person/{person}/outstanding")
def outstanding_for_person(person: str, role: str | None = None,
                           db: Session = Depends(get_db)):
    """What this person still has to read. Drives the portal's to-do list."""
    docs = db.query(SopDocument).filter(SopDocument.status == "active").all()
    if role:
        docs = [d for d in docs if role in d.role_list]
    done = {
        (a.document_id, a.version)
        for a in db.query(SopAcknowledgment).filter(
            func.lower(SopAcknowledgment.person) == person.lower()).all()
    }
    out = []
    for d in docs:
        if not d.current_version:
            out.append({"code": d.code, "title": d.title, "reason": "no version assigned"})
        elif (d.id, d.current_version) not in done:
            out.append({"code": d.code, "title": d.title, "version": d.current_version,
                        "reason": "not acknowledged", "criticalControl": d.critical_control})
    return {"person": person, "outstanding": out}


# ------------------------------------------------------------- training records
@router.post("/training", status_code=201)
def add_training(payload: TrainingIn, db: Session = Depends(get_db)):
    passed = None
    if payload.score is not None and payload.pass_mark is not None:
        passed = payload.score >= payload.pass_mark
    expires = None
    if payload.expires_in_days:
        expires = datetime.now(timezone.utc) + timedelta(days=payload.expires_in_days)

    row = TrainingRecord(person=payload.person.strip(), person_role=payload.person_role,
                         program=payload.program, module=payload.module,
                         score=payload.score, pass_mark=payload.pass_mark, passed=passed,
                         attempt=payload.attempt, assessed_by=payload.assessed_by,
                         expires_at=expires, notes=payload.notes)
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"ok": True, "id": row.id, "passed": passed, "expiresAt": expires}


@router.get("/training/expiring")
def expiring_training(days: int = Query(60, ge=1, le=365), db: Session = Depends(get_db)):
    cutoff = _now() + timedelta(days=days)
    rows = (db.query(TrainingRecord)
              .filter(TrainingRecord.expires_at.isnot(None),
                      TrainingRecord.expires_at <= cutoff,
                      TrainingRecord.passed.is_(True))
              .order_by(TrainingRecord.expires_at).all())
    now = _now()
    return [{"person": r.person, "program": r.program, "module": r.module,
             "expiresAt": r.expires_at,
             "expired": _aware(r.expires_at) < now} for r in rows]


# --------------------------------------------------------------- cleaning logs
@router.post("/cleaning-logs", status_code=201)
def add_cleaning_log(payload: CleaningIn, db: Session = Depends(get_db)):
    sop = db.query(SopDocument).filter(SopDocument.code == "SOP-PKG-001").first()
    row = CleaningLog(sop_version=sop.current_version if sop else None,
                      **payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)

    warnings = []
    if row.contact_time_met is False:
        warnings.append(
            f"Sanitizer contact time recorded as {row.contact_minutes} minutes. "
            "SOP-PKG-001 step 4 requires 10.")
    if row.contact_minutes is None:
        warnings.append("No sanitizer contact time recorded.")
    if row.allergen_changeover and not row.verified_by:
        warnings.append("Allergen changeover with no second-person verification.")
    if row.test_run_clear is False:
        warnings.append("Test run not clear — line should not have restarted.")

    return {"ok": True, "id": row.id, "warnings": warnings}


@router.get("/cleaning-logs")
def list_cleaning_logs(start: datetime | None = None, end: datetime | None = None,
                       allergen_only: bool = False, limit: int = 200,
                       db: Session = Depends(get_db)):
    """Date-range pull for an audit. Everything an auditor asks for in one call."""
    q = db.query(CleaningLog)
    if start: q = q.filter(CleaningLog.completed_at >= start)
    if end:   q = q.filter(CleaningLog.completed_at <= end)
    if allergen_only: q = q.filter(CleaningLog.allergen_changeover.is_(True))
    rows = q.order_by(CleaningLog.completed_at.desc()).limit(min(limit, 1000)).all()
    return [{
        "id": r.id, "sop": f"{r.sop_code} v{r.sop_version or '—'}",
        "area": r.area, "equipment": r.equipment, "type": r.log_type,
        "productBefore": r.product_before, "productAfter": r.product_after,
        "allergenChangeover": r.allergen_changeover, "allergens": r.allergens_involved,
        "startedAt": r.started_at, "completedAt": r.completed_at,
        "contactMinutes": r.contact_minutes, "contactTimeMet": r.contact_time_met,
        "performedBy": r.performed_by, "verifiedBy": r.verified_by,
        "testRunClear": r.test_run_clear, "notes": r.notes,
    } for r in rows]


# Declared last on purpose: a literal path like /cleaning-logs would otherwise
# be captured by /{code}.
@router.get("/{code}")
def get_document(code: str, db: Session = Depends(get_db)):
    d = db.query(SopDocument).filter(SopDocument.code == code).first()
    if not d:
        raise HTTPException(404, f"No document {code}")
    return _doc_out(d, include_body=True, db=db)


# ------------------------------------------------------------------------ seed
def seed_from_json(path: str | None = None, db: Session | None = None):
    """Idempotent. Existing documents are left alone; only new codes are added."""
    path = path or os.path.join(os.path.dirname(__file__), "..", "sops.json")
    data = json.load(open(path, encoding="utf-8"))

    own_session = db is None
    if own_session:
        from ..database import SessionLocal
        db = SessionLocal()

    added = []
    try:
        for d in data["documents"]:
            if db.query(SopDocument).filter(SopDocument.code == d["code"]).first():
                continue
            unset = lambda v: None if v in (None, "UNSET", "") else v
            doc = SopDocument(
                code=d["code"], title=d["title"], doc_type=d["docType"],
                scope=d.get("scope", "business"), department=d.get("department"),
                roles=", ".join(d.get("roles", [])),
                owner=unset(d.get("owner")), approver=unset(d.get("approver")),
                current_version=unset(d.get("version")),
                # effective_date / review_due stay NULL until a human signs
                status=d.get("status", "draft"), source_file=d.get("sourceFile"),
                generates_record=d.get("generatesRecord"),
                critical_control=d.get("criticalControl", False),
                confidential=d.get("confidential", False),
                notes=d.get("notes"),
            )
            db.add(doc)
            db.flush()
            body = d.get("body") or json.dumps(
                {k: v for k, v in d.items() if k not in ("code", "title", "docType", "scope")},
                indent=2)
            db.add(SopVersion(document_id=doc.id,
                              version=doc.current_version or "0.0-imported",
                              body=body, change_note="Imported from source file",
                              authored_by="import"))
            added.append(d["code"])
        db.commit()
    finally:
        if own_session:
            db.close()
    return added
