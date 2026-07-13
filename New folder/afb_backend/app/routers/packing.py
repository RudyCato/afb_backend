from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/orders", tags=["packing"])


@router.post("/{order_number}/packing", response_model=schemas.PackingOut)
def record_packing(order_number: str, payload: schemas.PackingCreate, db: Session = Depends(get_db)):
    order = db.query(models.Order).filter(models.Order.order_number == order_number).first()
    if not order:
        raise HTTPException(404, "Order not found")

    record = models.PackingRecord(
        order_id=order.id, packed_by=payload.packed_by,
        boxes=payload.boxes, notes=payload.notes,
    )
    db.add(record)

    # apply per-item packed quantities if given, else mark everything fully packed
    if payload.item_qty_packed:
        for item_id_str, qty in payload.item_qty_packed.items():
            item = db.query(models.OrderItem).get(int(item_id_str))
            if item and item.order_id == order.id:
                item.qty_packed = min(item.qty_ordered, item.qty_packed + qty)
    else:
        for item in order.items:
            item.qty_packed = item.qty_ordered

    fully_packed = all(i.qty_packed >= i.qty_ordered for i in order.items)
    new_status = models.OrderStatus.packed if fully_packed else models.OrderStatus.packing
    order.status = new_status
    db.add(models.OrderStatusHistory(
        order_id=order.id, status=new_status,
        note=f"Packed by {payload.packed_by} ({payload.boxes} box(es))"
    ))
    db.commit()
    db.refresh(record)
    return record


@router.get("/{order_number}/packing", response_model=list[schemas.PackingOut])
def list_packing(order_number: str, db: Session = Depends(get_db)):
    order = db.query(models.Order).filter(models.Order.order_number == order_number).first()
    if not order:
        raise HTTPException(404, "Order not found")
    return order.packing_records
