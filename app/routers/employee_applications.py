"""
Internal-transfer applications — for existing staff applying for a different
position within AFB (promotion, cross-training, shift change). Distinct from
public job applications so hiring can triage them separately, and so employee
history stays private (never mixed into the external applicant queue).

Every submission:
  * captures which SOPs the employee acknowledged reading for the new role,
  * emails the hiring inbox (via the shared mail helper),
  * stores the row even if SMTP is offline (never lose an application).
"""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from email.message import EmailMessage
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.orm import Session

from .. import mail
from ..database import Base, engine, get_db

log = logging.getLogger("employee_applications")

router = APIRouter(prefix="/employee-applications", tags=["employee-applications"])


# --------------------------------------------------------------------------- model
class EmployeeApplication(Base):
    __tablename__ = "employee_applications"

    id = Column(Integer, primary_key=True, index=True)
    submitted_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Who is applying
    employee_name = Column(String(160), nullable=False)
    employee_email = Column(String(160), nullable=False, index=True)
    employee_phone = Column(String(40))
    current_role = Column(String(120), nullable=False)
    current_department = Column(String(120))
    hire_date = Column(String(30))         # free-text — some staff don't remember exact date

    # What they want
    applying_for_role = Column(String(120), nullable=False)   # matches jobs.json title
    applying_for_role_id = Column(String(80))                  # matches jobs.json id
    applying_for_department = Column(String(120))
    earliest_start = Column(String(60))
    shift_preference = Column(String(60))

    # Why + context
    reason = Column(Text, nullable=False)             # "Why do you want this role?"
    relevant_experience = Column(Text)
    supervisor_name = Column(String(160))              # someone we can ask about them

    # SOP acknowledgment — stored as JSON string list of SOP codes the applicant
    # confirmed reading. If a role has 3 SOPs, we expect 3 codes here.
    acknowledged_sop_codes = Column(Text)              # JSON array

    status = Column(String(40), default="submitted", index=True)   # submitted|under_review|approved|declined|withdrawn
    notes = Column(Text)                               # HR reviewer notes

    source_ip = Column(String(64))


Base.metadata.create_all(bind=engine)


# --------------------------------------------------------------------------- schemas
class EmployeeApplicationCreate(BaseModel):
    employee_name: str
    employee_email: EmailStr
    employee_phone: Optional[str] = None
    current_role: str
    current_department: Optional[str] = None
    hire_date: Optional[str] = None

    applying_for_role: str
    applying_for_role_id: Optional[str] = None
    applying_for_department: Optional[str] = None
    earliest_start: Optional[str] = None
    shift_preference: Optional[str] = None

    reason: str
    relevant_experience: Optional[str] = None
    supervisor_name: Optional[str] = None
    acknowledged_sop_codes: List[str] = []


class EmployeeApplicationOut(BaseModel):
    id: int
    submitted_at: datetime
    employee_name: str
    employee_email: str
    employee_phone: Optional[str]
    current_role: str
    current_department: Optional[str]
    hire_date: Optional[str]
    applying_for_role: str
    applying_for_role_id: Optional[str]
    applying_for_department: Optional[str]
    earliest_start: Optional[str]
    shift_preference: Optional[str]
    reason: str
    relevant_experience: Optional[str]
    supervisor_name: Optional[str]
    acknowledged_sop_codes: List[str] = []
    status: str
    notes: Optional[str]


class EmployeeApplicationStatusUpdate(BaseModel):
    status: str
    notes: Optional[str] = None


def _to_out(row: EmployeeApplication) -> EmployeeApplicationOut:
    codes: List[str] = []
    if row.acknowledged_sop_codes:
        try:
            parsed = json.loads(row.acknowledged_sop_codes)
            if isinstance(parsed, list):
                codes = [str(c) for c in parsed]
        except (json.JSONDecodeError, TypeError):
            codes = []
    return EmployeeApplicationOut(
        id=row.id, submitted_at=row.submitted_at,
        employee_name=row.employee_name, employee_email=row.employee_email,
        employee_phone=row.employee_phone, current_role=row.current_role,
        current_department=row.current_department, hire_date=row.hire_date,
        applying_for_role=row.applying_for_role, applying_for_role_id=row.applying_for_role_id,
        applying_for_department=row.applying_for_department,
        earliest_start=row.earliest_start, shift_preference=row.shift_preference,
        reason=row.reason, relevant_experience=row.relevant_experience,
        supervisor_name=row.supervisor_name, acknowledged_sop_codes=codes,
        status=row.status, notes=row.notes,
    )


