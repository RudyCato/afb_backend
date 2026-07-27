"""
Returns intake — logs product coming back from a customer or delivered order.

Every return also creates a matching InventoryTransaction (reason=returned) and
bumps the product's on-hand quantity, so a returned case never has to be
adjusted separately from the /stock page.
"""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/returns", tags=["returns"])


def _to_out(r: models.CustomerReturn) -> schemas.ReturnOut:
    return schemas.ReturnOut(
        id=r.id,
        order_number=r.order_number,
        customer_id=r.customer_id,
        customer_name=(r.customer.name if r.customer else None),
        product_id=r.product_id,
        sku=r.product.sku,
        product_name=r.product.name,
        qty=r.qty,
        sell_by_date=r.sell_by_date,
        reason=r.reason,
        notes=r.notes,
        created_by=r.created_by,
        created_at=r.created_at,
    )


@router.post("", response_model=schemas.ReturnOut, status_code=201)
def log_return(payload: schemas.ReturnCreate, db: Session = Depends(get_db)):
    if payload.qty <= 0:
        raise HTTPException(422, "Quantity must be greater than zero.")

    product = db.query(models.Product).get(payload.product_id)
    if not product:
        raise HTTPException(404, "Product not found.")

    if payload.customer_id is not None:
        customer = db.query(models.Customer).get(payload.customer_id)
        if not customer:
            raise HTTPException(404, "Customer not found.")

    ret = models.CustomerReturn(
        product_id=payload.product_id,
        qty=payload.qty,
        reason=payload.reason,
        order_number=(payload.order_number or None),
        customer_id=payload.customer_id,
        sell_by_date=payload.sell_by_date,
        notes=payload.notes,
        created_by=payload.created_by,
    )
    db.add(ret)

    # Bump inventory back up + record the transaction. Reference stitches the
    # transaction back to whatever identifier we have (order#, customer, or
    # just the reason) so /stock history stays readable.
    inv = db.query(models.Inventory).filter(models.Inventory.product_id == payload.product_id).first()
    if inv:
        inv.qty_on_hand = int(inv.qty_on_hand) + payload.qty
        inv.last_updated = datetime.utcnow()

    ref_parts = []
    if payload.order_number:
        ref_parts.append(f"order {payload.order_number}")
    if payload.customer_id:
        cust = db.query(models.Customer).get(payload.customer_id)
        if cust:
            ref_parts.append(f"customer {cust.name}")
    ref_parts.append(f"reason: {payload.reason.value}")
    db.add(models.InventoryTransaction(
        product_id=payload.product_id,
        change_qty=payload.qty,
        reason=models.InventoryReason.returned,
        reference=" — ".join(ref_parts),
    ))

    db.commit()
    db.refresh(ret)
    return _to_out(ret)


@router.get("", response_model=list[schemas.ReturnOut])
def list_returns(
    limit: int = 200,
    customer_id: int | None = None,
    order_number: str | None = None,
    db: Session = Depends(get_db),
):
    q = db.query(models.CustomerReturn)
    if customer_id is not None:
        q = q.filter(models.CustomerReturn.customer_id == customer_id)
    if order_number:
        q = q.filter(models.CustomerReturn.order_number == order_number)
    rows = q.order_by(models.CustomerReturn.created_at.desc()).limit(limit).all()
    return [_to_out(r) for r in rows]
