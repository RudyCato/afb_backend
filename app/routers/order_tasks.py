from datetime import datetime, date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/order-tasks", tags=["order-tasks"])


def _task_to_out(t: models.OrderTask) -> schemas.OrderTaskOut:
    return schemas.OrderTaskOut(
        id=t.id, order_id=t.order_id, order_number=t.order.order_number,
        task_type=t.task_type, assigned_to=t.assigned_to, assigned_by=t.assigned_by,
        status=t.status, started_at=t.started_at, completed_at=t.completed_at,
        duration_minutes=t.duration_minutes, notes=t.notes, created_at=t.created_at,
    )


@router.post("", response_model=schemas.OrderTaskOut)
def create_task(payload: schemas.OrderTaskCreate, db: Session = Depends(get_db)):
    order = db.query(models.Order).get(payload.order_id)
    if not order:
        raise HTTPException(404, "Order not found")
    task = models.OrderTask(
        order_id=payload.order_id, task_type=payload.task_type,
        assigned_to=payload.assigned_to, assigned_by=payload.assigned_by,
        notes=payload.notes,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return _task_to_out(task)


@router.get("", response_model=list[schemas.OrderTaskOut])
def list_tasks(
    order_id: int | None = None,
    assigned_to: str | None = None,
    status: models.OrderTaskStatus | None = None,
    task_type: models.OrderTaskType | None = None,
    db: Session = Depends(get_db),
):
    q = db.query(models.OrderTask)
    if order_id:
        q = q.filter(models.OrderTask.order_id == order_id)
    if assigned_to:
        q = q.filter(models.OrderTask.assigned_to == assigned_to)
    if status:
        q = q.filter(models.OrderTask.status == status)
    if task_type:
        q = q.filter(models.OrderTask.task_type == task_type)
    rows = q.order_by(models.OrderTask.created_at.desc()).all()
    return [_task_to_out(t) for t in rows]


@router.patch("/{task_id}/start", response_model=schemas.OrderTaskOut)
def start_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(models.OrderTask).get(task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    if task.status == models.OrderTaskStatus.completed:
        raise HTTPException(400, "Task already completed")
    task.status = models.OrderTaskStatus.in_progress
    task.started_at = datetime.utcnow()
    db.commit()
    db.refresh(task)
    return _task_to_out(task)


@router.patch("/{task_id}/complete", response_model=schemas.OrderTaskOut)
def complete_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(models.OrderTask).get(task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    task.completed_at = datetime.utcnow()
    if not task.started_at:
        task.started_at = task.completed_at  # started+completed together if "start" was skipped
    task.duration_minutes = round((task.completed_at - task.started_at).total_seconds() / 60, 1)
    task.status = models.OrderTaskStatus.completed
    db.commit()
    db.refresh(task)
    return _task_to_out(task)


@router.patch("/{task_id}/reassign", response_model=schemas.OrderTaskOut)
def reassign_task(task_id: int, payload: schemas.OrderTaskReassign, db: Session = Depends(get_db)):
    task = db.query(models.OrderTask).get(task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    task.assigned_to = payload.assigned_to
    db.commit()
    db.refresh(task)
    return _task_to_out(task)


@router.get("/staff-board", response_model=list[schemas.StaffBoardEntry])
def staff_board(db: Session = Depends(get_db)):
    """Everyone currently working on something — order tasks and bulk production
    assignments combined — for the dashboard's 'who's doing what' view."""
    entries = []

    order_tasks = db.query(models.OrderTask).filter(
        models.OrderTask.status != models.OrderTaskStatus.completed
    ).all()
    for t in order_tasks:
        entries.append(schemas.StaffBoardEntry(
            packer_name=t.assigned_to, kind="order_task",
            label=f"{t.task_type.value.replace('_',' ').title()} — order {t.order.order_number}",
            status=t.status.value, reference=t.order.order_number,
        ))

    assignments = db.query(models.PackingAssignment).filter(
        models.PackingAssignment.status.in_([models.AssignmentStatus.assigned, models.AssignmentStatus.in_progress])
    ).all()
    for a in assignments:
        entries.append(schemas.StaffBoardEntry(
            packer_name=a.assigned_to, kind="bulk_assignment",
            label=f"Packing {a.qty_assigned - a.qty_completed} more {a.product.name}",
            status=a.status.value, reference=a.product.sku,
        ))

    return sorted(entries, key=lambda e: e.packer_name)


@router.get("/daily-report")
def daily_task_report(report_date: date | None = None, db: Session = Depends(get_db)):
    """End-of-day production report: time spent per task type per staff member."""
    target = report_date or datetime.utcnow().date()
    rows = db.query(models.OrderTask).filter(
        models.OrderTask.status == models.OrderTaskStatus.completed,
        models.OrderTask.completed_at >= datetime.combine(target, datetime.min.time()),
        models.OrderTask.completed_at < datetime.combine(target, datetime.max.time()),
    ).all()

    summary: dict[str, dict] = {}
    for r in rows:
        key = (r.assigned_to, r.task_type.value)
        bucket = summary.setdefault(key, {
            "packer_name": r.assigned_to, "task_type": r.task_type.value,
            "tasks_completed": 0, "total_minutes": 0.0,
        })
        bucket["tasks_completed"] += 1
        bucket["total_minutes"] += r.duration_minutes or 0

    result = list(summary.values())
    for r in result:
        r["total_minutes"] = round(r["total_minutes"], 1)
        r["avg_minutes"] = round(r["total_minutes"] / r["tasks_completed"], 1) if r["tasks_completed"] else 0
    return sorted(result, key=lambda r: (r["packer_name"], r["task_type"]))
