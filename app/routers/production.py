from datetime import datetime, date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/production", tags=["production"])


# ---------- Packers ----------
@router.get("/packers", response_model=list[schemas.PackerOut])
def list_packers(active_only: bool = True, db: Session = Depends(get_db)):
    q = db.query(models.Packer)
    if active_only:
        q = q.filter(models.Packer.active == True)  # noqa: E712
    return q.order_by(models.Packer.name).all()


# ---------- Assignments (packing manager creates, packers work off these) ----------
def _assignment_to_out(a: models.PackingAssignment) -> schemas.PackingAssignmentOut:
    return schemas.PackingAssignmentOut(
        id=a.id, product_id=a.product_id, sku=a.product.sku, product_name=a.product.name,
        qty_assigned=a.qty_assigned, qty_completed=a.qty_completed,
        assigned_to=a.assigned_to, assigned_by=a.assigned_by, status=a.status,
        notes=a.notes, created_at=a.created_at, updated_at=a.updated_at,
    )


@router.post("/assignments", response_model=schemas.PackingAssignmentOut)
def create_assignment(payload: schemas.PackingAssignmentCreate, db: Session = Depends(get_db)):
    product = db.query(models.Product).get(payload.product_id)
    if not product:
        raise HTTPException(404, "Product not found")
    assignment = models.PackingAssignment(
        product_id=payload.product_id, qty_assigned=payload.qty_assigned,
        assigned_to=payload.assigned_to, assigned_by=payload.assigned_by,
        notes=payload.notes,
    )
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return _assignment_to_out(assignment)


@router.get("/assignments", response_model=list[schemas.PackingAssignmentOut])
def list_assignments(
    assigned_to: str | None = None,
    status: models.AssignmentStatus | None = None,
    db: Session = Depends(get_db),
):
    q = db.query(models.PackingAssignment)
    if assigned_to:
        q = q.filter(models.PackingAssignment.assigned_to == assigned_to)
    if status:
        q = q.filter(models.PackingAssignment.status == status)
    rows = q.order_by(models.PackingAssignment.created_at.desc()).all()
    return [_assignment_to_out(a) for a in rows]


@router.patch("/assignments/{assignment_id}", response_model=schemas.PackingAssignmentOut)
def update_assignment_status(assignment_id: int, payload: schemas.AssignmentStatusUpdate, db: Session = Depends(get_db)):
    assignment = db.query(models.PackingAssignment).get(assignment_id)
    if not assignment:
        raise HTTPException(404, "Assignment not found")
    assignment.status = payload.status
    assignment.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(assignment)
    return _assignment_to_out(assignment)


# ---------- Daily production logging (packers log completed work here) ----------
@router.post("/log", response_model=schemas.ProductionLogOut)
def log_production(payload: schemas.ProductionLogCreate, db: Session = Depends(get_db)):
    product = db.query(models.Product).get(payload.product_id)
    if not product:
        raise HTTPException(404, "Product not found")

    assignment = None
    if payload.assignment_id:
        assignment = db.query(models.PackingAssignment).get(payload.assignment_id)
        if not assignment:
            raise HTTPException(404, "Assignment not found")

    log = models.PackerProductionLog(
        assignment_id=payload.assignment_id, product_id=payload.product_id,
        packer_name=payload.packer_name, qty_completed=payload.qty_completed,
        notes=payload.notes,
    )
    db.add(log)

    # completed production adds finished stock back into inventory
    inv = db.query(models.Inventory).filter(models.Inventory.product_id == payload.product_id).first()
    if inv:
        inv.qty_on_hand += payload.qty_completed
        inv.last_updated = datetime.utcnow()
    db.add(models.InventoryTransaction(
        product_id=payload.product_id, change_qty=payload.qty_completed,
        reason=models.InventoryReason.production_completed,
        reference=f"assignment #{payload.assignment_id}" if payload.assignment_id else "ad-hoc production",
    ))

    # update the assignment's progress if this log is tied to one
    if assignment:
        assignment.qty_completed = min(assignment.qty_assigned, assignment.qty_completed + payload.qty_completed)
        assignment.updated_at = datetime.utcnow()
        if assignment.qty_completed >= assignment.qty_assigned:
            assignment.status = models.AssignmentStatus.completed
        elif assignment.status == models.AssignmentStatus.assigned:
            assignment.status = models.AssignmentStatus.in_progress

    db.commit()
    db.refresh(log)
    return schemas.ProductionLogOut(
        id=log.id, assignment_id=log.assignment_id, product_id=log.product_id,
        sku=product.sku, product_name=product.name, packer_name=log.packer_name,
        qty_completed=log.qty_completed, notes=log.notes, logged_at=log.logged_at,
    )


@router.get("/log", response_model=list[schemas.ProductionLogOut])
def list_production_log(
    packer_name: str | None = None,
    log_date: date | None = None,
    db: Session = Depends(get_db),
):
    q = db.query(models.PackerProductionLog)
    if packer_name:
        q = q.filter(models.PackerProductionLog.packer_name == packer_name)
    if log_date:
        q = q.filter(models.PackerProductionLog.logged_at >= datetime.combine(log_date, datetime.min.time()))
        q = q.filter(models.PackerProductionLog.logged_at < datetime.combine(log_date, datetime.max.time()))
    rows = q.order_by(models.PackerProductionLog.logged_at.desc()).all()
    return [
        schemas.ProductionLogOut(
            id=r.id, assignment_id=r.assignment_id, product_id=r.product_id,
            sku=r.product.sku, product_name=r.product.name, packer_name=r.packer_name,
            qty_completed=r.qty_completed, notes=r.notes, logged_at=r.logged_at,
        )
        for r in rows
    ]


@router.get("/summary/today")
def production_summary_today(db: Session = Depends(get_db)):
    """Totals per packer for today — used by the dashboard's daily production panel."""
    today = datetime.utcnow().date()
    rows = (
        db.query(models.PackerProductionLog)
        .filter(models.PackerProductionLog.logged_at >= datetime.combine(today, datetime.min.time()))
        .all()
    )
    totals: dict[str, dict] = {}
    for r in rows:
        t = totals.setdefault(r.packer_name, {"packer_name": r.packer_name, "units_packed": 0, "log_count": 0})
        t["units_packed"] += r.qty_completed
        t["log_count"] += 1
    return sorted(totals.values(), key=lambda x: x["units_packed"], reverse=True)
