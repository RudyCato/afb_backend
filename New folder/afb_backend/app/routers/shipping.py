from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter(tags=["shipping"])


@router.post("/orders/{order_number}/shipment", response_model=schemas.ShipmentOut)
def create_shipment(order_number: str, payload: schemas.ShipmentCreate, db: Session = Depends(get_db)):
    order = db.query(models.Order).filter(models.Order.order_number == order_number).first()
    if not order:
        raise HTTPException(404, "Order not found")
    if order.shipment:
        raise HTTPException(400, "Shipment already exists for this order")

    address = payload.address or order.customer.address
    shipment = models.Shipment(
        order_id=order.id, carrier=payload.carrier,
        tracking_number=payload.tracking_number, address=address,
        status=models.ShipmentStatus.in_transit, shipped_at=datetime.utcnow(),
    )
    db.add(shipment)
    db.flush()

    db.add(models.ShipmentEvent(
        shipment_id=shipment.id, status="in_transit",
        location="Paterson, NJ facility", notes="Shipment created and left the facility",
    ))

    # move inventory from reserved -> shipped (deduct on_hand, clear reservation)
    for item in order.items:
        inv = db.query(models.Inventory).filter(models.Inventory.product_id == item.product_id).first()
        if inv:
            inv.qty_on_hand = max(0, inv.qty_on_hand - item.qty_ordered)
            inv.qty_reserved = max(0, inv.qty_reserved - item.qty_ordered)
            db.add(models.InventoryTransaction(
                product_id=item.product_id, change_qty=-item.qty_ordered,
                reason=models.InventoryReason.order_shipped, reference=order.order_number,
            ))

    order.status = models.OrderStatus.out_for_delivery
    order.updated_at = datetime.utcnow()
    db.add(models.OrderStatusHistory(
        order_id=order.id, status=models.OrderStatus.out_for_delivery,
        note=f"Shipped via {payload.carrier}"
    ))
    db.commit()
    db.refresh(shipment)
    return shipment


@router.post("/shipments/{shipment_id}/events", response_model=schemas.ShipmentOut)
def add_shipment_event(shipment_id: int, payload: schemas.ShipmentEventCreate, db: Session = Depends(get_db)):
    shipment = db.query(models.Shipment).get(shipment_id)
    if not shipment:
        raise HTTPException(404, "Shipment not found")

    db.add(models.ShipmentEvent(
        shipment_id=shipment.id, status=payload.status,
        location=payload.location, notes=payload.notes,
    ))

    if payload.status.lower() == "delivered":
        shipment.status = models.ShipmentStatus.delivered
        shipment.delivered_at = datetime.utcnow()
        order = shipment.order
        order.status = models.OrderStatus.delivered
        order.updated_at = datetime.utcnow()
        db.add(models.OrderStatusHistory(
            order_id=order.id, status=models.OrderStatus.delivered, note="Delivered"
        ))
    elif payload.status.lower() == "exception":
        shipment.status = models.ShipmentStatus.exception

    db.commit()
    db.refresh(shipment)
    return shipment


@router.get("/orders/{order_number}/shipment", response_model=schemas.ShipmentOut)
def get_shipment(order_number: str, db: Session = Depends(get_db)):
    order = db.query(models.Order).filter(models.Order.order_number == order_number).first()
    if not order or not order.shipment:
        raise HTTPException(404, "No shipment found for that order")
    return order.shipment
