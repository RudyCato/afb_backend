# app/routers/packing_jobs.py
# SQF-Compliant Production & Packing Job API

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import PackingJob

router = APIRouter(prefix="/packing-jobs", tags=["Packing Jobs"])


# ── Pydantic schemas ──────────────────────────────────────────────────────────

class RawMaterialEntry(BaseModel):
    component: str = ""
    lot_number: str = ""
    expiration_date: str = ""
    allergen_declaration: str = "None"
    quantity_used: float = 0.0
    quantity_unit: str = "lbs"
    qa_signoff: str = ""

class MetalDetectorCheck(BaseModel):
    check_label: str = ""
    time: str = ""
    ferrous_pass: bool = False
    non_ferrous_pass: bool = False
    stainless_pass: bool = False
    rejection_test_pass: bool = False
    operator_initials: str = ""

class QualitySample(BaseModel):
    sample_number: int = 1
    time: str = ""
    gross_wt: float = 0.0
    net_wt: float = 0.0
    seal_pass: bool = False
    label_verified: bool = False
    visual_ok: bool = False
    initials: str = ""

class CorrectiveAction(BaseModel):
    time: str = ""
    nonconformance_description: str = ""
    root_cause: str = ""
    corrective_action: str = ""
    preventive_action: str = ""
    resolved_by: str = ""
    date_resolved: str = ""


class PackingJobCreate(BaseModel):
    # Section 1
    product_name: str
    product_sku: str
    batch_lot_number: str
    production_date: str
    shift: str
    packaging_line_id: Optional[str] = None
    lead_operator_name: Optional[str] = None

    # Section 2
    line_cleared_status: Optional[str] = None
    line_cleared_initials: Optional[str] = None
    surfaces_sanitized_status: Optional[str] = None
    surfaces_sanitized_initials: Optional[str] = None
    allergen_changeover_status: Optional[str] = None
    allergen_changeover_initials: Optional[str] = None
    allergen_swab_status: Optional[str] = None
    allergen_swab_initials: Optional[str] = None

    # Section 3
    raw_materials: List[RawMaterialEntry] = []

    # Section 4
    ccp_type: Optional[str] = None
    metal_detector_log: List[MetalDetectorCheck] = []

    # Section 5
    target_net_weight: Optional[float] = None
    target_net_weight_unit: Optional[str] = None
    tare_weight: Optional[float] = None
    tare_weight_unit: Optional[str] = None
    lot_code_format: Optional[str] = None
    quality_samples: List[QualitySample] = []

    # Section 6
    total_bulk_input_weight: Optional[float] = None
    total_packed_weight: Optional[float] = None
    scrap_waste_weight: Optional[float] = None
    unused_bulk_returned: Optional[float] = None
    variance_percent: Optional[float] = None

    # Section 7
    corrective_actions: List[CorrectiveAction] = []

    # Workflow
    status: str = "draft"
    submitted_by: Optional[str] = None
    notes: Optional[str] = None


class PackingJobUpdate(BaseModel):
    status: Optional[str] = None
    approved_by: Optional[str] = None
    notes: Optional[str] = None
    lead_operator_name: Optional[str] = None
    corrective_actions: Optional[List[CorrectiveAction]] = None
    quality_samples: Optional[List[QualitySample]] = None
    metal_detector_log: Optional[List[MetalDetectorCheck]] = None
    total_bulk_input_weight: Optional[float] = None
    total_packed_weight: Optional[float] = None
    scrap_waste_weight: Optional[float] = None
    unused_bulk_returned: Optional[float] = None
    variance_percent: Optional[float] = None


class PackingJobOut(PackingJobCreate):
    id: int
    created_at: datetime
    updated_at: datetime
    document_id: str
    revision: str
    approved_by: Optional[str] = None

    class Config:
        from_attributes = True


# ── Helpers ───────────────────────────────────────────────────────────────────

def _compute_variance(job: PackingJob) -> Optional[float]:
    try:
        inp = job.total_bulk_input_weight or 0
        out = (job.total_packed_weight or 0) + (job.scrap_waste_weight or 0) + (job.unused_bulk_returned or 0)
        if inp > 0:
            return round(abs(inp - out) / inp * 100, 2)
    except Exception:
        pass
    return None

def _serialize_list(items):
    return [i if isinstance(i, dict) else i.model_dump() for i in items]


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post("/", response_model=PackingJobOut, status_code=status.HTTP_201_CREATED)
def create_packing_job(payload: PackingJobCreate, db: Session = Depends(get_db)):
    data = payload.model_dump()
    for key in ("raw_materials", "metal_detector_log", "quality_samples", "corrective_actions"):
        data[key] = _serialize_list(data[key])

    job = PackingJob(**data)
    if job.variance_percent is None:
        job.variance_percent = _compute_variance(job)

    db.add(job)
    db.commit()
    db.refresh(job)
    return job


@router.get("/", response_model=List[PackingJobOut])
def list_packing_jobs(
    skip: int = 0,
    limit: int = 50,
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
):
    q = db.query(PackingJob)
    if status_filter:
        q = q.filter(PackingJob.status == status_filter)
    return q.order_by(PackingJob.created_at.desc()).offset(skip).limit(limit).all()


@router.get("/{job_id}", response_model=PackingJobOut)
def get_packing_job(job_id: int, db: Session = Depends(get_db)):
    job = db.query(PackingJob).filter(PackingJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Packing job not found")
    return job


@router.patch("/{job_id}", response_model=PackingJobOut)
def update_packing_job(job_id: int, payload: PackingJobUpdate, db: Session = Depends(get_db)):
    job = db.query(PackingJob).filter(PackingJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Packing job not found")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if isinstance(value, list):
            value = _serialize_list(value)
        setattr(job, field, value)

    job.updated_at = datetime.utcnow()
    if any(f in update_data for f in ("total_bulk_input_weight", "total_packed_weight",
                                       "scrap_waste_weight", "unused_bulk_returned")):
        if "variance_percent" not in update_data:
            job.variance_percent = _compute_variance(job)

    db.commit()
    db.refresh(job)
    return job


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_packing_job(job_id: int, db: Session = Depends(get_db)):
    job = db.query(PackingJob).filter(PackingJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Packing job not found")
    db.delete(job)
    db.commit()
