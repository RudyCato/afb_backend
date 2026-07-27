"""
Receiving intake — logs product coming INTO the building from a vendor / supplier.

Every receipt (unless condition == rejected) also creates a matching
InventoryTransaction (reason=received_stock) and bumps the product's on-hand
quantity in one step.

If put-away location fields are provided and differ from the current Inventory
row, the row is updated so /stock reflects where product physically lives now.

One product per receipt for schema simplicity — a multi-line delivery is
logged as multiple receipts sharing the same vendor / po_number.
"""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/receipts", tags=["receipts"])


def _to_out(r: models.Receipt) -> schemas.ReceiptOut:
    discrepancy = 0
    if r.qty_expected is not None:
        discrepancy = int(r.qty_expected) - int(r.qty_received)
    return schemas.ReceiptOut(
        id=r.id,
        product_id=r.product_id,
        sku=r.product.sku,
        product_name=r.product.name,
        qty_received=r.qty_received,
        qty_expected=r.qty_expected,
        discrepancy=discrepancy,
        vendor=r.vendor,
        po_number=r.po_number,
        lot_code=r.lot_code,
        sell_by_date=r.sell_by_date,
        condition=r.condition,
        temperature_f=r.temperature_f,
        put_away_warehouse=r.put_away_warehouse,
        put_away_aisle=r.put_away_aisle,
        put_away_bin_column=r.put_away_bin_column,
        received_by=r.received_by,
        notes=r.notes,
        created_at=r.created_at,
    )


@router.post("", response_model=schemas.ReceiptOut, status_code=201)
def log_receipt(payload: schemas.ReceiptCreate, db: Session = Depends(get_db)):
    if payload.qty_received <= 0:
        raise HTTPException(422, "Quantity received must be greater than zero.")
    if not (payload.received_by or "").strip():
        raise HTTPException(422, "Received-by (staff name) is required.")

    product = db.query(models.Product).get(payload.product_id)
    if not product:
        raise HTTPException(404, "Product not found.")

    receipt = models.Receipt(
        product_id=payload.product_id,
        qty_received=payload.qty_received,
        qty_expected=payload.qty_expected,
        vendor=(payload.vendor or None),
        po_number=(payload.po_number or None),
        lot_code=(payload.lot_code or None),
        sell_by_date=payload.sell_by_date,
        condition=payload.condition,
        temperature_f=payload.temperature_f,
        put_away_warehouse=(payload.put_away_warehouse or None),
        put_away_aisle=(payload.put_away_aisle or None),
        put_away_bin_column=(payload.put_away_bin_column or None),
        received_by=payload.received_by.strip(),
        notes=(payload.notes or None),
    )
    db.add(receipt)

    # Rejected shipments never enter stock — receipt is logged for the paper
    # trail, but inventory is not touched.
    if payload.condition != models.ReceiptCondition.rejected:
        inv = db.query(models.Inventory).filter(models.Inventory.product_id == payload.product_id).first()
        if inv is None:
            # First time we've seen this product in inventory — create the row so
            # the receipt actually lands somewhere.
            inv = models.Inventory(product_id=payload.product_id, qty_on_hand=0)
            db.add(inv)
            db.flush()
        inv.qty_on_hand = int(inv.qty_on_hand) + payload.qty_received
        inv.last_updated = datetime.utcnow()

        # If put-away fields were provided, they win — that's the physical
        # truth of where the product actually lives now.
        if payload.put_away_warehouse:
            inv.warehouse = payload.put_away_warehouse
        if payload.put_away_aisle:
            inv.aisle = payload.put_away_aisle
        if payload.put_away_bin_column:
            inv.bin_column = payload.put_away_bin_column

        ref_parts = []
        if payload.vendor:
            ref_parts.append(f"vendor {payload.vendor}")
        if payload.po_number:
            ref_parts.append(f"PO {payload.po_number}")
        if payload.lot_code:
            ref_parts.append(f"lot {payload.lot_code}")
        if payload.condition != models.ReceiptCondition.good:
            ref_parts.append(f"condition: {payload.condition.value}")
        db.add(models.InventoryTransaction(
            product_id=payload.product_id,
            change_qty=payload.qty_received,
            reason=models.InventoryReason.received_stock,
            reference=(" — ".join(ref_parts) or f"received by {payload.received_by.strip()}"),
        ))

    db.commit()
    db.refresh(receipt)
    return _to_out(receipt)


@router.get("", response_model=list[schemas.ReceiptOut])
def list_receipts(
    limit: int = 200,
    product_id: int | None = None,
    vendor: str | None = None,
    po_number: str | None = None,
    since_days: int | None = None,
    db: Session = Depends(get_db),
):
    q = db.query(models.Receipt)
    if product_id is not None:
        q = q.filter(models.Receipt.product_id == product_id)
    if vendor:
        q = q.filter(models.Receipt.vendor == vendor)
    if po_number:
        q = q.filter(models.Receipt.po_number == po_number)
    if since_days is not None and since_days > 0:
        cutoff = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        from datetime import timedelta
        cutoff = cutoff - timedelta(days=since_days - 1)
        q = q.filter(models.Receipt.created_at >= cutoff)
    rows = q.order_by(models.Receipt.created_at.desc()).limit(limit).all()
    return [_to_out(r) for r in rows]