# --------------------------------------------------------------------------- mail
def _email_hr(row: EmployeeApplication):
    """Best-effort notification — never blocks or fails the save."""
    lines = [
        f"Internal transfer request — {row.applying_for_role}",
        "",
        f"Employee          {row.employee_name}",
        f"Current role      {row.current_role} ({row.current_department or 'no dept'})",
        f"Hire date         {row.hire_date or '—'}",
        f"Contact           {row.employee_email} · {row.employee_phone or '—'}",
        f"Supervisor ref    {row.supervisor_name or '—'}",
        "",
        f"Applying for      {row.applying_for_role} ({row.applying_for_department or 'no dept'})",
        f"Earliest start    {row.earliest_start or '—'}",
        f"Shift preference  {row.shift_preference or '—'}",
        "",
        "Why they want this role:",
        row.reason or "(not given)",
        "",
        "Relevant experience:",
        row.relevant_experience or "(not given)",
        "",
        "SOPs acknowledged: " + (row.acknowledged_sop_codes or "(none — check whether the role has any)"),
        "",
        f"Submitted         {row.submitted_at:%Y-%m-%d %H:%M UTC}",
        f"Record ID         {row.id}",
    ]
    msg = mail.build_message(
        subject=f"[Internal] {row.applying_for_role} — {row.employee_name}",
        to=mail.inbox_for("HIRING_INBOX"),
        body="\n".join(lines),
        reply_to=f"{row.employee_name} <{row.employee_email}>",
    )
    mail.send(msg)


def _email_ack(row: EmployeeApplication):
    body = (
        f"Hi {row.employee_name.split(' ')[0]},\n\n"
        f"We received your internal application for the {row.applying_for_role} role. "
        f"Your current supervisor and HR will review it and get back to you shortly.\n\n"
        f"— American Food & Beverage HR"
    )
    msg = mail.build_message(
        subject=f"We received your internal application — {row.applying_for_role}",
        to=row.employee_email,
        body=body,
    )
    mail.send(msg)


# --------------------------------------------------------------------------- routes
@router.post("", response_model=EmployeeApplicationOut, status_code=201)
def submit(payload: EmployeeApplicationCreate, db: Session = Depends(get_db)):
    if len((payload.reason or "").strip()) < 20:
        raise HTTPException(422, "Please give a fuller reason (at least 20 characters) so HR can evaluate the request.")

    row = EmployeeApplication(
        employee_name=payload.employee_name.strip(),
        employee_email=str(payload.employee_email).strip(),
        employee_phone=(payload.employee_phone or "").strip() or None,
        current_role=payload.current_role.strip(),
        current_department=(payload.current_department or "").strip() or None,
        hire_date=(payload.hire_date or "").strip() or None,
        applying_for_role=payload.applying_for_role.strip(),
        applying_for_role_id=(payload.applying_for_role_id or "").strip() or None,
        applying_for_department=(payload.applying_for_department or "").strip() or None,
        earliest_start=(payload.earliest_start or "").strip() or None,
        shift_preference=(payload.shift_preference or "").strip() or None,
        reason=payload.reason.strip(),
        relevant_experience=(payload.relevant_experience or "").strip() or None,
        supervisor_name=(payload.supervisor_name or "").strip() or None,
        acknowledged_sop_codes=json.dumps(payload.acknowledged_sop_codes or []),
    )
    db.add(row)
    db.commit()
    db.refresh(row)

    # Best-effort email — never fail the request if SMTP is down.
    try:
        _email_hr(row)
    except Exception:
        log.exception("HR notification failed for employee application %s", row.id)
    try:
        _email_ack(row)
    except Exception:
        log.exception("Applicant ack failed for employee application %s", row.id)

    return _to_out(row)


@router.get("", response_model=list[EmployeeApplicationOut])
def list_applications(
    status: Optional[str] = None,
    limit: int = 200,
    db: Session = Depends(get_db),
):
    q = db.query(EmployeeApplication)
    if status:
        q = q.filter(EmployeeApplication.status == status)
    rows = q.order_by(EmployeeApplication.submitted_at.desc()).limit(limit).all()
    return [_to_out(r) for r in rows]


@router.patch("/{application_id}", response_model=EmployeeApplicationOut)
def update_status(application_id: int, payload: EmployeeApplicationStatusUpdate,
                  db: Session = Depends(get_db)):
    row = db.query(EmployeeApplication).get(application_id)
    if not row:
        raise HTTPException(404, "Employee application not found.")
    row.status = payload.status
    if payload.notes is not None:
        row.notes = payload.notes
    db.commit()
    db.refresh(row)
    return _to_out(row)
