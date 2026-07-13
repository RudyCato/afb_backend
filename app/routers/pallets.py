import random
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/pallets", tags=["pallets"])


def _new_pallet_number() -> str:
    return f"PLT-{random.randint(100000, 999999)}"


def _pallet_to_out(p: models.Pallet) -> schemas.PalletOut:
    return schemas.PalletOut(
        id=p.id, pallet_number=p.pallet_number, loaded_by=p.loaded_by,
        carrier=p.carrier, status=p.status, notes=p.notes,
        created_at=p.created_at, shipped_at=p.shipped_at,
        order_count=len(p.orders),
    )


@router.post("", response_model=schemas.PalletOut)
def create_pallet(payload: schemas.PalletCreate, db: Session = Depends(get_db)):
    pallet = models.Pallet(
        pallet_number=_new_pallet_number(), loaded_by=payload.loaded_by,
        carrier=payload.carrier, notes=payload.notes,
    )
    db.add(pallet)
    db.commit()
    db.refresh(pallet)
    return _pallet_to_out(pallet)


@router.get("", response_model=list[schemas.PalletOut])
def list_pallets(status: models.PalletStatus | None = None, db: Session = Depends(get_db)):
    q = db.query(models.Pallet)
    if status:
        q = q.filter(models.Pallet.status == status)
    rows = q.order_by(models.Pallet.created_at.desc()).all()
    return [_pallet_to_out(p) for p in rows]


@router.post("/{pallet_id}/assign", response_model=schemas.PalletOut)
def assign_order_to_pallet(pallet_id: int, payload: schemas.PalletAssignOrder, db: Session = Depends(get_db)):
    pallet = db.query(models.Pallet).get(pallet_id)
    if not pallet:
        raise HTTPException(404, "Pallet not found")
    order = db.query(models.Order).filter(models.Order.order_number == payload.order_number).first()
    if not order:
        raise HTTPException(404, "Order not found")
    if order.status not in (models.OrderStatus.packed, models.OrderStatus.out_for_delivery):
        raise HTTPException(400, f"Order {order.order_number} isn't packed yet (status: {order.status.value})")
    order.pallet_id = pallet.id
    db.commit()
    db.refresh(pallet)
    return _pallet_to_out(pallet)


@router.post("/{pallet_id}/unassign", response_model=schemas.PalletOut)
def unassign_order_from_pallet(pallet_id: int, payload: schemas.PalletAssignOrder, db: Session = Depends(get_db)):
    pallet = db.query(models.Pallet).get(pallet_id)
    if not pallet:
        raise HTTPException(404, "Pallet not found")
    order = db.query(models.Order).filter(
        models.Order.order_number == payload.order_number, models.Order.pallet_id == pallet.id
    ).first()
    if not order:
        raise HTTPException(404, "That order isn't on this pallet")
    order.pallet_id = None
    db.commit()
    db.refresh(pallet)
    return _pallet_to_out(pallet)


@router.patch("/{pallet_id}/status", response_model=schemas.PalletOut)
def update_pallet_status(pallet_id: int, payload: schemas.PalletStatusUpdate, db: Session = Depends(get_db)):
    pallet = db.query(models.Pallet).get(pallet_id)
    if not pallet:
        raise HTTPException(404, "Pallet not found")
    pallet.status = payload.status
    if payload.status == models.PalletStatus.shipped and not pallet.shipped_at:
        pallet.shipped_at = datetime.utcnow()
    db.commit()
    db.refresh(pallet)
    return _pallet_to_out(pallet)


@router.get("/{pallet_id}/manifest", response_model=schemas.PalletManifestOut)
def get_manifest(pallet_id: int, db: Session = Depends(get_db)):
    pallet = db.query(models.Pallet).get(pallet_id)
    if not pallet:
        raise HTTPException(404, "Pallet not found")

    orders_out = []
    for o in pallet.orders:
        items = [
            schemas.PalletManifestItem(sku=i.product.sku, name=i.product.name, qty=i.qty_ordered)
            for i in o.items
        ]
        orders_out.append(schemas.PalletManifestOrder(
            order_number=o.order_number, customer_name=o.customer.name,
            company=o.customer.company, address=o.customer.address, items=items,
        ))

    return schemas.PalletManifestOut(
        pallet_number=pallet.pallet_number, loaded_by=pallet.loaded_by,
        carrier=pallet.carrier, status=pallet.status,
        created_at=pallet.created_at, shipped_at=pallet.shipped_at,
        orders=orders_out,
    )
