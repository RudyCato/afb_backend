"""
Lightweight read-only jobs API — surfaces the postings from afb-site/jobs.json
alongside each role's SOPs (looked up in the SOP library). Powers the role
picker + "read this SOP before applying" panel on the public and internal
application forms.

Kept read-only: the source of truth for postings is still afb-site/jobs.json,
edited by hand.
"""
from __future__ import annotations

import json
import os
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db

router = APIRouter(prefix="/jobs", tags=["jobs"])


_HERE = os.path.dirname(os.path.abspath(__file__))
_JOBS_PATH = os.path.normpath(os.path.join(_HERE, "..", "..", "afb-site", "jobs.json"))


def _load_jobs() -> dict:
    if not os.path.exists(_JOBS_PATH):
        raise HTTPException(500, f"jobs.json not found at {_JOBS_PATH}")
    with open(_JOBS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


class JobSopRef(BaseModel):
    code: str
    title: Optional[str] = None
    department: Optional[str] = None
    doc_type: Optional[str] = None
    status: Optional[str] = None
    current_version: Optional[str] = None


class JobOut(BaseModel):
    id: str
    title: str
    department: Optional[str] = None
    type: Optional[str] = None
    shift: Optional[str] = None
    summary: Optional[str] = None
    does: List[str] = []
    needs: List[str] = []
    sop_codes: List[str] = []
    sops: List[JobSopRef] = []


def _resolve_sops(codes: List[str], db: Session) -> List[JobSopRef]:
    """Join a list of SOP codes against the SOP library, so the picker can show
    real titles + status. Unknown codes still return a stub so the UI can flag
    'SOP not found yet — check with the manager'."""
    if not codes:
        return []
    # Import inside the function to avoid a circular import — sops.py imports Base too.
    from .sops import SopDocument
    docs = db.query(SopDocument).filter(SopDocument.code.in_(codes)).all()
    by_code = {d.code: d for d in docs}
    out: List[JobSopRef] = []
    for code in codes:
        d = by_code.get(code)
        if d:
            out.append(JobSopRef(
                code=code, title=d.title, department=d.department,
                doc_type=d.doc_type, status=d.status,
                current_version=d.current_version,
            ))
        else:
            out.append(JobSopRef(code=code, title=None, status="not_found"))
    return out


def _job_row_to_out(row: dict, db: Session) -> JobOut:
    codes = list(row.get("sopCodes") or [])
    return JobOut(
        id=row["id"],
        title=row.get("title", ""),
        department=row.get("department"),
        type=row.get("type"),
        shift=row.get("shift"),
        summary=row.get("summary"),
        does=list(row.get("does") or []),
        needs=list(row.get("needs") or []),
        sop_codes=codes,
        sops=_resolve_sops(codes, db),
    )


@router.get("", response_model=List[JobOut])
def list_jobs(db: Session = Depends(get_db)):
    data = _load_jobs()
    return [_job_row_to_out(row, db) for row in data.get("jobs", [])]


@router.get("/{job_id}", response_model=JobOut)
def get_job(job_id: str, db: Session = Depends(get_db)):
    data = _load_jobs()
    for row in data.get("jobs", []):
        if row.get("id") == job_id:
            return _job_row_to_out(row, db)
    raise HTTPException(404, f"No job with id '{job_id}'.")


@router.get("/{job_id}/sops", response_model=List[JobSopRef])
def sops_for_job(job_id: str, db: Session = Depends(get_db)):
    """Just the SOPs for a role — small payload for the picker."""
    data = _load_jobs()
    for row in data.get("jobs", []):
        if row.get("id") == job_id:
            return _resolve_sops(list(row.get("sopCodes") or []), db)
    raise HTTPException(404, f"No job with id '{job_id}'.")
