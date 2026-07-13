import random
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/orders", tags=["orders"])


def _gen_order_number(db: Session) -> str:
    while True:
        candidate = f"AFB-{random.randint(100000, 999999)}"
        exists = db.query(models.Order).filter(models.Order.order_number == candidate).first()
        if not exists:
            return candidate


def _order_to_out(order: models.Order) -> schemas.OrderOut:
    items_out = [
        schemas.OrderItemOut(
            id=i.id, product_id=i.product_id, sku=i.product.sku,
            name=i.product.name, qty_ordered=i.qty_ordered, qty_packed=i.qty_packed
        )
        for i in order.items
    ]
    packing_out = [
        schemas.PackingRecordBrief(packed_by=r.packed_by, boxes=r.boxes, packed_at=r.packed_at)
        for r in sorted(order.packing_records, key=lambda r: r.packed_at)
    ]
    return schemas.OrderOut(
        id=order.id, order_number=order.order_number, status=order.status,
        delivery_pref=order.delivery_pref, notes=order.notes,
        created_at=order.created_at, updated_at=order.updated_at,
        customer=order.customer, items=items_out,
        status_history=sorted(order.status_history, key=lambda h: h.changed_at),
        packing_records=packing_out,
        pallet_number=order.pallet.pallet_number if order.pallet else None,
    )


@router.post("", response_model=schemas.OrderOut)
def create_order(payload: schemas.OrderCreate, db: Session = Depends(get_db)):
    # find-or-create customer by email
    customer = db.query(models.Customer).filter(
        models.Customer.email == payload.customer.email
    ).first()
    if not customer:
        customer = models.Customer(**payload.customer.model_dump())
        db.add(customer)
        db.flush()

    order = models.Order(
        order_number=_gen_order_number(db),
        customer_id=customer.id,
        status=models.OrderStatus.received,
        delivery_pref=payload.delivery_pref,
        notes=payload.notes,
    )
    db.add(order)
    db.flush()

    for item in payload.items:
        product = db.query(models.Product).get(item.product_id)
        if not product:
            raise HTTPException(400, f"Unknown product_id {item.product_id}")
        db.add(models.OrderItem(
            order_id=order.id, product_id=item.product_id,
            qty_ordered=item.qty_ordered, unit_price_snapshot=product.unit_price,
        ))
        # reserve stock
        inv = db.query(models.Inventory).filter(models.Inventory.product_id == item.product_id).first()
        if inv:
            inv.qty_reserved += item.qty_ordered
            db.add(models.InventoryTransaction(
                product_id=item.product_id, change_qty=-item.qty_ordered,
                reason=models.InventoryReason.order_reserved, reference=order.order_number,
            ))

    db.add(models.OrderStatusHistory(
        order_id=order.id, status=models.OrderStatus.received, note="Order placed"
    ))
    db.commit()
    db.refresh(order)
    return _order_to_out(order)


@router.get("", response_model=list[schemas.OrderOut])
def list_orders(status: models.OrderStatus | None = None, customer_id: int | None = None, db: Session = Depends(get_db)):
    q = db.query(models.Order)
    if status:
        q = q.filter(models.Order.status == status)
    if customer_id:
        q = q.filter(models.Order.customer_id == customer_id)
    orders = q.order_by(models.Order.created_at.desc()).all()
    return [_order_to_out(o) for o in orders]


@router.get("/{order_number}", response_model=schemas.OrderOut)
def get_order(order_number: str, db: Session = Depends(get_db)):
    order = db.query(models.Order).filter(models.Order.order_number == order_number).first()
    if not order:
        raise HTTPException(404, "Order not found")
    return _order_to_out(order)


@router.patch("/{order_number}/status", response_model=schemas.OrderOut)
def update_status(order_number: str, payload: schemas.OrderStatusUpdate, db: Session = Depends(get_db)):
    order = db.query(models.Order).filter(models.Order.order_number == order_number).first()
    if not order:
        raise HTTPException(404, "Order not found")

    if payload.status == models.OrderStatus.cancelled and order.status != models.OrderStatus.cancelled:
        # release reservations
        for item in order.items:
            inv = db.query(models.Inventory).filter(models.Inventory.product_id == item.product_id).first()
            if inv:
                inv.qty_reserved = max(0, inv.qty_reserved - item.qty_ordered)
                db.add(models.InventoryTransaction(
                    product_id=item.product_id, change_qty=item.qty_ordered,
                    reason=models.InventoryReason.order_released, reference=order.order_number,
                ))

    order.status = payload.status
    order.updated_at = datetime.utcnow()
    db.add(models.OrderStatusHistory(
        order_id=order.id, status=payload.status, note=payload.note
    ))
    db.commit()
    db.refresh(order)
    return _order_to_out(order)
