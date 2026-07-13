import math

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/packaging", tags=["packaging"])


def _spec_to_out(s: models.PackagingSpec) -> schemas.PackagingSpecOut:
    return schemas.PackagingSpecOut(
        id=s.id, product_id=s.product_id, product_name=s.product.name,
        container_product_id=s.container_product_id,
        container_name=s.container_product.name if s.container_product else None,
        container_qty_per_unit=s.container_qty_per_unit,
        lid_product_id=s.lid_product_id,
        lid_name=s.lid_product.name if s.lid_product else None,
        lid_qty_per_unit=s.lid_qty_per_unit,
        box_product_id=s.box_product_id,
        box_name=s.box_product.name if s.box_product else None,
        units_per_box=s.units_per_box,
        notes=s.notes,
    )


@router.post("/specs", response_model=schemas.PackagingSpecOut)
def upsert_spec(payload: schemas.PackagingSpecCreate, db: Session = Depends(get_db)):
    product = db.query(models.Product).get(payload.product_id)
    if not product:
        raise HTTPException(404, "Product not found")

    spec = db.query(models.PackagingSpec).filter(models.PackagingSpec.product_id == payload.product_id).first()
    if not spec:
        spec = models.PackagingSpec(product_id=payload.product_id)
        db.add(spec)

    spec.container_product_id = payload.container_product_id
    spec.container_qty_per_unit = payload.container_qty_per_unit
    spec.lid_product_id = payload.lid_product_id
    spec.lid_qty_per_unit = payload.lid_qty_per_unit
    spec.box_product_id = payload.box_product_id
    spec.units_per_box = max(1, payload.units_per_box)
    spec.notes = payload.notes

    db.commit()
    db.refresh(spec)
    return _spec_to_out(spec)


@router.get("/specs", response_model=list[schemas.PackagingSpecOut])
def list_specs(db: Session = Depends(get_db)):
    rows = db.query(models.PackagingSpec).all()
    return [_spec_to_out(s) for s in rows]


@router.get("/specs/{product_id}", response_model=schemas.PackagingSpecOut)
def get_spec(product_id: int, db: Session = Depends(get_db)):
    spec = db.query(models.PackagingSpec).filter(models.PackagingSpec.product_id == product_id).first()
    if not spec:
        raise HTTPException(404, "No packaging spec for that product")
    return _spec_to_out(spec)


def compute_materials_needed(db: Session, product_id: int, qty: int) -> list[schemas.MaterialLine]:
    spec = db.query(models.PackagingSpec).filter(models.PackagingSpec.product_id == product_id).first()
    if not spec:
        return []
    lines: list[schemas.MaterialLine] = []
    if spec.container_product_id:
        lines.append(schemas.MaterialLine(
            role="container", product_id=spec.container_product_id,
            sku=spec.container_product.sku, name=spec.container_product.name,
            qty_needed=qty * spec.container_qty_per_unit,
        ))
    if spec.lid_product_id:
        lines.append(schemas.MaterialLine(
            role="lid", product_id=spec.lid_product_id,
            sku=spec.lid_product.sku, name=spec.lid_product.name,
            qty_needed=qty * spec.lid_qty_per_unit,
        ))
    if spec.box_product_id:
        boxes = math.ceil(qty / max(1, spec.units_per_box))
        lines.append(schemas.MaterialLine(
            role="box", product_id=spec.box_product_id,
            sku=spec.box_product.sku, name=spec.box_product.name,
            qty_needed=boxes,
        ))
    return lines


@router.get("/materials-needed", response_model=schemas.MaterialsNeededOut)
def materials_needed(product_id: int, qty: int, db: Session = Depends(get_db)):
    product = db.query(models.Product).get(product_id)
    if not product:
        raise HTTPException(404, "Product not found")

    spec = db.query(models.PackagingSpec).filter(models.PackagingSpec.product_id == product_id).first()
    lines = compute_materials_needed(db, product_id, qty)
    return schemas.MaterialsNeededOut(product_id=product_id, qty_ordered=qty, has_spec=bool(spec), materials=lines)
