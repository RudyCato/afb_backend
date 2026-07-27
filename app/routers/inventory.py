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
        description=inv.product.description,
        category=inv.product.category,
        location=inv.location,
        warehouse=inv.warehouse,
        aisle=inv.aisle,
        bin_column=inv.bin_column,
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


@router.patch("/{product_id}/location", response_model=schemas.InventoryOut)
def update_location(product_id: int, payload: schemas.InventoryLocationUpdate, db: Session = Depends(get_db)):
    """Edit warehouse/aisle/bin (column) and the min-qty reorder point —
    everything about *where an item lives and when to reorder it*, as
    opposed to /adjust which is about *how much of it there is*."""
    inv = db.query(models.Inventory).filter(models.Inventory.product_id == product_id).first()
    if not inv:
        raise HTTPException(404, "No inventory record for that product")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(inv, field, value)
    # Keep the legacy free-text `location` field roughly in sync for any
    # code/reports that still read it directly.
    parts = [p for p in [inv.warehouse, inv.aisle and f"Aisle {inv.aisle}", inv.bin_column and f"Bin {inv.bin_column}"] if p]
    if parts:
        inv.location = " / ".join(parts)
    inv.last_updated = datetime.utcnow()
    db.commit()
    db.refresh(inv)
    return _to_out(inv)


@router.post("/{product_id}/adjust", response_model=schemas.InventoryOut)
def adjust_inventory(product_id: int, payload: schemas.InventoryAdjust, db: Session = Depends(get_db)):
    inv = db.query(models.Inventory).filter(models.Inventory.product_id == product_id).first()
    if not inv:
        raise HTTPException(404, "No inventory record for that product")

    change_qty = payload.change_qty
    # "removed" always leaves stock, "returned" always adds it back —
    # enforced here too (not just in the UI) so a direct API call can't
    # silently invert what the reason claims.
    if payload.reason == models.InventoryReason.removed:
        change_qty = -abs(change_qty)
    elif payload.reason == models.InventoryReason.returned:
        change_qty = abs(change_qty)

    inv.qty_on_hand += change_qty
    inv.last_updated = datetime.utcnow()
    db.add(models.InventoryTransaction(
        product_id=product_id, change_qty=change_qty,
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
