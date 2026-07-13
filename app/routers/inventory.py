from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/inventory", tags=["inventory"])


def _to_out(inv: models.Inventory) -> schemas.InventoryOut:
    available = inv.qty_on_hand - inv.qty_reserved
    return schemas.InventoryOut(
        product_id=inv.product_id,
        sku=inv.product.sku,
        name=inv.product.name,
        category=inv.product.category,
        location=inv.location,
        qty_on_hand=inv.qty_on_hand,
        qty_reserved=inv.qty_reserved,
        qty_available=available,
        reorder_threshold=inv.reorder_threshold,
        low_stock=available <= inv.reorder_threshold,
        last_updated=inv.last_updated,
    )


@router.get("", response_model=list[schemas.InventoryOut])
def list_inventory(low_stock_only: bool = False, db: Session = Depends(get_db)):
    rows = db.query(models.Inventory).all()
    out = [_to_out(r) for r in rows]
    if low_stock_only:
        out = [r for r in out if r.low_stock]
    return out


@router.get("/{product_id}", response_model=schemas.InventoryOut)
def get_inventory(product_id: int, db: Session = Depends(get_db)):
    inv = db.query(models.Inventory).filter(models.Inventory.product_id == product_id).first()
    if not inv:
        raise HTTPException(404, "No inventory record for that product")
    return _to_out(inv)


@router.post("/{product_id}/adjust", response_model=schemas.InventoryOut)
def adjust_inventory(product_id: int, payload: schemas.InventoryAdjust, db: Session = Depends(get_db)):
    inv = db.query(models.Inventory).filter(models.Inventory.product_id == product_id).first()
    if not inv:
        raise HTTPException(404, "No inventory record for that product")
    inv.qty_on_hand += payload.change_qty
    inv.last_updated = datetime.utcnow()
    db.add(models.InventoryTransaction(
        product_id=product_id, change_qty=payload.change_qty,
        reason=payload.reason, reference=payload.reference
    ))
    db.commit()
    db.refresh(inv)
    return _to_out(inv)


@router.get("/{product_id}/transactions")
def get_transactions(product_id: int, db: Session = Depends(get_db)):
    rows = (
        db.query(models.InventoryTransaction)
        .filter(models.InventoryTransaction.product_id == product_id)
        .order_by(models.InventoryTransaction.created_at.desc())
        .all()
    )
    return [
        {
            "change_qty": r.change_qty,
            "reason": r.reason,
            "reference": r.reference,
            "created_at": r.created_at,
        }
        for r in rows
    ]
